import sys

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


def get_place_categories(place):
    api = connect_to_google_places_api()

    query_result = api.nearby_search(
        lat_lng=get_lat_and_lng(place['coordinates']),
        name=place['name'],
        radius=100)

    categories = []

    if query_result.places:
        place = query_result.places[0]
        place.get_details()

        if place.types:
            for category in place.types:
                categories.append(category)

    return categories


# def main():
#     place = {
#         'name': 'Amsterdam Roest',
#         'coordinates': get_lat_and_lng('52.371939, 4.9264524'),
#         'categories': [],
#         'distance_to_previous': None
#     }
#
#     get_place_categories(place)
#
#
# if __name__ == "__main__":
#     main()