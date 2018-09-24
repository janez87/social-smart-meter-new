# system modules
import os
import sys

# external modules
import numpy as np
import pickle
import skimage.io
import torch
from torch.autograd import Variable as V
import torchvision.models as models
from torchvision import transforms as trn
from torch.nn import functional as F
from matplotlib import pyplot as plt
from PIL import Image

sys.path.append('../models/')

# my modules
from tensorflow_object_detection import load_model, run_model_on_single_image

from mrcnn import model as modellib
from mrcnn import utils
from mrcnn import visualize

from coco.coco import CocoConfig
from coco.coco import CocoDataset


def load_mrcnn_model():
    # Directory to save logs and trained model
    mrcnn_model_dir = '../models/mrcnn/'

    # Local path to trained weights file
    coco_model_path = '../weights/mask_rcnn_coco.h5'

    # Download COCO trained weights from Releases if needed
    if not os.path.exists(coco_model_path):
        utils.download_trained_weights(coco_model_path)

    class InferenceConfig(CocoConfig):
        # Set batch size to 1 since we'll be running inference on
        # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
        GPU_COUNT = 1
        IMAGES_PER_GPU = 1

    config = InferenceConfig()
    config.display()

    # Create model object in inference mode.
    model = modellib.MaskRCNN(mode='inference', model_dir=mrcnn_model_dir, config=config)

    # Load weights trained on MS-COCO
    model.load_weights(coco_model_path, by_name=True)

    # Load COCO dataset
    dataset = CocoDataset()
    dataset.load_coco('coco', 'train')
    dataset.prepare()

    return {'model': model, 'dataset': dataset}


def load_tf_model():
    detection_graph, category_index = load_model()

    return {'detection_graph': detection_graph, 'category_index': category_index}


def load_places_model():
    # the architecture to use
    arch = 'resnet50'

    # load the pre-trained weights
    model_file = '%s_places365.pth.tar' % arch
    if not os.access(model_file, os.W_OK):
        weight_url = 'http://places2.csail.mit.edu/models_places365/' + model_file
        os.system('wget ' + weight_url)

    model = models.__dict__[arch](num_classes=365)
    checkpoint = torch.load(model_file, map_location=lambda storage, loc: storage)
    state_dict = {str.replace(k, 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
    model.load_state_dict(state_dict)
    model.eval()

    # load the image transformer
    centre_crop = trn.Compose([
        trn.Resize((256, 256)),
        trn.CenterCrop(224),
        trn.ToTensor(),
        trn.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # load the class label
    file_name = 'categories_places365.txt'
    if not os.access(file_name, os.W_OK):
        synset_url = 'https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt'
        os.system('wget ' + synset_url)
    classes = list()
    with open(file_name) as class_file:
        for line in class_file:
            classes.append(line.strip().split(' ')[0][3:])
    classes = tuple(classes)

    return {'model': model, 'centre_crop': centre_crop, 'classes': classes}


def load_models():
    models_path = '../models/models.pkl'

    if models_path and os.path.getsize(models_path) > 0:
        with open(models_path, 'rb') as f:
            unpickler = pickle.Unpickler(f)
            # if file is not empty, models will be equal
            # to the value unpickled
            models = unpickler.load()
    else:
        mrcnn_model = load_mrcnn_model()
        # tf_model = load_tf_model()
        places_model = load_places_model()

        models = {
            'mrcnn': mrcnn_model,
            'tf': {},
            'places': places_model,
        }

    return models


def load_image_into_numpy_array(image):
    """Helper code"""
    (im_width, im_height) = image.size

    return np.array(image.getdata()).reshape(
          (im_height, im_width, 3)).astype(np.uint8)


def get_tf_annotations(image, document_id, models):
    # Get Tensorflow model from models object
    detection_graph = models['tf']['detection_graph']
    category_index = models['tf']['category_index']

    annotations = []

    # Run Tensorflow image object detection
    output_dict = run_model_on_single_image(image, document_id, detection_graph, category_index)

    # Get class ids
    class_ids = output_dict['detection_classes']

    # Get scores
    scores = output_dict['detection_scores']

    # For each class id, get class name and get corresponding score
    for class_id, score in zip(class_ids, scores):
        if score > 0.0 and int(class_id) in category_index.keys():
            annotations.append({
                'class': category_index[int(class_id)]['name'],
                'score': float(score),
                'model': 'tf'
            })

    return annotations


def get_mrcnn_annotations(image, document_id, models):
    # Get Mask R-CNN model from models object
    model = models['mrcnn']['model']
    dataset = models['mrcnn']['dataset']

    annotations = []

    # Run Mask R-CNN image object detection
    results = model.detect([image], verbose=1)
    r = results[0]

    # Visualize image with masks
    visualize.display_instances(
        image, document_id, r['rois'], r['masks'], r['class_ids'],
        dataset.class_names, r['scores'])

    # Get class ids
    class_ids = r['class_ids'].tolist()

    # Get scores
    scores = r['scores'].tolist()

    # For each class id, get class name and get corresponding score
    for class_id, score in zip(class_ids, scores):
        annotations.append({
            'class': dataset.class_names[class_id],
            'score': score,
            'model': 'mrcnn'
        })

    return annotations


def get_places_annotations(image, models):
    # Get Places-365 model from models object
    model = models['places']

    annotations = []

    input_img = V(model['centre_crop'](image).unsqueeze(0))

    # forward pass
    logit = model['model'].forward(input_img)
    h_x = F.softmax(logit, 1).data.squeeze()
    probs, idx = h_x.sort(0, True)

    # output the prediction
    for i in range(0, 5):
        if probs[i] > 0.2:
            annotations.append({
                'class': model['classes'][idx[i]],
                'score': float(probs[i]),
                'model': 'places'
            })

    return annotations


def get_annotations(url, document_id, models):
    annotations = []

    processed = False

    path = '../../data/images/input/{}.jpg'.format(document_id)

    if os.path.isfile(path):
        image = skimage.io.imread(path)

        # Run the Mask R-CNN model
        annotations += get_mrcnn_annotations(image, document_id, models)

        # Run the Tensorflow model
        # annotations += get_tf_annotations(image, document_id, models)

        # Run the Places365 model
        image = Image.open(path)
        annotations += get_places_annotations(image, models)

        processed = True
    else:
        # Load the image from the specified url
        image = skimage.io.imread(url)

        # Save the image to directory
        skimage.io.imsave('../../data/images/input/{}.jpg'.format(document_id), image)

        # Load the image from the input directory
        image = Image.open('../../data/images/input/{}.jpg'.format(document_id))

        # Run the Mask R-CNN model
        annotations += get_mrcnn_annotations(image, document_id, models)

        # Run the Tensorflow model
        # annotations += get_tf_annotations(image, document_id, models)

        # Run the Places365 model
        image = Image.open(path)
        annotations += get_places_annotations(image, models)

        processed = True

    return annotations, processed
