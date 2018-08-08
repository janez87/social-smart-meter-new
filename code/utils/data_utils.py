# system modules
import sys

# external modules
from datetime import datetime
from pymongo import MongoClient

# my modules
sys.path.append('../')
from config import mongo_config as config

from enrichment.place_processing import determine_area_name


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']
    merged_collection = db['merged']
    users_collection = db['users']

    collections = {
        'twitter': twitter_collection,
        'instagram': instagram_collection,
        'merged': merged_collection,
        'users': users_collection
    }

    polygons = []
    multipolygons = []
    for document in db['area'].find({'name': 'amsterdam'}):
        for area in document['geojson']['features']:
            if area['geometry']['type'] == 'Polygon':
                polygons.append(area)
            elif area['geometry']['type'] == 'MultiPolygon':
                multipolygons.append(area)

    areas = {
        'polygons': polygons,
        'multipolygons': multipolygons
    }

    return collections, areas


def update_document(document, collection):
    categories = document['place']['categories']
    categories.remove('Train Station')
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            'place.categories': categories
        }
    }, upsert=False)


def main(source):
    collections, areas = setup()

    if source == '--instagram':
        print('Editing Instagram documents..')
        # For each document in the Instagram collection, enrich the data
        cursor = collections['instagram'].find({'_id': {'$gte': '1806892642299357113_287957108'}})

        for document in cursor:
            print(document['_id'])
            update_document(document, collections['instagram'])
        print('Done!')

    if source == '--twitter':
        print('Editing Twitter documents..')
        # For each document in the Twitter collection, enrich the data
        # for document in twitter_collection.find({'image.url': {'$ne': None}, 'image.annotations': []}):
        for document in collections['twitter'].find({'time': {'$gte': datetime(2018, 6, 20, 0, 0, 0)}}):
            print(document['_id'])
            update_document(document, collections['twitter'])
        print('Done!')

    if source == '--merged':
        print('Editing documents..')
        # For each document in the Instagram collection, enrich the data

        # cursor = collections['merged'].find({'_id': {'$gte': '1806900875550450285_1291811407'},
        #                                      'place.coordinates': {'$ne': None},
        #                                      'place.name': {'$ne': None},
        #                                      'place.categories': []}, no_cursor_timeout=True)

        cursor = collections['merged'].find({'place.name': 'Amsterdam, Netherlands',
                                             'place.categories': 'Train Station'}, no_cursor_timeout=True)

        # cursor = collections['merged'].find({'place.name': 'IJburg',
        #                                      'place.categories': 'Pizza Place'}, no_cursor_timeout=True)

        for document in cursor:
            print(document['_id'])
            update_document(document, collections['merged'])
        print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])


