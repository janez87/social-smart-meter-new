# https://pythonprogramming.net/using-bio-tags-create-named-entity-lists/

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


def train_ner_model():
    # TODO
    return None


def get_tokens(text):
    tokens = []

    stop_words = set(stopwords.words('english'))
    stop_words.add('#')
    stop_words.add('@')
    stop_words.add('?')
    stop_words.add('!')

    sentences = sent_tokenize(text)
    for sentence in sentences:
        word_tokens = word_tokenize(sentence)

        filtered_sentence = []

        for w in word_tokens:
            if w not in stop_words:
                filtered_sentence.append(w)
                tokens.append(w)

        # print(filtered_sentence)

    return tokens
