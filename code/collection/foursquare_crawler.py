# system modules
import sys

# external modules
from requests import Session, adapters

# my modules
sys.path.append("../")
from config import foursquare_config as config


def get_response(params):
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    response = session.get("https://api.foursquare.com/v2/venues/search", params=params, verify=True)
    return response.json()


def get_foursquare_place_categories(place):
    params = {
        'll': place['coordinates'],
        'intent': 'match',
        'radius': 50,
        'limit': 1,
        'query': place['name'],
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'v': '20180802'
    }

    categories = place['categories']

    response = get_response(params)

    meta = response['meta']
    if 'code' in meta.keys():
        print(meta['code'])

    response = response['response']

    if 'venues' in response.keys():
        venues = response['venues']

        if venues:
            for category in venues[0]['categories']:
                if category not in categories:
                    categories.append(category['name'])

    return categories


def query_place_name(place_name):
    categories = []
    coordinates = None

    params = {
        'near': 'Amsterdam, Netherlands',
        # 'intent': 'match',
        'limit': 1,
        'query': place_name,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'v': '20180802'
    }

    response = get_response(params)

    meta = response['meta']
    if 'code' in meta.keys():
        print(meta['code'])

    response = response['response']

    if 'venues' in response.keys():
        venues = response['venues']

        if venues:
            for category in venues[0]['categories']:
                if category not in categories:
                    categories.append(category['name'])

            if 'location' in venues[0].keys():
                location = venues[0]['location']
                print(location)
                coordinates = '{}, {}'.format(location['lat'], location['lng'])

    return categories, coordinates


# def main():
#     place_name = 'Coffeemania Slotermeer'
#
#     coordinates, categories = query_place_name(place_name)
#
#     print(coordinates)
#     print(categories)
#
#     place = {
#         'name': 'Corendon Village Amsterdam',
#         'coordinates': '52.329199375348, 4.7853669647758',
#         'categories': []
#     }
#
#     print(get_foursquare_place_categories(place))
#
# #     place = {
# #         "name": "WESTERPARK",
# #         "coordinates": "52.386625994325, 4.8740168452806",
# #         "categories": [
# #             "neighborhood",
# #             "political"
# #         ],
# #         "distance_to_previous": 0.0,
# #         "processed": False
# #     }
# #
# #     params = {
# #         'll': place['coordinates'],
# #         'intent': 'match',
# #         'radius': 50,
# #         'limit': 1,
# #         'query': place['name'],
# #         'client_id': config['client_id'],
# #         'client_secret': config['client_secret'],
# #         'v': '20180531'
# #     }
# #
# #     for category in get_response(params)['response']['venues'][0]['categories']:
# #         print(category['name'])
#
#
# if __name__ == "__main__":
#     main()
