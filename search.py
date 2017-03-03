import tweepy
import json
from tweepy import OAuthHandler
import sys
reload(sys)
sys.setdefaultencoding('utf8')


# Accessing Twitter API
consumer_key = "" # API key
consumer_secret = "" # API secret
access_token = ""
access_secret = ""

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

def getTweets(keywords, languages):
    tweets = []
    data = tweepy.Cursor(api.search, q= keywords, lang= languages).items(25)
    for tweet in data:
        tweets.append(tweet._json)
    return tweets
