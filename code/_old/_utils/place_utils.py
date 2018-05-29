from geopy.geocoders import Nominatim
from geopy.distance import distance

GEOLOCATOR = Nominatim()


def get_distance_between_posts(previous_post, current_post):
    previous_latitude = previous_post['latitude']
    previous_longitude = previous_post['longitude']
    previous_coordinates = [previous_latitude, previous_longitude]

    current_latitude = current_post['latitude']
    current_longitude = current_post['longitude']
    current_coordinates = [current_latitude, current_longitude]

    return distance(previous_coordinates, current_coordinates)