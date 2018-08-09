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
        'v': config['version']
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
        'limit': 1,
        'query': place_name,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'v': config['version']
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
                coordinates = '{}, {}'.format(location['lat'], location['lng'])

    return categories, coordinates
