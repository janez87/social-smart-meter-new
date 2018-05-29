import os
import skimage.io

from mrcnn import model as modellib
from mrcnn import utils
from mrcnn import visualize

from coco.coco import CocoConfig
from coco.coco import CocoDataset

from tensor_flow_object_detection import load_model, run_model_on_single_image


def train_mcrnn_model(mcrnn_model_dir):
    # TODO: To be implemented..

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
    model = modellib.MaskRCNN(mode='inference', model_dir=mcrnn_model_dir, config=config)

    # Load weights trained on MS-COCO
    # model.load_weights(coco_model_path, by_name=True)
    model.load_weights(coco_model_path, by_name=True)

    # Load COCO dataset
    dataset = CocoDataset()
    dataset.load_coco('./coco', 'train')
    dataset.prepare()

    return model, dataset


def get_annotations(model, dataset, image_url, post_id, tf_params):
    # TODO: To be implemented..

    # Specify the results directory
    # results_dir = '../data/instagram/images/output'

    annotations = []

    # Load the image from the specified url
    image = skimage.io.imread(image_url)

    # Run tensorflow image object detection
    detection_graph, category_index = load_model(tf_params)
    run_model_on_single_image(image, post_id, detection_graph, category_index)

    # Detect objects
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
            'score': score
        })

    # Keep unique class names
    # annotations = np.unique(annotations)

    return annotations

