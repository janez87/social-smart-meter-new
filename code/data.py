# Reused code from:
# http://blog.miz.space/data/2016/05/08/instagram-api-data-collection/

import json

from bson.objectid import ObjectId
from io import BytesIO
from PIL import Image
from requests import get, Session, adapters

from classification import activity_check
from images import get_annotations
from text import get_tokens


def collect_data(params):
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    response = session.get("https://api.instagram.com/v1/media/search", params=params, verify=True)
    return response.json()


def store_data(response, db):
    # Decode the JSON data
    dump = json.dumps(response)
    data = json.loads(dump)

    # Insert the data into database and return ObjectId
    return db.input.insert(data)


def handle_data(db, object_id, img_model, img_dataset):
    # Get data from object in database input collection
    cursor = db['input'].find({'_id': ObjectId(object_id)})
    media = cursor.next()
    data = media['data']

    # Process data
    posts = process_data(data, img_model, img_dataset)

    # Insert processed posts to the database output collection
    db.output.insert({'_id': ObjectId(object_id), 'data': posts})


def process_data(data, img_model, img_dataset):
    posts = []

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
        image_url, image_annotations = process_image(post, post_id, img_model, img_dataset)

        # Process location
        place_name, place_category, latitude, longitude = process_location(post)

        # Classify post
        energy_consumption, activities = classification(tokens, image_annotations)

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
            'place_category': place_category,
            'latitude': latitude,
            'longitude': longitude,
            'energy_consumption': energy_consumption,
            'activities': activities
        })

    return posts


# TODO: Move this to new classification file
def classification(tokens, annotations):
    # TODO: to be (further) implemented

    activities = []

    energy_consumption = 0

    output = activity_check(tokens, annotations)

    for domain in output:
        if output[domain]['output'] == 1:
            energy_consumption = 1
            activities.append(domain)

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

    # Process user (get home address, etc.)
    # TODO: to be implemented..
    home_address = ''

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
def process_image(post, post_id, model, dataset):
    image_url = None
    image_annotations = None

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
    # TODO: to be implemented..
    image_annotations = get_annotations(model, dataset, image_url, post_id)

    return image_url, image_annotations


# TODO: Move this to new location processing file
def process_location(post):
    place_name = ''
    place_category = ''
    latitude = None
    longitude = None

    if post['location'] is None:
        return place_name, place_category, latitude, longitude

    # If not empty, get location
    location = post['location']
    latitude = location['latitude']
    longitude = location['longitude']
    place_name = location['name']

    # Process location (get category)
    # TODO: to be implemented..
    place_category = ''

    return place_name, place_category, latitude, longitude


def save_image(url, dir, name):
    response = get(url)
    img = Image.open(BytesIO(response.content))
    filename = "{}.jpg".format(name)
    img.save(dir+filename)
