from dictionaries import image_dictionaries, text_dictionaries, update_text_dictionaries
from location import get_city_from_coordinates, get_coordinates_from_place, get_distance
from user import get_home_town, get_previous_place


def init():
    activities = {
        'food_consumption': {'output': 0, 'activity': '', 'tokens': []},
        'dwelling': {'output': 0, 'activity': '', 'tokens': []},
        'leisure': {'output': 0, 'activity': '', 'tokens': []},
        'mobility': {'output': 0, 'mode_of_transport': '', 'distance_in_km': 0, 'tokens': []}
    }

    return activities


# def get_activities():
#     return ACTIVITIES


def activity_check(named_entities, annotations):
    # latitude = location['latitude']
    # longitude = location['longitude']
    # place = location['place']

    # Get initial (empty) activities object
    activities = init()

    # Image classification
    activities = classify_image(annotations, activities, image_dictionaries)

    # Text classification
    update_text_dictionaries()

    activities = classify_text(named_entities, activities, text_dictionaries)

    return activities

    # classify_location_by_coordinates(latitude, longitude, user_profile)
    # classify_location_by_place(place)

    # If either the image or text output (some token) indicates for a mobility activity,
    # then:
    # classify_location_by_token(token)

    # Update ACTIVITIES


def classify_image(annotations, activities, dictionaries):
    if annotations is not None:
        for annotation in annotations:
            activities = dictionary_check(annotation, activities, dictionaries)

    return activities


def classify_text(named_entities, activities, dictionaries):
    if named_entities is not None:
        for ne in named_entities:
            activities = dictionary_check(ne, activities, dictionaries)

    return activities


def classify_location_by_coordinates(latitude, longitude, user_profile, ACTIVITIES):
    coordinates = [latitude, longitude]

    home_town = get_home_town(user_profile)

    city = get_city_from_coordinates(latitude, longitude)

    if city != home_town:
        prev_place = get_previous_place(user_profile)
        prev_latitude, prev_longitude = get_coordinates_from_place(prev_place)
        prev_coordinates = [prev_latitude, prev_longitude]

        if prev_coordinates != coordinates:
            ACTIVITIES['mobility']['output'] = 1

            distance_in_km = get_distance(prev_coordinates, coordinates).km
            ACTIVITIES['mobility']['distance_in_km'] = distance_in_km

            # Infer distance between current and previous location
            # TODO: Extend this condition statement
            if distance_in_km > 5000:
                ACTIVITIES['mobility']['mode_of_transport'] = 'air'


def classify_location_by_place(place, ACTIVITIES):
    # TODO: Determine place category
    category = ''

    # TODO Determine home and work locations
    home = ''
    work = ''

    if category == home or work:
        ACTIVITIES['dwelling']['output'] = 1

    return dictionary_check(category)


def classify_location_by_token(token):
    output = None

    return output


def dictionary_check(token, activities, dictionaries):
    if token in dictionaries['food_consumption']:
        activities['food_consumption']['output'] = 1
        activities['food_consumption']['tokens'].append(token)

    if token in dictionaries['dwelling']:
        activities['dwelling']['output'] = 1
        activities['dwelling']['tokens'].append(token)

    if token in dictionaries['leisure']:
        activities['leisure']['output'] = 1
        activities['leisure']['tokens'].append(token)

    if token in dictionaries['mobility']:
        activities['mobility']['output'] = 1
        activities['mobility']['tokens'].append(token)
        # classify_location_by_token(token)

    return activities
