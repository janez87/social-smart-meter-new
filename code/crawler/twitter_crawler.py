import sys

import json
import tweepy

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
        'until': params['end_date'].date(),
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


def get_twitter_response(params):
    params = handle_params(params)

    api = connect_to_twitter_api()

    print('Getting Twitter response..')
    try:
        for tweet in tweepy.Cursor(
                api.search,
                q=params['q'],
                geocode=params['geocode'],
                count=params['count'],
                since=params['since'],
                until=params['until']
        ).items():
            print(tweet)
    except Exception as e:
        print(e)


def crawl_twitter_data(params, collection, document):
    params = handle_params(params)

    api = connect_to_twitter_api()

    print('Getting Twitter response..')
    print('Inserting Twitter documents..')
    try:
        for status in tweepy.Cursor(
                api.search,
                q=params['q'],
                geocode=params['geocode'],
                since=params['since'],
                until=params['until']
        ).items(params['count']):
            dump = json.dumps(status._json)
            post = json.loads(dump)

            # print(post)

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
            except DuplicateKeyError as e:
                print(e)
    except Exception as e:
        print(e)

    print('Done! All Twitter documents are inserted.')


def process_time(post):
    time = None

    if post['created_at']:
        time = post['created_at']

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
        'home': home
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
        coordinates = post['coordinates']

    return {
        'name': place_name,
        'coordinates': coordinates,
        'categories': categories,
        'distance_to_previous': None
    }


def process_text_data(post):
    caption = None
    language = None

    if post['text']:
        caption = post['text']

    if post['lang']:
        language = post['lang']

    return {
        'caption': caption,
        'language': language,
        'tokens': []
    }


# TODO: Find out where the url to the image is stored?!
def process_image_data(post):
    return {
        'url': None,
        'annotations': []
    }
