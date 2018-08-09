# system modules
import sys

# external modules
import json
import time

from datetime import datetime
from pymongo.errors import DuplicateKeyError
from requests import Session, adapters

# my modules
sys.path.append("../")
from config import instagram_config as config


def handle_params(params):
    # Start date
    min_date = params['start_date']
    min_timestamp = time.mktime(min_date.timetuple())

    # End date
    max_date = params['end_date']
    max_timestamp = time.mktime(max_date.timetuple())

    # Return Instagram params
    return {
        'lat': params['latitude'],
        'lng': params['longitude'],
        'distance': params['distance'],  # radius of requested area
        'min_timestamp': str(min_timestamp),  # start date
        'max_timestamp': str(max_timestamp),  # end date
        'count': params['count'],  # number of posts(100 max)
        'access_token': config['access_token']  # your access token
    }


def get_instagram_response(params):
    params = handle_params(params)
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    print('Connecting to Instagram API..')
    print('Getting Instagram response..')
    response = session.get("https://api.instagram.com/v1/media/search", params=params, verify=True)
    return response.json()


def crawl_instagram_data(params, collection, document):
    response = get_instagram_response(params)

    print('Inserting Instagram documents..')
    # Decode the JSON data
    dump = json.dumps(response)
    data = json.loads(dump)

    posts = []

    try:
        posts = data['data']

        # Iterate over data to insert each post as a document
        for post in posts:
            document['_id'] = post['id']
            document['link'] = post['link']
            document['time'] = datetime.fromtimestamp(int(post['created_time']))
            document['user'] = process_user_data(post)
            document['text'] = process_text_data(post)
            document['image'] = process_image_data(post)
            document['place'] = process_place_data(post)

            # Try if there is not document with same id yet, otherwise pass
            try:
                # Insert document into database collection (_id is created automatically)
                collection.insert(document)
            except DuplicateKeyError as e:
                print(e)

    except:
        print('OAuthRateLimitException: wait for {} minutes'.format(60))

    print('Done! {} Instagram documents are inserted.'.format(len(posts)))


def process_user_data(post):
    # User information (username is always available)
    return {
        'username': post['user']['username'],
        'home': {
            'name': None,
            'coordinates': None
        }
    }


def process_text_data(post):
    message = None

    if post['caption'] is not None:
        message = post['caption']['text']

    return {
        'message': message,
        'language': None,
        'tokens': [],
        'processed': False
    }


def process_image_data(post):
    # Image (always available)
    return {
        'url': post['images']['standard_resolution']['url'],
        'annotations': [],
        'processed': False
    }


def process_place_data(post):
    place_name = None

    place = post['location']
    # Location information (coordinates are always available)
    if place['name'] is not None:
        place_name = post['location']['name']

    return {
        'name': place_name,
        'coordinates': '%s, %s' % (place['latitude'], place['longitude']),
        'categories': [],
        'distance_to_previous': None,
        'processed': False
    }
