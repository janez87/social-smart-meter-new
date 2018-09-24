# system modules
import sys

# external modules
from pymongo import MongoClient

# my modules
sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    collections = {
        'twitter': db['twitter'],
        'instagram': db['instagram'],
        'merged': db['merged'],
        'users': db['users']
    }

    return collections


def update_document(document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {

        }
    }, upsert=False)


def main(args):
    source = args[0]  # name of collection (e.g., 'twitter' or 'instagram')

    collections = setup()

    print('Editing documents..')
    # For each document in the collection, enrich the data
    cursor = collections[source].find({}, no_cursor_timeout=True)

    for document in cursor:
        print(document['_id'])
        update_document(document, collections[source])

    cursor.close()
    print('Done!')


if __name__ == "__main__":
    main(sys.argv[1:])
