import sys

from pymongo import MongoClient
from datetime import datetime

from instagram_crawler import crawl_instagram_data
from twitter_crawler import crawl_twitter_data

sys.path.append('../')
from config import mongo_config as config


def get_params():
    # Amsterdam neighborhoods
    amsterdam = {
        'Centrum': {'latitude': '52.372374', 'longitude': '4.898844', 'radius': '1500'},
        'Noord': {'latitude': '52.395940', 'longitude': '4.924071', 'radius': '2000'},
        'Oost': {'latitude': '', 'longitude': '', 'radius': ''},
        'Zuidoost': {'latitude': '52.304499', 'longitude': '4.971431', 'radius': '2000'},
        'Zuid': {'latitude': '52.342684', 'longitude': '4.885141', 'radius': '2000'},
        'West': {'latitude': '52.388177', 'longitude': '4.862139', 'radius': '1500'},
        'Nieuw-West': {'latitude': '52.360300', 'longitude': '4.810984', 'radius': '3000'},
        'Westpoort': {'latitude': '52.403051', 'longitude': '4.826776', 'radius': '2000'}
    }

    # Choose a neighborhood
    neighborhood = amsterdam['Centrum']

    # Coordinates
    # latitude = neighborhood['latitude']
    latitude = '47.076668'
    # longitude = neighborhood['longitude']
    longitude = '15.421371'

    # Radius in meters
    # distance = neighborhood['radius']
    distance = '5000'

    # Start date
    start_date = datetime(2018, 5, 24, 0, 0, 0)

    # End date
    end_date = datetime(2018, 5, 25, 0, 0, 0)

    # Number of posts to retrieve (max = 100)
    count = 100

    # Return params
    return {
        'latitude': latitude,
        'longitude': longitude,
        'distance': distance,  # radius of requested area
        'start_date': start_date,  # start date
        'end_date': end_date,  # end date
        'count': count  # number of posts(100 max)
    }


def connect_to_db():
    # First, run the "mongod" command from the terminal to establish a connection
    # Then, connect to the MongoClient
    client = MongoClient(config['DB_HOST'], config['DB_PORT'])

    # Return the database
    return client[config['DB_NAME']]


def main():
    print('Connecting to Mongo..')
    db = connect_to_db()
    print('Connection established!\n')

    document = {
        '_id': None,
        'link': None,
        'time': None,
        'user': {
            'username': None,
            'home': None
        },
        'text': {
            'caption': None,
            'language': None,
            'tokens': []
        },
        'image': {
            'url': None,
            'annotations': []
        },
        'place': {
            'name': None,
            'coordinates': None,
            'categories': [],
            'distance_to_previous': None
        },
        'activities': {
            'dwelling': {'output': None, 'activity': None, 'tags': []},
            'food_consumption': {'output': None, 'activity': None, 'tags': []},
            'leisure': {'output': None, 'activity': None, 'tags': []},
            'mobility': {'output': None, 'mode_of_transport': None, 'distance_in_km': None, 'tags': []}
        }
    }

    params = get_params()

    print('Crawling Instagram..')
    instagram_collection = db['instagram']
    crawl_instagram_data(params, instagram_collection, document)

    print('Crawling Twitter..')
    twitter_collection = db['twitter']
    crawl_twitter_data(params, twitter_collection, document)

    print('Done!')


if __name__ == "__main__":
    main()
