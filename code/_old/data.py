# Reused code from:
# http://blog.miz.space/data/2016/05/08/instagram-api-data-collection/

import json
import tweepy

from bson.objectid import ObjectId
from io import BytesIO
from PIL import Image
from requests import get, Session, adapters

from config import fb_config, twitter_config
from classification import activity_check
from images import get_annotations
from location import get_categories, get_distance_between_posts
from text import get_tokens
from user import query_on_username


def refresh_facebook_access_token():
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))

    # Get long-term access token (by exchanging the short-term one)
    response = session.get("https://graph.facebook.com/v2.11/oauth/access_token", params=params, verify=True)

    # Get json response
    json_response = response.json()

    # Refresh access token
    fb_config['access_token'] = json_response['access_token']

#
def connect_to_twitter(config):
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])

    # Return Twitter API (by Tweepy)
    return tweepy.API(auth)


def collect_instagram_data(params):
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    response = session.get("https://api.instagram.com/v1/media/search", params=params, verify=True)
    return response.json()


def collect_user_data(params):
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    response = session.get("https://api.instagram.com/v1/users/search", params=params, verify=True)
    return response.json()


def store_data(response, db):
    # Decode the JSON data
    dump = json.dumps(response)
    data = json.loads(dump)

    # Insert the data into database and return ObjectId
    return db.input.insert(data)


def handle_data(db, object_id, img_model, img_dataset, tf_params):
    # Get data from object in database input collection
    cursor = db['input'].find({'_id': ObjectId(object_id)})
    media = cursor.next()
    data = media['data']

    # Process data
    posts = process_data(db, data, img_model, img_dataset, tf_params)

    # Insert processed posts to the database output collection
    db.output.insert({'_id': ObjectId(object_id), 'data': posts})


def process_data(db, data, img_model, img_dataset, tf_params):
    posts = []

    collection = db.output

    # Loop through posts to process the data
    for post in data:
        # Get post id
        post_id = post['id']

        # Get (url) link to post
        link = post['link']

        # Process user
        username, home_address = process_user(post)

        # Process text
        text, tokens = process_text(post)

        # Process image
        image_url, image_annotations = process_image(post, post_id, img_model, img_dataset, tf_params)

        # Process location
        place_name, place_categories, latitude, longitude, traveled_distance = process_location(post, username, collection)

        # Classify post
        energy_consumption, activities = classification(tokens, image_annotations, traveled_distance)

        # Add object to posts array
        posts.append({
            '_id': post_id,
            'link': link,
            'username': username,
            'home_address': home_address,
            'text': text,
            'tokens': tokens,
            'image_url': image_url,
            'image_annotations': image_annotations,
            'place_name': place_name,
            'place_categories': place_categories,
            'latitude': latitude,
            'longitude': longitude,
            'traveled_distance': traveled_distance,
            'energy_consumption': energy_consumption,
            'activities': activities
        })

    return posts


# TODO: Move this to new classification file
def classification(tokens, annotations, traveled_distance):
    # TODO: to be (further) implemented

    activities = []

    energy_consumption = 0

    output = activity_check(tokens, annotations)

    for domain in output:
        if output[domain]['output'] == 1:
            energy_consumption = 1
            activities.append(domain)

    # If distance > 1km, classify as mobility.
    if traveled_distance.km > 1:
        if 'mobility' not in activities:
            activities.append('mobility')

        # TODO: Infer mode of transport

    return energy_consumption, activities


# TODO: Move this to new user processing file
def process_user(post):
    username = None
    home_address = None

    if post['user'] is None:
        return username, home_address

    # If not empty, get username
    user = post['user']
    username = user['username']

    # Connect to Twitter API
    api = connect_to_twitter(twitter_config)

    # Check for Twitter account
    try:
        twitter_user = api.get_user(user)
        if twitter_user.location is not None:
            home_address = twitter_user.location
    except:
        pass

    return username, home_address


# TODO: Move this to new text processing file
def process_text(post):
    text = None
    # named_entities = None
    tokens = None

    if post['caption'] is None:
        return text, tokens

    # If not empty, get caption
    caption = post['caption']
    text = caption['text']

    # Process text (get named entities)
    tokens = get_tokens(text)

    # TODO: to be implemented..
    # named_entities = []

    return text, tokens


# TODO: Move this to new image processing file
def process_image(post, post_id, model, dataset, tf_params):
    image_url = None
    image_annotations = []

    if post['images'] is None:
        return image_url, image_annotations

    # If not empty, get images
    # TODO: Make this work for multiple images
    images = post['images']
    standard_resolution = images['standard_resolution']
    image_url = standard_resolution['url']

    # Save image to input directory
    input_dir = '../data/instagram/images/input/'
    save_image(image_url, input_dir, post_id)

    # Process image (get annotations)
    # TODO: to be (further) implemented..
    image_annotations = get_annotations(model, dataset, image_url, post_id, tf_params)

    return image_url, image_annotations


# TODO: Move this to new location processing file
def process_location(post, username, collection):
    place_name = ''
    place_categories = []
    latitude = None
    longitude = None

    if post['location'] is None:
        return place_name, place_categories, latitude, longitude

    # If not empty, get location
    location = post['location']
    latitude = location['latitude']
    longitude = location['longitude']
    place_name = location['name']

    # Process location (get category)
    place_categories = get_categories(place_name, latitude, longitude)

    # Check if the place differs from the last checked-in place
    posts = query_on_username(username, collection)

    # Only return the most recent post (which is the last one in the array)
    previous_post = posts[(len(posts)-1)]

    # Determine distance "traveled" between this post and the previous post created by the user
    traveled_distance = get_distance_between_posts(previous_post, post)

    return place_name, place_categories, latitude, longitude, traveled_distance


def save_image(url, dir, name):
    response = get(url)
    img = Image.open(BytesIO(response.content))
    filename = "{}.jpg".format(name)
    img.save(dir+filename)
