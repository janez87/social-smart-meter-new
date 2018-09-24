# system modules
import os
import sys

# external modules
import skimage.io
import urllib.request
from datetime import datetime
from pymongo import MongoClient

# my modules
sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    collections = {
        'instagram': db['instagram'],
        'twitter': db['twitter']
    }

    return collections


def delete_document(document_id, collection):
    collection.delete_one({'_id': document_id})


def save_image(image_url, document_id, collection):
    # Try if there is not document with same id yet, otherwise pass
    try:
        # Load the image from the specified url
        image = skimage.io.imread(image_url)

        # Save the image to directory
        path = '../../data/images/input/{}.jpg'.format(document_id)

        if not os.path.isfile(path):
            skimage.io.imsave(path, image)

    except urllib.error.HTTPError as e:
        print(e)
        delete_document(document_id, collection)
        print('Document {} deleted'.format(document_id))


def main(args):
    source = args[0]  # name of collection (e.g., 'twitter' or 'instagram')

    collections = setup()

    print('Saving images to input directory..')
    cursor = collections[source].find({}, no_cursor_timeout=True)

    # For each document in the collection, enrich the data
    for document in cursor:
        print('[ID] {}'.format(document['_id']))
        image_url = document['image']['url']
        if image_url:
            save_image(image_url, document['_id'], collections[source])
    cursor.close()
    print('Done!')

if __name__ == "__main__":
    main(sys.argv[1:])
