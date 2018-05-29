from geopy.geocoders import Nominatim
from geopy.distance import distance

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
