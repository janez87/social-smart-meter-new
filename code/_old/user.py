def get_home_town(user_profile):
    home_town = None

    # Find corresponding user profile on Twitter or Google

    # Retrieve home town

    return home_town


def get_previous_place(user_profile):
    return None


def get_previous_coordinates(user_profile):
    return None


def get_previous_city_from_place(place):
    return None


def get_previous_city_from_coordinates(coordinates):
    return None


def get_previous_city(user_profile):
    # if place:
    #     return get_previous_city_from_place(place)
    # elseif coordinates:
    #     return get_previous_city_from_coordinates(coordinates)

    return None


# TODO: Make this function more generic (query_on_attribute instead of query_on_username)
def query_on_username(query, collection):
    documents = collection.find({'data.username': query})

    posts = []

    for document in documents:
        data = document['data']
        for post in data:
            if post['username'] == query:
                posts.append(post)

    return posts
