import pymongo
import psycopg2
from utils.Singleton import Singleton

@Singleton
class Connection:
    MongoDBClient = None
    db = None # MongoDB
    PostGreSQLConnect = None
    cur = None # PostgreSQL

    def __init__(self):
        try:
            # Mongo Auth 
            self.MongoDBClient = pymongo.MongoClient('')
            self.db = self.MongoDBClient.openMakerdB
            # PostGreSQL Auth
            self.PostGreSQLConnect = psycopg2.connect("")
            self.cur = self.PostGreSQLConnect.cursor()
            print "new connection"
        except Exception as e:
            print e
            print "I am unable to connect to the database"
