import facebook

from requests import Session, adapters

from config import facebook_config


def refresh_facebook_access_token():
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))

    # Parameters
    # TODO: Check if fb_exchange_token requires the short-term access token or the user token
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': facebook_config['app_id'],
        'client_secret': facebook_config['app_secret'],
        'fb_exchange_token': facebook_config['user_token']
    }

    # Get long-term access token (by exchanging the short-term one)
    response = session.get("https://graph.facebook.com/v2.11/oauth/access_token", params=params, verify=True)

    # Get json response
    json_response = response.json()

    # Refresh access token
    facebook_config['access_token'] = json_response['access_token']


def connect_to_facebook_api(token_type):
    # Create Facebook Graph API
    if token_type is 'long_term_token':
        # Refresh long-term access token
        refresh_facebook_access_token()

        # Use long-term token
        graph = facebook.GraphAPI(access_token=facebook_config['access_token'], version="2.12")

    elif token_type is 'user_token':
        # Use user token
        graph = facebook.GraphAPI(access_token=facebook_config['user_token'], version="2.12")

    else:
        # Use short-term token (expires after 2 hours)
        graph = facebook.GraphAPI(access_token=facebook_config['access_token'], version="2.12")

    return graph


def match_place(place_name, latitude, longitude, graph):
    coordinates = ('%s,%s' % (latitude, longitude))

    # TODO: Add some error catch construction in case the graph connection can't be established
    places = graph.search(q=place_name,
                          type='place',
                          center=coordinates,
                          distance='100',
                          limit='1',
                          fields='name,location,category_list')

    return places


def get_place_categories(place_name, latitude, longitude, graph):
    places = match_place(place_name, latitude, longitude, graph)

    categories = []

    if places['data']:
        place = places['data'][0]

        if place['category_list']:
            for category in place['category_list']:
                categories.append(category['name'])

    return categories


def get_all_place_categories(graph):
    return graph.search(
        type='placetopic',
        topic_filter='all',
        limit='2000',  # 2000 is sufficient to retrieve all place topics
        field='name, parent_ids')
