import sys

from pymongo import MongoClient

from image_processing import get_annotations, load_models, load_mrcnn_model
from place_processing import determine_distance_to_previous
from text_processing import get_tokens

sys.path.append('../')
from config import mongo_config as config
from crawler.google_crawler import get_place_categories
from crawler.twitter_crawler import get_twitter_user


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']

    print('Loading the models..')
    # TODO: Save model variables in ./../models directory
    models = load_models()

    return instagram_collection, twitter_collection, models


def enrich_user(user):
    twitter_user = get_twitter_user(user)

    if twitter_user:
        if twitter_user.location:
            user['home'] = twitter_user.location

    return user


def enrich_text_with_language(text):
    # text['language'] = determine_language(text['caption'])

    return text


def enrich_text_with_tokens(text):
    text['tokens'] = get_tokens(text['caption'])

    return text


def enrich_image(image, document_id, models):
    # image['annotations'] = get_annotations(image['url'], document_id, models)

    return image


def enrich_place_with_categories(place):
    place['categories'] = get_place_categories(place)

    return place


def enrich_place_with_distance_to_previous(place, username, time, collection):
    place['distance_to_previous'] = determine_distance_to_previous(place, username, time, collection)

    return place


def update_document(updates, document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            'user': updates['user'],
            'text': updates['text'],
            'image': updates['image'],
            'place': updates['place'],
        }
    }, upsert=False)


def enrich_document(document, collection, models):
    user = document['user']
    if not user['home']:
        user = enrich_user(user)

    text = document['text']
    if text['caption']:
        if not text['language']:
            text = enrich_text_with_language(text)

        text = enrich_text_with_tokens(text)

    image = document['image']
    if image['url']:
        image = enrich_image(image, document['_id'], models)

    place = document['place']
    if place['coordinates']:
        place = enrich_place_with_distance_to_previous(place, user['username'], document['time'], collection)

        if place['name']:
            place = enrich_place_with_categories(place)

    updates = {
        'user': user,
        'text': text,
        'image': image,
        'place': place
    }

    update_document(updates, document, collection)


def main():
    instagram_collection, twitter_collection, models = setup()

    print('Enriching Instagram documents..')
    # For each document in the Instagram collection, enrich the data
    for document in instagram_collection.find():
        enrich_document(document, instagram_collection, models)

    print('Enriching Twitter documents..')
    # For each document in the Twitter collection, enrich the data
    for document in twitter_collection.find():
        enrich_document(document, twitter_collection, models)

    print('Done!')


if __name__ == "__main__":
    main()
