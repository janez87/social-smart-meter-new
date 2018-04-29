from geopy.geocoders import Nominatim
from geopy.distance import distance

GEOLOCATOR = Nominatim()

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
