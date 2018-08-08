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

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']

    collections = {
        'instagram': instagram_collection,
        'twitter': twitter_collection
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


def main(source):
    collections = setup()

    if source == '--instagram':
        print('Saving Instagram images to input directory')
        # cursor = collections['instagram'].find({'time': {'$gte': datetime(2018, 7, 27, 0, 0, 0)}},
        cursor = collections['instagram'].find({'_id': {'$gte': '1832897945024450677_7810164471'}},
                                               no_cursor_timeout=True)
        for document in cursor:
            print('[ID] {}'.format(document['_id']))
            image_url = document['image']['url']
            if image_url:
                save_image(image_url, document['_id'], collections['instagram'])
        cursor.close()
        print('Done!')

    elif source == '--twitter':
        print('Saving Twitter images to input directory')
        # cursor = collections['twitter'].find({'time': {'$gte': datetime(2018, 7, 27, 0, 0, 0)}},
        cursor = collections['twitter'].find({'_id': {'$gte': '1023712969669132288'}},
                                             no_cursor_timeout=True)
        for document in cursor:
            print('[ID] {}'.format(document['_id']))
            image_url = document['image']['url']
            if image_url:
                save_image(image_url, document['_id'], collections['twitter'])
        cursor.close()
        print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])
