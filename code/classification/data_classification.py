import os
import sys

from pymongo import MongoClient

sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']

    # Make sure the dictionary collections are up to date
    os.system('python3 dictionary_processing.py')

    dwelling_dictionary = db['dwelling_dictionary']
    food_consumption_dictionary = db['food_consumption_dictionary']
    leisure_dictionary = db['leisure_dictionary']
    mobility_dictionary = db['mobility_dictionary']

    dictionaries = {
        'dwelling': dwelling_dictionary,
        'food_consumption': food_consumption_dictionary,
        'leisure': leisure_dictionary,
        'mobility': mobility_dictionary
    }

    return instagram_collection, twitter_collection, dictionaries


def add_term(term, activity):
    activity['output'] = 1
    if term not in activity['tags']:
        activity['tags'].append(term)


def dictionary_check(term, activities, dictionaries, key):
    if dictionaries['dwelling'].find({'term': term, 'key': key}).count() > 0:
        add_term(term, activities['dwelling'])

    if dictionaries['food_consumption'].find({'term': term, 'key': key}).count() > 0:
        add_term(term, activities['food_consumption'])

    if dictionaries['leisure'].find({'term': term, 'key': key}).count() > 0:
        add_term(term, activities['leisure'])

    if dictionaries['mobility'].find({'term': term, 'key': key}).count() > 0:
        add_term(term, activities['mobility'])

    return activities


def classify_text(text, activities, dictionaries):
    for token in text['tokens']:
        activities = dictionary_check(token, activities, dictionaries, 'text')

    return activities


def classify_image(image, activities, dictionaries):
    thresholds = {
        'mrcnn': 0.8,
        'tf': 0.5
    }

    for annotation in image['annotations']:
        if ((annotation['model'] == 'mrcnn' and annotation['score'] > thresholds['mrcnn'])
                or (annotation['model'] == 'tf' and annotation['score'] > thresholds['tf'])):
            activities = dictionary_check(annotation['class'], activities, dictionaries, 'images')

    return activities


def classify_place(place, activities, dictionaries):
    for category in place['categories']:
        activities = dictionary_check(category, activities, dictionaries, 'places')

    return activities


def update_document(activities, document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            'activities': activities
        }
    }, upsert=False)


def reset_activities(document, collection):
    activities = {
        'dwelling': {'output': None, 'activity': None, 'tags': []},
        'food_consumption': {'output': None, 'activity': None, 'tags': []},
        'leisure': {'output': None, 'activity': None, 'tags': []},
        'mobility': {'output': None, 'mode_of_transport': None, 'distance_in_km': None, 'tags': []}
    }

    update_document(activities, document, collection)


def classify_document(document, collection, dictionaries):
    activities = document['activities']

    text = document['text']
    if text['tokens']:
        activities = classify_text(text, activities, dictionaries)

    image = document['image']
    if image['annotations']:
        activities = classify_image(image, activities, dictionaries)

    place = document['place']
    if place['categories']:
        activities = classify_place(place, activities, dictionaries)

    update_document(activities, document, collection)


def main():
    instagram_collection, twitter_collection, dictionaries = setup()

    print('Classifying Instagram documents..')
    # For each document in the Instagram collection, classify the data
    for document in instagram_collection.find():
        reset_activities(document, instagram_collection)
        classify_document(document, instagram_collection, dictionaries)

    print('Classifying Twitter documents..')
    # For each document in the Twitter collection, classify the data
    for document in twitter_collection.find():
        reset_activities(document, twitter_collection)
        classify_document(document, twitter_collection, dictionaries)

    print('Done!')


if __name__ == "__main__":
    main()
