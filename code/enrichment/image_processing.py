import os
import sys

import numpy as np
import pickle
import skimage.io

from matplotlib import pyplot as plt

sys.path.append('../models/')

from tensorflow_object_detection import load_model, run_model_on_single_image

from mrcnn import model as modellib
from mrcnn import utils
from mrcnn import visualize

from coco.coco import CocoConfig
from coco.coco import CocoDataset


# TODO: Check alternative (RetinaNet model, https://github.com/tensorflow/tpu/tree/master/models/official/retinanet)
def load_mrcnn_model():
    # Directory to save logs and trained model
    mrcnn_model_dir = '../models/mrcnn/'

    # Local path to trained weights file
    coco_model_path = '../weights/mask_rcnn_coco.h5'

    # Download COCO trained weights from Releases if needed
    # if not os.path.exists(coco_model_path):
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
        tf_model = load_tf_model()

        models = {
            'mrcnn': mrcnn_model,
            'tf': tf_model
        }

        # Save the TF model object into a pickle file
        # with open(models_path, 'wb') as f:
        #     pickle.dump(models, f, protocol=pickle.HIGHEST_PROTOCOL)

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
        if score > 0.0:
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

        # Keep unique class names
        # annotations = np.unique(annotations)

    return annotations


def get_annotations(image_url, document_id, models):
    # Specify the results directory
    # results_dir = '../data/images/output'

    annotations = []

    # Load the image from the specified url
    image = skimage.io.imread(image_url)

    # Save the image to directory
    skimage.io.imsave('../../data/images/input/{}.png'.format(document_id), image)

    # Run the Mask R-CNN model
    annotations += get_mrcnn_annotations(image, document_id, models)

    # Run the Tensorflow model
    annotations += get_tf_annotations(image, document_id, models)

    return annotations
