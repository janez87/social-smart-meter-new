# system modules
import sys

# my modules
from googleplaces import GooglePlaces, types

sys.path.append('../')
from config import google_config as config


def connect_to_google_places_api():
    return GooglePlaces(config['api_key'])


def get_lat_and_lng(coordinates):
    coordinates = coordinates.split(', ')

    return {
        'lat': float(coordinates[0]),
        'lng': float(coordinates[1])
    }


def get_google_place_categories(place):
    api = connect_to_google_places_api()

    query_result = api.nearby_search(
        lat_lng=get_lat_and_lng(place['coordinates']),
        name=place['name'],
        radius=50)

    categories = place['categories']

    if query_result.places:
        place = query_result.places[0]
        place.get_details()

        if place.types:
            for category in place.types:
                if category not in categories:
                    categories.append(category)

    return categories


def query_coordinates_by_place_name(place_name, coordinates):
    api = connect_to_google_places_api()

    query_result = api.nearby_search(
        lat_lng=get_lat_and_lng(coordinates),
        keyword=place_name
    )

    if query_result.places:
        place = query_result.places[0]
        place.get_details()

        print(place)
