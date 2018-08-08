import requests


def get_concept(params):
    return requests.get('http://api.conceptnet.io/c/{}/{}?rel={}&limit={}'.format(
        params['language'],
        params['concept'],
        params['relation'],
        params['limit']
    )).json()


def get_related_concepts(concept):
    related_concepts = []

    for edge in concept['edges']:
        relation = edge['rel']['label']

        # if (relation == ('IsA' or 'RelatedTo')) and (end['language'] == 'en'):
        if relation == 'RelatedTo':
            related_concept = {
                'relation': relation,
                'concept': edge['end']['label']
            }

            if related_concept not in related_concepts:
                related_concepts.append(related_concept)

    return related_concepts


def main():
    params = {
        'language': 'en',
        'concept': 'cheese',
        'relation': '/r/RelatedTo',
        'limit': '1000'
    }

    concept = get_concept(params)
    related_concepts = get_related_concepts(concept)

    for concept in related_concepts:
        print(concept['relation'], ' > ', concept['concept'])


if __name__ == "__main__":
    main()

