# system modules
import sys

# external modules
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# my modules
sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']
    merged_collection = db['merged']

    collections = {
        'twitter': twitter_collection,
        'instagram': instagram_collection,
        'merged': merged_collection
    }

    return collections


def insert_document(document, collection):
    try:
        collection.insert(document)
    except DuplicateKeyError as e:
        print(e)


def update_document(document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            'categories': document['categories']
        }
    }, upsert=False)


def main(arg):
    collections = setup()

    print('Merging Instagram and Twitter collections..')

    instagram_cursor = collections['instagram'].find({'time': {'$gte': datetime(2018, 6, 22, 0, 0, 0)}})
    twitter_cursor = collections['twitter'].find({'time': {'$gte': datetime(2018, 6, 22, 0, 0, 0)}})

    for document in instagram_cursor:
        print(document['_id'])
        if arg == '--merge':
            insert_document(document, collections['merged'])
        elif arg == '--update':
            update_document(document, collections['merged'])

    for document in twitter_cursor:
        print(document['_id'])
        if arg == '--merge':
            insert_document(document, collections['merged'])
        elif arg == '--update':
            update_document(document, collections['merged'])

    print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])
