import sys

from googleplaces import GooglePlaces, types

sys.path.append('../')
from config import google_config as config

# sys.path.append('./enrichment')
# from place_processing import get_coordinates_from_place


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


def query_place(token, location):
    api = connect_to_google_places_api()

    query_result = api.nearby_search(
        lat_lng=get_lat_and_lng(location['coordinates']),
        name=token,
        radius=50)

    if query_result.places:
        place = query_result.places[0]
        place.get_details()

        # print(token, ' > ', place)


def query_coordinates_by_place_name(place_name, coordinates):
    api = connect_to_google_places_api()

    query_result = api.nearby_search(
        lat_lng=get_lat_and_lng(coordinates),
        keyword=place_name
        # radius=20000
    )

    if query_result.places:
        place = query_result.places[0]
        place.get_details()

        print(place)


# def main():
#     place_name = 'Coffeemania Slotermeer'
#     coordinates = '52.3554281, 4.8053591'
#
#     query_coordinates_by_place_name(place_name, coordinates)
#     # location = {
#     #     "name": "Amsterdam, Netherlands",
#     #     "coordinates": "52.3777, 4.9001",
#     #     "categories": [],
#     #     "distance_to_previous": 0.0,
#     #     "processed": False
#     # }
#     #
#     # tokens = [
#     #     "Thank",
#     #     "taking",
#     #     "away",
#     #     "Amsterdam",
#     #     "thank",
#     #     "always",
#     #     "patient",
#     #     "I",
#     #     "make",
#     #     "try",
#     #     "200",
#     #     "times",
#     #     "good",
#     #     "selfie"
#     # ]
#     #
#     # for token in tokens:
#     #     query_place(token, location)
#
#     # place = {
#     #     'name': 'Amsterdam Roest',
#     #     'coordinates': get_lat_and_lng('52.371939, 4.9264524'),
#     #     'categories': [],
#     #     'distance_to_previous': None
#     # }
#     #
#     # get_place_categories(place)
#
#
# if __name__ == "__main__":
#     main()
