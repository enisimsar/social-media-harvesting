#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import time
import threading
from application.Connections import Connection
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')


def get_next_tweets_sequence():
    cursor = Connection.Instance().db["counters"].find_and_modify(
            query= { '_id': "tweetDBId" },
            update= { '$inc': { 'seq': 1 } },
            new= True,
            upsert= True
    )
    return cursor['seq']

#Variables that contains the user credentials to access Twitter API
consumer_key = "" # API key
consumer_secret = "" # API secret
access_token = ""
access_token_secret = ""

#This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):

    def __init__(self,alert):
        self.terminate = False
        self.campaignId = alert['alertid']
        self.campaignName = alert['name']
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if self.terminate == False:
            #print data
            Connection.Instance().cur.execute("update alerts set threadstatus=%s where alertid = %s;", ["OK", self.campaignId])
            Connection.Instance().PostGreSQLConnect.commit()
            tweet = json.loads(data)
            tweet['tweetDBId'] = get_next_tweets_sequence()
            Connection.Instance().db[str(self.campaignId)].insert_one(tweet) #this creates tweets collection, if there is one then write on it
            return True
        else:
            return False

    def on_error(self, status):
        Connection.Instance().cur.execute("update alerts set threadstatus=%s where alertid = %s;", [str(status), self.campaignId])
        Connection.Instance().PostGreSQLConnect.commit()
        print status
        if self.terminate == True:
            return False

    def stop(self):
        self.terminate = True

class StreamCreator():
    def __init__(self,alert):
        #This handles Twitter authetification and the connection to Twitter Streaming API
        self.l = StdOutListener(alert)
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.stream = Stream(self.auth, self.l)
        self.t = threading.Thread(target = self.stream.filter, kwargs = {'track':alert['keywords'],'languages':alert['lang']} )
    def start(self):
        self.t.start()
    def terminate(self):
        self.l.terminate = True
    def checkAlive(self):
        return self.t.isAlive()
