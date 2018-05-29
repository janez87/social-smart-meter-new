#!/usr/bin/env python

import tweepy
import json
from pymongo import MongoClient


class StreamListener(tweepy.StreamListener):

    def on_connect(self):
        # Called when the connection is made
        print("You're connected to the streaming server.")

    def on_error(self, status_code):
        # This is called when an error occurs
        print('Error: ' + repr(status_code))
        return False    # break stream off

    def on_data(self, data):
        # This will be called each time we receive stream data
        client = MongoClient('localhost', 27017)

        # Use thesis database
        db = client.thesis

        # Decode JSON
        datajson = json.loads(data)

        # We only want to store tweets in Dutch
        if "lang" in datajson and datajson["lang"] == "nl":
            # Store tweet info into the tweets collection.
            db.twitter_users.insert(datajson)

    # def on_status(self, status):
    #     try:
    #         print self.status_wrapper.fill(status.text)
    #         print '\n %s  %s  via %s\n' % (status.author.screen_name, status.created_at, status.source)
    #     except:
    #         # Catch any unicode errors while printing to console
    #         # and just ignore them to avoid breaking application.
    #         pass

    def on_timeout(self):
        print('Snoozing Zzzzzz')


def main():
    # Prompt for login credentials and setup stream object
    consumer_key = 'huvgmNpGMk7sqGzXgojrbmUbE'
    consumer_secret = '49ObbSKkfltqkahcxoGKwvV32y0UCgCInY1eek19Iv8cK9YFyP'
    access_token = '790524240307089408-QP6v1qDgeyxO9mctVUJHbrL22XoiomT'
    access_token_secret = 'kKGis1U13kaQKAfHJ7kaS4VG279Xt536pQSUjvcg6RVJZ'

    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    stream = tweepy.Stream(auth, StreamListener(), timeout=None)

    # Prompt for mode of streaming
    valid_modes = ['sample', 'filter']
    while True:
        mode = raw_input('Mode? [sample/filter] ')
        if mode in valid_modes:
            break
        print('Invalid mode! Try again.')

    if mode == 'sample':
        stream.sample()

    if mode == 'filter':
        track_list = raw_input('Keywords to track (comma seperated): ').strip()

        # http://boundingbox.klokantech.com/
        bounding_box = [4.73, 52.29, 4.98, 52.42]   # Amsterdam

        if track_list:
            track_list = [k for k in track_list.split(',')]
        else:
            track_list = None

        stream.filter(locations=bounding_box, track=track_list)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nGoodbye!')