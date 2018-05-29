import tweepy

from config import twitter_config


def connect_to_twitter_api(config):
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])

    # Return Twitter API (by Tweepy)
    return tweepy.API(auth)


def get_twitter_home_address(username):
    home_address = None

    # Connect to Twitter API
    api = connect_to_twitter_api(twitter_config)

    # Check for Twitter account
    try:
        twitter_user = api.get_user(username)

        # If Twitter account exists,
        # get home_address if it's available
        if twitter_user.location is not None:
            home_address = twitter_user.location
    except Exception as e:
        # print(e)
        pass

    return home_address
