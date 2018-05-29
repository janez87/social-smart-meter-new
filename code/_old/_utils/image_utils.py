import os
import skimage.io

from mrcnn import model as modellib
from mrcnn import utils
from mrcnn import visualize

from coco.coco import CocoConfig
from coco.coco import CocoDataset

from tensor_flow_object_detection import load_model, run_model_on_single_image


# TODO: Check alternative (RetinaNet model)
# https://github.com/tensorflow/tpu/tree/master/models/official/retinanet
def get_mrcnn_model():
    # Directory to save logs and trained model
    mrcnn_model_dir = './models/mrcnn/'

    # Local path to trained weights file
    coco_model_path = './weights/mask_rcnn_coco.h5'

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
    # model.load_weights(coco_model_path, by_name=True)
    model.load_weights(coco_model_path, by_name=True)

    # Load COCO dataset
    dataset = CocoDataset()
    dataset.load_coco('./coco', 'train')
    dataset.prepare()

    return model, dataset


def get_tf_model():
    # Define what model to download
    model_name = 'faster_rcnn_inception_resnet_v2_atrous_oid_2018_01_28'  # Alternative: 'ssd_mobilenet_v1_coco_2017_11_17'
    model_file = model_name + '.tar.gz'
    download_base = 'http://download.tensorflow.org/models/object_detection/'

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    path_to_ckpt = model_name + '/frozen_inference_graph.pb'

    # List of the strings that is used to add correct label for each box.
    path_to_labels = 'object_detection/data/oid_bbox_trainable_label_map.pbtxt'  # Alternative: 'mscoco_label_map.pbtxt'

    num_classes = 545  # Alternative: 90

    # Create params object
    params = {
        'model_name': model_name,
        'model_file': model_file,
        'download_base': download_base,
        'path_to_ckpt': path_to_ckpt,
        'path_to_labels': path_to_labels,
        'num_classes': num_classes
    }

    detection_graph, category_index = load_model(params)

    return detection_graph, category_index


def get_annotations(image_url, post_id, models):
    # Specify the results directory
    # results_dir = '../data/instagram/images/output'

    annotations = []

    # Load the image from the specified url
    image = skimage.io.imread(image_url)

    # If specified, run the Tensorflow model
    if models['tf']['run'] is True:
        annotations += get_tf_annotations(image, post_id, models)

    # If specified, run the Mask R-CNN model
    if models['mrcnn']['run'] is True:
        annotations += get_mrcnn_annotations(image, post_id, models)

    return annotations


def get_tf_annotations(image, post_id, models):
    # Get Tensorflow model from models object
    detection_graph = models['tf']['detection_graph']
    category_index = models['tf']['category_index']

    annotations = []

    # Run Tensorflow image object detection
    output_dict = run_model_on_single_image(image, post_id, detection_graph, category_index)

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


def get_mrcnn_annotations(image, post_id, models):
    # Get Mask R-CNN model from models object
    model = models['mrcnn']['model']
    dataset = models['mrcnn']['dataset']

    annotations = []

    # Run Mask R-CNN image object detection
    results = model.detect([image], verbose=1)
    r = results[0]

    # Visualize image with masks
    visualize.display_instances(
        image, r['rois'], r['masks'], r['class_ids'],
        dataset.class_names, r['scores'])
    # plt.savefig('{}/{}.png'.format(results_dir, post_id))

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
