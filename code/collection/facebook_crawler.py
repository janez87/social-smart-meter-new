import time
import facebook

from config import facebook_config as config


def connect_to_fb_api():
    # if config['extended_token']['expires_in'] + config['extended_on'] < time.time():
    #     graph = facebook.GraphAPI(access_token=config['short_lived_access_token'], version="2.12")
    #     config['extended_token'] = graph.extend_access_token(config['app_id'], config['app_secret'])
    #     config['extended_on'] = time.time()

    return facebook.GraphAPI(access_token=config['short_lived_access_token'], version="2.12")


# TODO: Check why "Amsterdam, Netherlands" gets "City" topic twice
def get_facebook_place_categories(place):
    graph = connect_to_fb_api()

    # TODO: Add some error catch construction in case the graph connection can't be established
    places = graph.search(q=place['name'],
                          type='place',
                          center=place['coordinates'],
                          distance='100',
                          limit='1',
                          fields='name,location,category_list')

    categories = []

    if places['data']:
        place = places['data'][0]

        if place['category_list']:
            for category in place['category_list']:
                categories.append(category['name'])

    return categories


def get_all_place_categories():
    graph = connect_to_fb_api()

    return graph.search(
        type='placetopic',
        topic_filter='all',
        limit='2000',  # 2000 is sufficient to retrieve all place topics
        field='name, parent_ids')
