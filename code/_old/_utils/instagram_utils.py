import json
from requests import get, Session, adapters


def get_instagram_response(params):
    session = Session()
    session.mount("https://", adapters.HTTPAdapter(max_retries=10))
    response = session.get("https://api.instagram.com/v1/media/search", params=params, verify=True)
    return response.json()


def store_instagram_data(response, db):
    # Decode the JSON data
    dump = json.dumps(response)
    data = json.loads(dump)

    # Insert the data into database and return ObjectId
    return db.input_instagram.insert(data)


def collect_instagram_data(params, db):
    response = get_instagram_response(params)
    object_id = store_instagram_data(response, db)

    return object_id
