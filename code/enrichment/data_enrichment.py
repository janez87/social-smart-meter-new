# system modules
import sys

# external modules
import numpy as np
import time

from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# my modules
from image_processing import get_annotations, load_models, load_mrcnn_model
from place_processing import determine_area_name, determine_distance_to_home, determine_distance_to_previous
from text_processing import get_tokens

sys.path.append('../')
from config import mongo_config as config
from collection.facebook_crawler import get_facebook_place_categories
from collection.foursquare_crawler import get_foursquare_place_categories, query_place_name
from collection.google_crawler import get_google_place_categories
from collection.twitter_crawler import get_twitter_user


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
    for document in db['area'].find({'name': 'istanbul'}):
        for area in document['geojson']['features']:
            if area['geometry']['type'] == 'Polygon':
                polygons.append(area)
            elif area['geometry']['type'] == 'MultiPolygon':
                multipolygons.append(area)

    areas = {
        'polygons': polygons,
        'multipolygons': multipolygons
    }

    # TODO: Save model variables in ./../models directory
    # print('Loading the models..')
    # models = load_models()

    return collections, areas, {}


def enrich_user(user, users, source):
    if not user['home']['name']:
        # User matching
        twitter_user = get_twitter_user(user)

        if twitter_user:
            if twitter_user.location:
                user['home'] = twitter_user.location

    # Store user in collection
    try:
        users.insert({
            '_id': '{}{}'.format(user['username'], source),
            'username': user['username'],
            'home': user['home'],
            'places': []
        })
    except DuplicateKeyError as e:
        print(e)

    return user


def enrich_text_with_language(text):
    # text['language'] = determine_language(text['message'])

    return text


def enrich_text_with_tokens(text):
    if not text['tokens']:
        text['tokens'] = get_tokens(text['message'])

        text['processed'] = True

    return text


def enrich_image(image, document_id, models):
    if not image['processed']:
        image['annotations'], processed = get_annotations(image['url'], document_id, models)

        image['processed'] = processed

    return image


def enrich_place_with_categories(place):
    if not place['processed']:

        place_categories = place['categories']

        foursquare_categories = get_foursquare_place_categories(place)
        print('FOURSQUARE: ', foursquare_categories)
        place_categories += foursquare_categories
        # google_categories = get_google_place_categories(place)
        # print('GOOGLE: ', google_categories)
        # place_categories += google_categories

        place['categories'] = np.unique(place_categories).tolist()

        place['processed'] = True

    return place


def enrich_place_by_name(place):
    place_categories = place['categories']
    new_categories, coordinates = query_place_name(place['name'])

    place_categories += new_categories
    place['categories'] = np.unique(place_categories).tolist()

    place['coordinates'] = coordinates

    print('CATEGORIES: ', place['categories'])
    print('COORDINATES: ', place['coordinates'])

    return place


def enrich_place_with_distance_to_previous(place, username, time, collection):
    place['distance_to_previous'] = determine_distance_to_previous(place, username, time, collection)

    return place


def enrich_place_with_area_name(place, areas):
    area_name = determine_area_name(place, areas)

    print(area_name)

    return area_name


def update_document(updates, document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            # 'user': updates['user'],
            # 'text': updates['text'],
            # 'image': updates['image'],
            'place': updates['place'],
            # 'area_name': updates['area_name'],
        }
    }, upsert=False)


def user_home_check(place, user):
    # Check if the user's at home
    home_place_categories = ['Home', 'Thuis', '', 'Home (private)', 'Residence',
                             'Residential Building (Apartment / Condo)']
    if place['categories']:
        for category in place['categories']:
            if category in home_place_categories:
                place['user_at_home'] = True

    if user['home']['name']:
        place['distance_to_home'] = determine_distance_to_home(place, user)
        if place['distance_to_home'] < 1.0:
            place['user_at_home'] = True

    return place


def enrich_document(document, collection, users, areas, models, source):
    user = document['user']
    # user = enrich_user(document['user'], users, source)
    #
    # text = document['text']
    # if text['message']:
    #     # if not text['language']:
    #     #     text = enrich_text_with_language(text)
    #     text = enrich_text_with_tokens(text)
    #
    # image = document['image']
    # if image['url']:
    #     image = enrich_image(image, document['_id'], models)

    place = document['place']
    area_name = None

    # if place['name']:
    #     place = enrich_place_by_name(place)
    #
    #     if place['coordinates']:
    #         area_name = enrich_place_with_area_name(place, areas)

    if place['coordinates']:
        # place = enrich_place_with_distance_to_previous(place, user['username'], document['time'], collection)
        # area_name = enrich_place_with_area_name(place, areas)

        if place['name']:
            place = enrich_place_with_categories(place)

    # place = user_home_check(place, user)

    updates = {
        # 'user': user,
        # 'text': text,
        # 'image': image,
        'place': place,
        # 'area_name': area_name
    }

    update_document(updates, document, collection)


def main(source):
    collections, areas, models = setup()

    if source == '--instagram':
        print('Enriching Instagram documents..')
        # cursor = collections['instagram'].find({'time': {'$gte': datetime(2018, 7, 27, 0, 0, 0)}},
        cursor = collections['instagram'].find({'_id': {'$gte': '1833086586720779780_5809860165'}},
        # cursor = collections['instagram'].find({'place.name': {'$ne': 'Amsterdam, Netherlands'}, 'place.categories': [],
                                                # '_id': {'$gte': '1806900875550450285_1291811407'}},
                                               no_cursor_timeout=True)
        # For each document in the Instagram collection, enrich the data
        for document in cursor:
            print('[ID] {}'.format(document['_id']))
            try:
                enrich_document(document, collections['instagram'], collections['users'], areas, models, source)
            except AttributeError as e:
                print(e)
        cursor.close()
        print('Done!')

    elif source == '--twitter':
        print('Enriching Twitter documents..')
        # cursor = collections['twitter'].find({'time': {'$gte': datetime(2018, 7, 28, 0, 0, 0)}}
        # cursor = collections['twitter'].find({'_id': {'$gte': '1009949133724049408'},
        cursor = collections['twitter'].find({'_id': {'$gte': '1018150848245940225'},
                                              'place.coordinates': None,
                                              'place.name': {'$ne': None}}, no_cursor_timeout=True)
        # For each document in the Twitter collection, enrich the data
        for document in cursor:
            time.sleep(1)
            print('[ID] {}'.format(document['_id']))
            try:
                enrich_document(document, collections['twitter'], collections['users'], areas, models, source)
            except AttributeError as e:
                print(e)
            except ValueError as e:
                print(e)
        cursor.close()
        print('Done!')

    elif source == '--merged':
        print('Enriching documents..')
        cursor = collections['merged'].find({'_id': {'$gte': '1811709830843833266_1281777949'},
                                             'place.processed': False,
                                             'place.coordinates': {'$ne': None},
                                             'place.name': {'$ne': None},
                                             'place.categories': []}, no_cursor_timeout=True)

        # cursor = collections['merged'].find({}, no_cursor_timeout=True)

        # For each document in the merged collection, enrich the data
        for document in cursor:
            time.sleep(1)
            print('[ID] {}'.format(document['_id']))
            try:
                enrich_document(document, collections['merged'], collections['users'], areas, models, source)
            except AttributeError as e:
                print(e)
            except ValueError as e:
                print(e)
        cursor.close()
        print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])
