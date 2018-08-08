import sys

import csv
from pymongo import MongoClient

sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    dwelling_dictionary = db['dwelling_dictionary']
    food_dictionary = db['food_dictionary']
    leisure_dictionary = db['leisure_dictionary']
    mobility_dictionary = db['mobility_dictionary']

    return {
        'dwelling': dwelling_dictionary,
        'food': food_dictionary,
        'leisure': leisure_dictionary,
        'mobility': mobility_dictionary
    }


def read_csv(filename):
    file = open(filename, "rU")
    reader = csv.reader(file, delimiter=";")

    terms = []

    # Row returns a list; hence, take the first argument (str)
    for row in reader:
        terms.append(row[0])

    file.close()

    return terms


def insert_terms(terms, collection, key):
    for term in terms:
        if collection.find({'term': term}).count() == 0:
            collection.insert({
                'term': term,
                'confidence': None,
                'key': key
            })


def store_dwelling_dictionaries(collection):
    terms = read_csv('../dictionaries/text/dwelling_dictionary.csv')
    insert_terms(terms, collection, 'text')

    terms = read_csv('../dictionaries/images/coco/dwelling_dictionary.csv')
    terms += read_csv('../dictionaries/images/open_images/dwelling_dictionary.csv')
    terms += read_csv('../dictionaries/images/places/dwelling_dictionary.csv')
    insert_terms(terms, collection, 'image')

    terms = read_csv('../dictionaries/places/facebook/dwelling_dictionary.csv')
    terms += read_csv('../dictionaries/places/foursquare/dwelling_dictionary.csv')
    terms += read_csv('../dictionaries/places/google/dwelling_dictionary.csv')
    insert_terms(terms, collection, 'place')


def store_food_dictionaries(collection):
    terms = read_csv('../dictionaries/text/food_dictionary.csv')
    insert_terms(terms, collection, 'text')

    terms = read_csv('../dictionaries/images/coco/food_dictionary.csv')
    terms += read_csv('../dictionaries/images/open_images/food_dictionary.csv')
    terms += read_csv('../dictionaries/images/places/food_dictionary.csv')
    insert_terms(terms, collection, 'image')

    terms = read_csv('../dictionaries/places/facebook/food_dictionary.csv')
    terms += read_csv('../dictionaries/places/foursquare/food_dictionary.csv')
    terms += read_csv('../dictionaries/places/google/food_dictionary.csv')
    insert_terms(terms, collection, 'place')


def store_leisure_dictionaries(collection):
    terms = read_csv('../dictionaries/text/leisure_dictionary.csv')
    insert_terms(terms, collection, 'text')

    terms = read_csv('../dictionaries/images/coco/leisure_dictionary.csv')
    terms += read_csv('../dictionaries/images/open_images/leisure_dictionary.csv')
    terms += read_csv('../dictionaries/images/places/leisure_dictionary.csv')
    insert_terms(terms, collection, 'image')

    terms = read_csv('../dictionaries/places/facebook/leisure_dictionary.csv')
    terms += read_csv('../dictionaries/places/foursquare/leisure_dictionary.csv')
    terms += read_csv('../dictionaries/places/google/leisure_dictionary.csv')
    insert_terms(terms, collection, 'place')


def store_mobility_dictionaries(collection):
    terms = read_csv('../dictionaries/text/mobility_dictionary.csv')
    insert_terms(terms, collection, 'text')

    terms = read_csv('../dictionaries/images/coco/mobility_dictionary.csv')
    terms += read_csv('../dictionaries/images/open_images/mobility_dictionary.csv')
    terms += read_csv('../dictionaries/images/places/mobility_dictionary.csv')
    insert_terms(terms, collection, 'image')

    # terms = read_csv('../dictionaries/places/facebook/mobility_dictionary.csv')
    terms += read_csv('../dictionaries/places/foursquare/mobility_dictionary.csv')
    terms += read_csv('../dictionaries/places/google/mobility_dictionary.csv')
    insert_terms(terms, collection, 'place')


def store_dictionaries(collections):
    store_dwelling_dictionaries(collections['dwelling'])
    store_food_dictionaries(collections['food'])
    store_leisure_dictionaries(collections['leisure'])
    store_mobility_dictionaries(collections['mobility'])


def main():
    collections = setup()
    store_dictionaries(collections)


if __name__ == "__main__":
    main()
