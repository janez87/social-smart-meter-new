import sys

import json
import requests
import tweepy

from dateutil.parser import parse
from pymongo.errors import DuplicateKeyError

sys.path.append("../")
from config import twitter_config as config


def handle_params(params):
    # Geocode
    geocode = '{},{},{}km'.format(
        params['latitude'],
        params['longitude'],
        int(params['distance'])/1000
    )

    # Return Twitter params
    return {
        'q': '*',
        'geocode': geocode,
        'count': params['count'],
        'since': params['start_date'].date(),
        'until': params['end_date'].date()
    }


def connect_to_twitter_api():
    # print('Connecting to Twitter API..')
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])

    # Return Twitter API (by Tweepy)
    return tweepy.API(auth)


def get_twitter_user(username):
    api = connect_to_twitter_api()
    twitter_user = None

    # Try to find the Twitter account corresponding to the given username
    try:
        twitter_user = api.get_user(username)
    except:
        pass

    return twitter_user


def crawl_twitter_data(params, collection, document):
    params = handle_params(params)

    api = connect_to_twitter_api()

    print('Getting Twitter response..')
    print('Inserting Twitter documents..')

    count = 0
    max_posts = 500
    # max_id = '1011947099859161089'

    # while count < max_posts:
    try:
        for status in tweepy.Cursor(
                api.search,
                q=params['q'],
                geocode=params['geocode'],
                since=params['since'],
                until=params['until'],
                # max_id=max_id
        ).items(params['count']):
            dump = json.dumps(status._json)
            post = json.loads(dump)

            if post['id']:
                document['_id'] = post['id_str']

            document['link'] = 'https://twitter.com/statuses/{}'.format(post['id_str'])
            document['time'] = process_time(post)
            document['user'] = process_user_data(post)
            document['place'] = process_place_data(post)
            document['text'] = process_text_data(post)
            document['image'] = process_image_data(post)

            # Try if there is not document with same id yet, otherwise pass
            try:
                # Insert document into database collection (_id is created automatically)
                collection.insert(document)
                count += 1
            except DuplicateKeyError as e:
                print(e)

        # max_id = post['id_str']

    except Exception as e:
        print(e)

    print('Done! {} Twitter documents are inserted.'.format(count))

    # TODO: Implement the strategy described on the website below
    # https://www.karambelkar.info/2015/01/how-to-use-twitters-search-rest-api-most-effectively./


def process_time(post):
    time = None

    if post['created_at']:
        time = parse(post['created_at'])

    return time


def process_user_data(post):
    home = None
    username = None

    if post['user']:
        if post['user']['location']:
            home = post['user']['location']

        if post['user']['screen_name']:
            username = post['user']['screen_name']

    return {
        'username': username,
        'home': {
            'name': home,
            'coordinates': None
        }
    }


def process_place_data(post):
    place_name = None
    coordinates = None
    categories = []

    # Location information (coordinates are always available)
    if post['place']:
        if post['place']['name']:
            place_name = post['place']['name']
        if post['place']['place_type']:
            categories.append(post['place']['place_type'])

    if post['coordinates']:
        coordinates = post['coordinates']['coordinates']
        coordinates = '{}, {}'.format(coordinates[1], coordinates[0])

    return {
        'name': place_name,
        'coordinates': coordinates,
        'categories': categories,
        'distance_to_previous': None,
        'processed': False
    }


def process_text_data(post):
    message = None
    language = None

    if post['text']:
        message = post['text']

    if post['lang']:
        language = post['lang']

    return {
        'message': message,
        'language': language,
        'tokens': [],
        'distance_to_home': None,
        'user_at_home': False,
        'processed': False
    }


def process_image_data(post):
    url = None

    if 'media' in post['entities'].keys():
        url = post['entities']['media'][0]['media_url_https']

    return {
        'url': url,
        'annotations': [],
        'processed': False
    }
