# external modules
from nltk.corpus import wordnet as wn, stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import sent_tokenize, word_tokenize, TweetTokenizer
from nltk.wsd import lesk


def get_tokens(message):
    tokens = []

    words = preprocess_text(message)

    for word in words:
        tokens.append({
            'word': word,
            'sense': word_sense_disambiguation(message, word)
        })

    return tokens


def preprocess_text(message):
    # Tokenization
    tokens = word_tokenize(message)

    # Stopword removal
    filtered_tokens = []

    stop_words = set(stopwords.words('english'))
    stop_words.add('#')
    stop_words.add('@')
    stop_words.add('?')
    stop_words.add('!')
    stop_words.add('"')
    stop_words.add("(")
    stop_words.add(")")
    stop_words.add(",")
    stop_words.add(".")
    stop_words.add(":")

    # Initialize stemmer
    # stemmer = SnowballStemmer("english")

    # Initialize lemmatizer
    lemmatizer = WordNetLemmatizer()

    for token in tokens:
        if token not in stop_words:
            filtered_tokens.append(lemmatizer.lemmatize(token))

    return filtered_tokens


# TODO: Only use this method for the words that are in one of our dictionaries
def word_sense_disambiguation(message, word):
    if message and word:
        sense = lesk(message, word)

        if sense:
            definition = sense.definition()

            return definition
    else:
        return None
