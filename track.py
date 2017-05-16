
#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import time
import threading
from application.Connections import Connection
import json
import re
from bson.objectid import ObjectId

def get_keywords(alertDic):
    keywords = []
    for key in alertDic:
        alert = alertDic[key]
        keywords = keywords + alert['keywords']
    keywords = list(set(keywords))
    print keywords
    return keywords

def get_lang(alertDic):
    lang = []
    for key in alertDic:
        alert = alertDic[key]
        lang = lang + alert['lang']
    lang = list(set(lang))
    return lang

def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
            query= { '_id': "tweetDBId" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

def separates_tweet(alertDic, tweet):
    for key in alertDic:
        alert = alertDic[key]
        try:
            if tweet['lang'] in alert['lang']:
                for keyword in alert['keywords']:
                    keyword = re.compile(keyword.replace(" ", "(.?)"), re.IGNORECASE)
                    if 'extended_tweet' in tweet and 'full_text' in tweet['extended_tweet']:
                        if re.search(keyword, str(tweet['extended_tweet']['full_text'].decode('utf-8'))):
                            tweet['_id'] = ObjectId()
                            Connection.Instance().db[str(alert['alertid'])].insert_one(tweet)
                            break
                    else:
                        if re.search(keyword, str(tweet['text'].decode('utf-8'))):
                            tweet['_id'] = ObjectId()
                            Connection.Instance().db[str(alert['alertid'])].insert_one(tweet)
                            break
        except KeyError:
            pass

# Accessing Twitter API
consumer_key = "" # API key
consumer_secret = "" # API secret
access_token = ""
access_secret = ""

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def __init__(self,alertDic):
        self.alertDic = alertDic
        self.terminate = False
        self.connection = True
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence()
            separates_tweet(self.alertDic, tweet)
            tweet['_id'] = ObjectId()
            Connection.Instance().db["all"].insert_one(tweet)
            self.connection = True
            return True
        else:
            return False

    def on_disconnect(self, notice):
        print ("Disconnect: {}".format(notice))
        self.connection = False
        return True

    def on_error(self, status):
        print status
        if status == 420:
            return False

    def stop(self):
        self.terminate = True

    def on_timeout(self):
        print('Timeout...')
        return True # To continue listening

class StreamCreator():
    def __init__(self,alertDic):
        #This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(alertDic)
        self.keywords = get_keywords(alertDic= alertDic)
        self.lang = get_lang(alertDic= alertDic)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target = self.stream.filter, kwargs = {'track':self.keywords, 'languages':self.lang} )
    def start(self):
        self.t.deamon = True
        self.t.start()
    def terminate(self):
        self.l.running = False
        self.l.stop()
        self.l.terminate = True
    def checkAlive(self):
        return self.t.isAlive()
    def checkConnection(self):
        if self.l is not None:
            return self.l.connection
        else:
            return False
