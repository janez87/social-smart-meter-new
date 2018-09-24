# external modules
from geopy.geocoders import Nominatim
from geopy.distance import distance
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

GEOLOCATOR = Nominatim()


def setup():
    return


def get_distance_between_places(previous_place, current_place):
    distance_between_places = None

    if previous_place['coordinates']:
        previous_coordinates = previous_place['coordinates']

        if current_place['coordinates']:
            current_coordinates = current_place['coordinates']

            return distance(previous_coordinates, current_coordinates).km

    return distance_between_places


def determine_distance_to_previous(place, username, time, collection):
    distance = 0.0

    # Find documents from the same user
    documents = collection.find({'user.username': username})

    # Keep documents that are created before the current document
    if documents.count() > 0:
        previous_documents = []

        for document in documents:
            if document['time'] < time:
                previous_documents.append(document)

        if previous_documents:
            # Only return the most recent previous post (which is the last one in the array)
            previous_document = previous_documents[(len(previous_documents) - 1)]

            # Determine "traveled" distance (in km) between this post and the previous post created by the user
            distance = get_distance_between_places(previous_document['place'], place)

    return distance


def get_coordinates_from_place(place):
    latitude = None
    longitude = None

    location = GEOLOCATOR.geocode(place)

    if location:
        latitude = location.raw['lat']
        longitude = location.raw['lon']

    return latitude, longitude


def determine_distance_to_home(place, user):
    if user['home']['name']:
        home_coordinates = get_coordinates_from_place(user['home']['name'])

        return distance(place['coordinates'], home_coordinates).km

    return None


def determine_area_name(place, areas):
    coordinates = place['coordinates'].split(', ')
    point = Point([float(coordinates[1]), float(coordinates[0])])

    # Check multipolygons
    for area in areas['multipolygons']:
        for polygon_vector in area['geometry']['coordinates'][0]:
            polygon = Polygon(polygon_vector)
            if polygon.contains(point):
                return area['properties']['name']


    # Check polygons
    for area in areas['polygons']:
        polygon = Polygon(area['geometry']['coordinates'][0])
        if polygon.contains(point):
            return area['properties']['name']

    return None
