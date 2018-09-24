# system modules
import os
import sys

# external modules
import numpy as np

from gensim.models import KeyedVectors
# from googletrans import Translator
from pymongo import MongoClient
from pymongo.errors import CursorNotFound

# my modules
sys.path.append('../')
from config import mongo_config as config


DATA_TYPE_WEIGHTS = {
    'dwelling': {'text': 0.35, 'image': 0.40, 'place': 0.25},
    'food': {'text': 0.33, 'image': 0.37, 'place': 0.30},
    'leisure': {'text': 0.35, 'image': 0.32, 'place': 0.33},
    'mobility': {'text': 0.37, 'image': 0.33, 'place': 0.30}
}

# translator = Translator()


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    collections = {
        'twitter': db['twitter'],
        'instagram': db['instagram'],
        'merged': db['merged'],
    }

    # Make sure the dictionary collections are up to date
    os.system('python3 dictionary_processing.py')

    dictionaries = {
        'dwelling': db['dwelling_dictionary'],
        'food': db['food_dictionary'],
        'leisure': db['leisure_dictionary'],
        'mobility': db['mobility_dictionary']
    }

    text_dictionaries = {
        'dwelling': get_dictionary_text_terms(dictionaries['dwelling']),
        'food': get_dictionary_text_terms(dictionaries['food']),
        'leisure': get_dictionary_text_terms(dictionaries['leisure']),
        'mobility': get_dictionary_text_terms(dictionaries['mobility'])
    }

    # Get Word2Vec's pre-trained Google News model
    print('Loading Word2Vec Google News pre-trained model..')
    model = KeyedVectors.load_word2vec_format('../models/word2vec/GoogleNews-vectors-negative300.bin', binary=True)

    return collections, dictionaries, text_dictionaries, model


def add_term(term, score, data_type, output):
    if term not in output['terms']:
        output['terms'].append({
            'term': term,
            'data_type': data_type,
            'score': score
        })


def dictionary_check(term, output, dictionaries, text_dictionaries, model, data_type):
    annotation_score = 0

    if data_type == 'text':
        # TODO: googletrans Translator stopped working recently
        # try:
        #     term = translator.translate(term['word']).text
        # except ValueError:
        term = term['word']

    elif data_type == 'image':
        annotation_score = term['score']
        term = term['class']

    for category in ['dwelling', 'food', 'leisure', 'mobility']:
        score = 0
        if dictionaries[category].find({'term': term, 'key': data_type}).count() > 0:
            if data_type == 'text':
                score = get_similarity_score(term, text_dictionaries[category], model)
            elif data_type == 'image':
                score = annotation_score
            elif data_type == 'place':
                score = 1

            add_term(term, score, data_type, output[category])

    return output


def get_dictionary_text_terms(dictionary):
    dictionary_terms = []
    cursor = dictionary.find({'key': 'text'})
    for document in cursor:
        dictionary_terms.append(document['term'])

    return dictionary_terms


def get_similarity_score(term, text_dictionary, model):
    try:
        distances = model.wv.distances(term, text_dictionary)
        score = np.mean(distances)
    except KeyError as e:
        print(e)
        score = 0.7

    return float(score)


def classify_text(text, output, dictionaries, text_dictionaries, model):
    for token in text['tokens']:
        output = dictionary_check(token, output, dictionaries, text_dictionaries, model, 'text')

    return output


def classify_image(image, output, dictionaries, text_dictionaries, model):
    thresholds = {
        'mrcnn': 0.85,
        'tf': 0.5
    }

    for annotation in image['annotations']:
        if ((annotation['model'] == 'mrcnn' and annotation['score'] > thresholds['mrcnn'])
                or (annotation['model'] == 'tf' and annotation['score'] > thresholds['tf'])):
            output = dictionary_check(annotation, output, dictionaries, text_dictionaries, model, 'image')
        elif annotation['model'] == 'places':
            output = dictionary_check(annotation, output, dictionaries, text_dictionaries, model, 'image')

    return output


def classify_place(place, output, dictionaries, text_dictionaries, model):
    for category in place['categories']:
        output = dictionary_check(category, output, dictionaries, text_dictionaries, model, 'place')

    return output


def determine_categories(output, distance_to_previous, user_at_home):
    categories = []

    for category in ['dwelling', 'food', 'leisure', 'mobility']:
        if output[category]['terms']:
            confidence = calculate_confidence(output, category)
            output[category]['confidence'] = confidence

            # Threshold
            if confidence > 0.34:
                categories.append(category)

    categories, output = classify_by_rules(output, categories, distance_to_previous, user_at_home)

    return categories, output


def calculate_confidence(output, category):
    terms = output[category]['terms']

    scores = {
        'text': [],
        'image': [],
        'place': []
    }

    for term in terms:
        scores[term['data_type']].append(term['score'])

    confidence = {}

    for data_type in ['text', 'image', 'place']:
        if len(scores[data_type]) > 0:
            confidence[data_type] = (1 / float(len(scores[data_type])) * DATA_TYPE_WEIGHTS[category][data_type] *
                                     np.sum(scores[data_type], dtype=float))
        else:
            confidence[data_type] = 0

    total_confidence = confidence['text'] + confidence['image'] + confidence['place']

    return total_confidence


def classify_by_rules(output, categories, distance_to_previous, user_at_home):
    for category in ['food', 'leisure']:
        if category in categories and user_at_home:
            if 'dwelling' not in categories:
                categories.append('dwelling')

            output['dwelling']['classified_by_rule'] = True

    if 'food' in categories and not user_at_home:
        if 'leisure' not in categories:
            categories.append('leisure')

        output['leisure']['classified_by_rule'] = True

    if distance_to_previous and distance_to_previous > 0.5:
        if 'mobility' not in categories:
            categories.append('mobility')

        output['mobility']['classified_by_rule'] = True

    return categories, output


def update_document(output, categories, document, collection):
    collection.update_one({
        '_id': document['_id']
    }, {
        '$set': {
            'categories': categories,
            'output': output
        }
    }, upsert=False)

    return document


def classify_document(document, collection, dictionaries, text_dictionaries, model):
    output = document['output']

    text = document['text']
    if text['tokens']:
        output = classify_text(text, output, dictionaries, text_dictionaries, model)

    image = document['image']
    if image['annotations']:
        output = classify_image(image, output, dictionaries, text_dictionaries, model)

    place = document['place']
    if place['categories']:
        output = classify_place(place, output, dictionaries, text_dictionaries, model)

    categories, output = determine_categories(output, document['place']['distance_to_previous'],
                                              document['place']['user_at_home'])

    update_document(output, categories, document, collection)


def reset_classification(document, collection):
    categories = []
    output = {
                'dwelling': {
                    'confidence': 0,
                    'terms': [],
                    'classified_by_rule': False
                },
                'food': {
                    'confidence': 0,
                    'terms': [],
                    'classified_by_rule': False
                },
                'leisure': {
                    'confidence': 0,
                    'terms': [],
                    'classified_by_rule': False
                },
                'mobility': {
                    'confidence': 0,
                    'terms': [],
                    'classified_by_rule': False
                }
            }

    return update_document(output, categories, document, collection)


def main(args):
    source = args[0]  # name of collection (e.g., 'twitter', 'instagram' or 'merged')

    collections, dictionaries, text_dictionaries, model = setup()

    print('Classifying documents..')
    cursor = collections[source].find({}, no_cursor_timeout=True)

    # For each document in the collection, enrich the data
    for document in cursor:
        print('[ID] {}'.format(document['_id']))
        try:
            reset_classification(document, collections[source])
            classify_document(document, collections[source], dictionaries, text_dictionaries, model)
        except CursorNotFound as e:
            pass
    cursor.close()
    print('Done!')


if __name__ == "__main__":
    main(sys.argv[1:])
