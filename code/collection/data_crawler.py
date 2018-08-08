import sys

from pymongo import MongoClient
from datetime import datetime

from instagram_crawler import crawl_instagram_data
from twitter_crawler import crawl_twitter_data

sys.path.append('../')
from config import mongo_config as config


def get_params(start_date, end_date):
    # Amsterdam neighborhoods
    amsterdam = {
        'Westpoort': {'latitude': '52.403187', 'longitude': '4.792265', 'radius': '5000'},
        'West': {'latitude': '52.353369', 'longitude': '4.828562', 'radius': '5000'},
        'Centrum': {'latitude': '52.402294', 'longitude': '4.923541', 'radius': '5000'},
        'Noord': {'latitude': '52.398831', 'longitude': '5.041166', 'radius': '5000'},
        'Zuidoost': {'latitude': '52.324137', 'longitude': '4.957676', 'radius': '5000'}
    }
    # amsterdam = {
    #     'Centrum': {'latitude': '52.372374', 'longitude': '4.898844', 'radius': '1500'},
    #     'Noord': {'latitude': '52.395940', 'longitude': '4.924071', 'radius': '2000'},
    #     'Oost': {'latitude': '52.354438', 'longitude': '4.935738', 'radius': '2000'},
    #     'Zuidoost': {'latitude': '52.304499', 'longitude': '4.971431', 'radius': '2000'},
    #     'Zuid': {'latitude': '52.342684', 'longitude': '4.885141', 'radius': '2000'},
    #     'West': {'latitude': '52.388177', 'longitude': '4.862139', 'radius': '1500'},
    #     'Nieuw-West': {'latitude': '52.360300', 'longitude': '4.810984', 'radius': '3000'},
    #     'Westpoort': {'latitude': '52.403051', 'longitude': '4.826776', 'radius': '2000'}
    # }

    istanbul = {
        '1': {'latitude': '41.068258', 'longitude': '28.664307', 'radius': '5000'},
        '2': {'latitude': '41.092642', 'longitude': '28.765154', 'radius': '5000'},
        '3': {'latitude': '40.993586', 'longitude': '28.648200', 'radius': '5000'},
        '4': {'latitude': '41.015633', 'longitude': '28.729213', 'radius': '5000'},
        '5': {'latitude': '41.050750', 'longitude': '28.831453', 'radius': '5000'},
        '6': {'latitude': '40.987185', 'longitude': '28.829332', 'radius': '5000'},
        '7': {'latitude': '41.126666', 'longitude': '28.873160', 'radius': '5000'},
        '8': {'latitude': '41.078336', 'longitude': '28.937297', 'radius': '5000'},
        '9': {'latitude': '41.011961', 'longitude': '28.931074', 'radius': '5000'},
        '10': {'latitude': '41.088416', 'longitude': '29.033801', 'radius': '5000'},
        '11': {'latitude': '41.160411', 'longitude': '29.055341', 'radius': '5000'},
        '12': {'latitude': '41.091171', 'longitude': '29.133347', 'radius': '5000'},
        '13': {'latitude': '41.033889', 'longitude': '29.041947', 'radius': '5000'},
        '14': {'latitude': '40.994163', 'longitude': '29.074830', 'radius': '5000'},
        '15': {'latitude': '41.031146', 'longitude': '29.123590', 'radius': '5000'},
        '16': {'latitude': '41.044651', 'longitude': '29.199141', 'radius': '5000'},
        '17': {'latitude': '40.943592', 'longitude': '29.156942', 'radius': '5000'},
        '18': {'latitude': '40.997134', 'longitude': '29.218187', 'radius': '5000'},
        '19': {'latitude': '40.937966', 'longitude': '29.275148', 'radius': '5000'},
        '20': {'latitude': '40.900205', 'longitude': '29.222532', 'radius': '5000'},
        '21': {'latitude': '40.847703', 'longitude': '29.296290', 'radius': '5000'},
        '22': {'latitude': '40.903837', 'longitude': '29.375094', 'radius': '5000'},
    }

    # Choose a neighborhood
    # neighborhood = istanbul['10']
    neighborhood = amsterdam['Zuidoost']

    # Coordinates
    latitude = neighborhood['latitude']
    longitude = neighborhood['longitude']

    # Radius in meters
    distance = neighborhood['radius']

    # Start date
    # start_date = datetime(2018, 5, 28, 11, 55, 0)

    # End date
    # end_date = datetime(2018, 5, 28, 12, 0, 0)

    # Number of posts to retrieve (max = 100)
    count = 100000

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


def main(source):
    print('Connecting to Mongo..')
    db = connect_to_db()
    print('Connection established!\n')

    document = {
        '_id': None,
        'link': None,
        'time': None,
        'user': {
            'username': None,
            'home': {
                'name': None,
                'coordinates': None
            }
        },
        'text': {
            'message': None,
            'language': None,
            'tokens': [],
            'processed': False
        },
        'image': {
            'url': None,
            'annotations': [],
            'processed': False
        },
        'place': {
            'name': None,
            'coordinates': None,
            'categories': [],
            'distance_to_previous': None,
            'user_at_home': False,
            'processed': False
        },
        'area_name': None,
        'categories': [],
        'output': {
            'dwelling': {
                'confidence': 0,
                'terms': []
            },
            'food': {
                'confidence': 0,
                'terms': []
            },
            'leisure': {
                'confidence': 0,
                'terms': []
            },
            'mobility': {
                'confidence': 0,
                'terms': []
            }
        }
    }

    year = 2018
    month = 6
    day = 27

    t = 60

    if source == '--instagram':
        print('Crawling Instagram..')

        instagram_collection = db['instagram']

        for h in range(20, 24):
            for m in range(0, int(60 / t)):
                if m == int((60 / t - 1)):
                    if h == 23:
                        start_date = datetime(year, month, day, h, t * m, 0)
                        end_date = datetime(year, month, day + 1, 0, 0, 0)
                    else:
                        start_date = datetime(year, month, day, h, t * m, 0)
                        end_date = datetime(year, month, day, h + 1, 0, 0)
                else:
                    start_date = datetime(year, month, day, h, t * m, 0)
                    end_date = datetime(year, month, day, h, t * m + t, 0)

                params = get_params(start_date, end_date)
                print('{} to {}'.format(start_date, end_date))
                crawl_instagram_data(params, instagram_collection, document)

        # start_date = datetime(year, month, day, 0, 0, 0)
        # end_date = datetime(year, month, day+1, 0, 0, 0)
        # params = get_params(start_date, end_date)
        # print('{} to {}'.format(start_date, end_date))
        # crawl_instagram_data(params, instagram_collection, document)

    elif source == '--twitter':
        print('Crawling Twitter..')

        twitter_collection = db['twitter']

        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = datetime(year, month, day+1, 0, 0, 0)

        params = get_params(start_date, end_date)

        crawl_twitter_data(params, twitter_collection, document)

    print('Done!')


if __name__ == "__main__":
    main(sys.argv[1])
