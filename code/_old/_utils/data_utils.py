from bson.objectid import ObjectId
from io import BytesIO
from langdetect import detect
from PIL import Image
from pymongo import MongoClient
from requests import get

from dictionaries import merged_dictionaries as dictionaries
from facebook_utils import get_place_categories
from image_utils import get_annotations
from place_utils import get_distance_between_posts
from text_utils import get_tokens
from twitter_utils import get_twitter_home_address


def connect_to_db(db_name):
    # First, run the "mongod" command from the terminal to establish a connection
    # Then, connect to the MongoClient
    client = MongoClient('localhost', 27017)

    # Return the database
    return client[db_name]


def query_on_attribute(query, attribute, collection):
    documents = collection.find({'data.{}'.format(attribute): query})

    posts = []

    for document in documents:
        data = document['data']
        for post in data:
            if post[attribute] == query:
                posts.append(post)

    return posts


# TODO: Make this suitable for Twitter as well
def process_data(object_id, db, save_images):
    # Get data from object in database input collection
    # TODO: Build in some error catching
    cursor = db['input_instagram'].find({'_id': ObjectId(object_id)})
    media = cursor.next()
    data = media['data']

    posts = []

    # Loop through posts to process the data
    for post in data:
        # Get post id
        post_id = post['id']

        # Process user
        username = process_user(post)

        # Process text
        text = process_text(post)

        # Process image
        image_url = process_image(post, post_id, save_images)

        # Process place
        place_name, latitude, longitude = process_place(post)

        # Add object to posts array
        posts.append({
            '_id': post_id,
            'link': post['link'],
            'created_time': post['created_time'],
            'username': username,
            'home_address': None,
            'text': text,
            'language': None,
            'text_tokens': [],
            'image_url': image_url,
            'image_annotations': [],
            'place_name': place_name,
            'place_categories': [],
            'latitude': latitude,
            'longitude': longitude,
            'traveled_distance': None,
            'energy_consumption': None,
            'activities': []
        })

    # Close the cursor
    cursor.close()

    # Insert processed posts to the database output collection
    db.output_instagram.insert({'_id': ObjectId(object_id), 'data': posts})


def enrich_data(enrichments, object_id, db, graph):
    cursor = db['output_instagram'].find({'_id': ObjectId(object_id)})
    media = cursor.next()
    data = media['data']

    # Iterate through posts to enrich the data
    for post in data:
        language = post['language']
        if enrichments['text_language'] is True:
            language = enrich_text_with_language(post)

        place_categories = post['place_categories']
        if enrichments['place_categories'] is True:
            place_categories = enrich_place_with_categories(post, graph)

        traveled_distance = post['traveled_distance']
        if enrichments['place_distance'] is True:
            traveled_distance = enrich_place_with_distance(post, db)

        home_address = post['home_address']
        if enrichments['user_home'] is True:
            home_address = enrich_user_with_home_address(post)

        index = data.index(post)
        db.output_instagram.update_one({
            '_id': ObjectId(object_id)
        }, {
            '$set': {
                'data.{}.language'.format(index): language,
                'data.{}.home_address'.format(index): home_address,
                'data.{}.place_categories'.format(index): place_categories,
                'data.{}.traveled_distance'.format(index): traveled_distance
            }
        }, upsert=False)

    # Close the cursor
    cursor.close()


def initialize_activities():
    activities = {
        'food_consumption': {'output': 0, 'activity': '', 'tokens': []},
        'dwelling': {'output': 0, 'activity': '', 'tokens': []},
        'leisure': {'output': 0, 'activity': '', 'tokens': []},
        'mobility': {'output': 0, 'mode_of_transport': '', 'distance_in_km': 0, 'tokens': []}
    }

    return activities


def dictionary_check(token, activities):
    # checked_token = {
    #     'token': token,
    #     'dwelling': 0,
    #     'food_consumption': 0,
    #     'leisure': 0,
    #     'mobility': 0
    # }

    # token_in_dictionary = 0

    if token in dictionaries['dwelling']:
        # checked_token['dwelling'] = 1
        # token_in_dictionary = 1
        activities['dwelling']['output'] = 1
        activities['dwelling']['tokens'].append(token)

    if token in dictionaries['food_consumption']:
        # checked_token['food_consumption'] = 1
        # token_in_dictionary = 1
        activities['food_consumption']['output'] = 1
        activities['food_consumption']['tokens'].append(token)

    if token in dictionaries['leisure']:
        # checked_token['leisure'] = 1
        # token_in_dictionary = 1
        activities['leisure']['output'] = 1
        activities['leisure']['tokens'].append(token)

    if token in dictionaries['mobility']:
        # checked_token['mobility'] = 1
        # token_in_dictionary = 1
        activities['mobility']['output'] = 1
        activities['mobility']['tokens'].append(token)

    # return checked_token, token_in_dictionary
    return activities


def classify_data(classification, models, object_id, db):
    cursor = db['output_instagram'].find({'_id': ObjectId(object_id)})
    media = cursor.next()
    data = media['data']

    # Iterate through posts to enrich the data
    for post in data:
        activities = initialize_activities()

        text_tokens = post['text_tokens']
        if classification['text'] is True:
            text_tokens = classify_text(post)

            for token in text_tokens:
                activities = dictionary_check(token, activities)

        image_annotations = post['image_annotations']
        if classification['image'] is True:
            # image_annotations = classify_image(post, models)

            for annotation in post['image_annotations']:
                activities = dictionary_check(annotation['class'], activities)

        place_categories = post['place_categories']
        if classification['place'] is True:
            for category in post['place_categories']:
                activities = dictionary_check(category, activities)

        # If distance > 0 km, classify implicit mobility activity
        if post['traveled_distance'] > 0.0:
            activities['mobility']['output'] = 1
            activities['mobility']['distance_in_km'] = post['traveled_distance']

        index = data.index(post)
        db.output_instagram.update_one({
            '_id': ObjectId(object_id)
        }, {
            '$set': {
                'data.{}.text_tokens'.format(index): text_tokens,
                'data.{}.image_annotations'.format(index): image_annotations,
                'data.{}.place_categories'.format(index): place_categories,
                'data.{}.activities'.format(index): activities
            }
        }, upsert=False)

    # Close the cursor
    cursor.close()


def process_user(post):
    username = None

    # If not empty, get username
    if post['user'] is not None:
        user = post['user']
        username = user['username']

    return username


def enrich_user_with_home_address(post):
    home_address = post['home_address']

    if post['username'] is not None:
        home_address = get_twitter_home_address(post['username'])

    return home_address


def process_text(post):
    text = None

    # If not empty, get caption
    if post['caption'] is not None:

        caption = post['caption']
        text = caption['text']

    return text


def enrich_text_with_language(post):
    language = post['language']

    # TODO: Fix "LangDetectException: No features in text."
    # https://github.com/Mimino666/langdetect/issues/44
    if post['text'] is not None:
        text = post['text']
        text = text.replace('\n', ' ').replace('\r', '')
        language = detect(text)

    return language


def classify_text(post):
    text_tokens = []

    # If not empty, get text tokens
    if post['text'] is not None:
        text_tokens = get_tokens(post['text'])

        # for text_token in text_tokens:
        #     # Check if in dictionaries
        #     classified_token, token_in_dictionary = dictionary_check(text_token)
        #
        #     # If in dictionary, add token to classified_tokens array
        #     if token_in_dictionary:
        #         classified_tokens.append(classified_token)

    return text_tokens


def process_image(post, post_id, save_images):
    image_url = None

    # If not empty, get images
    if post['images'] is not None:
        # TODO: Make this work for multiple images
        images = post['images']
        standard_resolution = images['standard_resolution']
        image_url = standard_resolution['url']

        # If desired, save image to input directory
        if save_images:
            input_dir = '../data/instagram/images/input/'
            save_image(image_url, input_dir, post_id)

    return image_url


def save_image(url, dir, name):
    response = get(url)
    img = Image.open(BytesIO(response.content))
    filename = "{}.jpg".format(name)
    img.save(dir+filename)


def classify_image(post, models):
    # Process image (get annotations)
    image_annotations = get_annotations(post['image_url'], post['_id'], models)

    return image_annotations


def process_place(post):
    place_name = ''
    latitude = None
    longitude = None

    # If not empty, get place
    if post['location'] is not None:
        location = post['location']
        latitude = location['latitude']
        longitude = location['longitude']
        place_name = location['name']

    return place_name, latitude, longitude


def enrich_place_with_categories(post, graph):
    place_categories = []

    # If place_name is not empty, get place categories
    if post['place_name'] is not None:
        # Get place categories
        place_categories = get_place_categories(post['place_name'], post['latitude'], post['longitude'], graph)

    return place_categories


def enrich_place_with_distance(current_post, db):
    distance = 0.0

    # Specify which collection to query
    collection = db['output_instagram']

    # Query posts from the same user
    attribute = 'username'

    posts = query_on_attribute(current_post[attribute], attribute, collection)

    # Keep posts that are created before the current post
    if posts:
        previous_posts = []

        for post in posts:
            if post['created_time'] < current_post['created_time']:
                previous_posts.append(post)

        if previous_posts:
            # Only return the most recent post (which is the last one in the array)
            most_recent_previous_post = previous_posts[(len(previous_posts) - 1)]

            # Determine "traveled" distance (in km) between this post and the previous post created by the user
            distance = get_distance_between_posts(most_recent_previous_post, current_post).km

    return distance


def classify_place():
    return

