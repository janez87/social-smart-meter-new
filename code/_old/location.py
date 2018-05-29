import facebook

from geopy.geocoders import Nominatim
from geopy.distance import distance

from config import facebook_config as config

GEOLOCATOR = Nominatim()


def connect_to_fb():
    return facebook.GraphAPI(access_token=config['access_token'], version="2.12")


def match_place(name, latitude, longitude):
    graph = connect_to_fb()

    coordinates = ('%s,%s' % (latitude, longitude))

    # categories = graph.search(
    #     type='placetopic',
    #     topic_filter='all',
    #     limit='2000',  # 2000 is sufficient to retrieve all place topics
    #     field='name, parent_ids')


    # TODO: Add some error catch construction in case the graph connection can't be established
    places = graph.search(q=name,
                          type='place',
                          center=coordinates,
                          distance='100',
                          limit='1',
                          fields='name,location,category_list')

    return places


def get_categories(name, latitude, longitude):
    places = match_place(name, latitude, longitude)

    categories = []

    if places['data']:
        place = places['data'][0]

        if place['category_list']:
            for category in place['category_list']:
                categories.append(category['name'])

    return categories


def get_address_from_place(place):
    latitude, longitude = get_coordinates_from_place(place)

    return get_address_from_coordinates(latitude, longitude)


def get_coordinates_from_place(place):
    location = GEOLOCATOR.geocode(place)
    latitude = location.raw['lat']
    longitude = location.raw['lon']

    return latitude, longitude


def get_country_from_place(place):
    address = get_address_from_place(place)

    return address['country']


def get_city_from_place(place):
    address = get_address_from_place(place)

    return address['city']


def get_address_from_coordinates(latitude, longitude):
    location = GEOLOCATOR.reverse([latitude, longitude])

    return location.raw['address']


def get_country_from_coordinates(latitude, longitude):
    address = get_address_from_coordinates(latitude, longitude)

    return address['country']


def get_city_from_coordinates(latitude, longitude):
    address = get_address_from_coordinates(latitude, longitude)

    return address['city']


def get_distance(coordinates1, coordinates2):
    return distance(coordinates1, coordinates2)


def get_distance_between_posts(previous_post, current_post):
    previous_latitude = previous_post['latitude']
    previous_longitude = previous_post['longitude']
    previous_coordinates = [previous_latitude, previous_longitude]

    current_latitude = current_post['latitude']
    current_longitude = current_post['longitude']
    current_coordinates = [current_latitude, current_longitude]

    return get_distance(previous_coordinates, current_coordinates)


