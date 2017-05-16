from __future__ import print_function
import pymongo
import psycopg2
from application.utils.Singleton import Singleton

@Singleton
class Connection:
    MongoDBClient = None
    db = None # MongoDB
    PostGreSQLConnect = None
    cur = None # PostgreSQL

    def __init__(self):
        try:
            self.MongoDBClient = pymongo.MongoClient('') # Please enter your mongo database
            self.db = self.MongoDBClient.openMakerdB
            self.newsdB = self.MongoDBClient.newsdB
            self.feedDB = self.MongoDBClient.feedDB
            self.infDB = self.MongoDBClient.influenceRanks
            self.PostGreSQLConnect = psycopg2.connect("") # Please enter your postgresql database
            self.cur = self.PostGreSQLConnect.cursor()
            print("new connection")
        except Exception as e:
            print(e)
            print("I am unable to connect to the database")
