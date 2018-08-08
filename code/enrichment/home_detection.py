# system modules
import sys

# external modules
import numpy as np

from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.preprocessing import StandardScaler

# my modules
from image_processing import get_annotations, load_models, load_mrcnn_model
from place_processing import determine_distance_to_previous, determine_area_name
from text_processing import get_tokens

sys.path.append('../')
from config import mongo_config as config


def setup():
    print('Connecting to Mongo..')
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])
    db = client[config['DB_NAME']]

    twitter_collection = db['twitter']
    instagram_collection = db['instagram']
    users_collection = db['users']

    collections = {
        'twitter': twitter_collection,
        'instagram': instagram_collection,
        'users': users_collection
    }

    return collections


def add_place(document, users, source):
    user_id = '{}{}'.format(document['user']['username'], source)
    user = users.find_one({'_id': user_id})

    places = []
    if user['places']:
        places = user['places']

    places.append(document['place']['coordinates'])

    users.update_one({
        '_id': '{}{}'.format(user['username'], source)
    }, {
        '$set': {
            'places': places
        }
    }, upsert=False)


def spatial_clustering(users):
    for user in users.find({'_id': 'melissajkoch--instagram'}):
        places = []
        for place in user['places']:
            # Convert coordinates string to float values
            coordinates = place.split(', ')
            coordinates[0] = float(coordinates[0])
            coordinates[1] = float(coordinates[1])
            places.append(coordinates)

        np_places = np.array(places)

        print('NP-PLACES: ', np_places)

        # Compute DBSCAN
        dbscan = DBSCAN(eps=0.3, min_samples=10).fit(np_places)
        labels = dbscan.labels_
        core_samples_mask = np.zeros_like(labels, dtype=bool)
        core_samples_mask[dbscan.core_sample_indices_] = True

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        unique_labels = set(labels)

        print('USER: {}\nLABELS: {}'.format(user['username'], labels))
        print('N_CLUSTERS: ', n_clusters_)
        print('UNIQUE LABELS: ', unique_labels)

    # How to detect home?

    # return


def main(source):
    collections = setup()

    if source == '--instagram':
        print('Home detection for Instagram users..')
        # cursor = collections['instagram'].find({'time': {'$gte': datetime(2018, 6, 22, 0, 0, 0)}})
        # for document in cursor:
        #     add_place(document, collections['users'], source)
        spatial_clustering(collections['users'])
        print('Done!')

    elif source == '--twitter':
        print('Home detection for Twitter users..')
        # cursor = collections['twitter'].find({'time': {'$gte': datetime(2018, 6, 22, 0, 0, 0)}})
        # for document in cursor:
        #     add_place(document, collections['users'], source)
        spatial_clustering(collections['users'])
        print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])
