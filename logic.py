import re
import search
import pymongo
from application.Connections import Connection
from time import gmtime, strftime, strptime
import json

def getThemes():
    names = Connection.Instance().feedDB.collection_names()
    result = {}
    themes = [{'name': name} for name in names]
    result['themes'] = themes
    return json.dumps(result, indent=4)

def getInfluencers(themename, cursor):
    length = len(list(Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0})))
    if cursor is None:
        influencers = Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0}).skip(0).limit(20)
        cursor = 0
    else:
        influencers = Connection.Instance().infDB[str(themename)].find({"type": "filteredUser"}, {"_id":0, "type": 0}).skip(int(cursor)).limit(20)
    result = {}
    influencers = list(influencers)
    if len(influencers) == 0:
        influencers.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next cursor'] = cursor
    result['cursor length'] = length
    result['influencers'] = influencers
    return json.dumps(result, indent=4)

def getFeeds(themename, cursor=0):
    length = len(list(Connection.Instance().feedDB[str(themename)].find({}, {"_id":0})))
    if cursor is None:
        feeds = Connection.Instance().feedDB[str(themename)].find({}, {"_id":0}).skip(0).limit(20)
        cursor = 0
    else:
        feeds = Connection.Instance().feedDB[str(themename)].find({}, {"_id":0}).skip(int(cursor)).limit(20)
    result = {}
    feeds = list(feeds)
    if len(feeds) == 0:
        feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next cursor'] = cursor
    result['cursor length'] = length
    result['feeds'] = feeds
    return json.dumps(result, indent=4)

def getAlertLimit(userid):
    Connection.Instance().cur.execute("select alertlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    return fetched[0][0]

def getUserInfo(username):
    Connection.Instance().cur.execute("select * from users where username = %s", [username])
    fetched = Connection.Instance().cur.fetchall()
    return {'userid': fetched[0][0], 'password': fetched[0][2]}

def getAllRunningAlertList():
    Connection.Instance().cur.execute("Select * from alerts where isrunning = %s;", [True])
    var = Connection.Instance().cur.fetchall()
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), 'lang': i[5].split(",")} for i in var]
    return alerts

def getAllAlertList():
    Connection.Instance().cur.execute("Select * from alerts;")
    var = Connection.Instance().cur.fetchall()
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), \
               'lang': i[5].split(","), 'status': i[6], 'creationTime': i[7]} for i in var]
    alerts = sorted(alerts, key=lambda k: k['alertid'])
    return alerts

def getThreadStatus(mainT):
    return mainT.checkThread()

def getThreadConnection(mainT):
    return mainT.checkConnection()

def getAlertName(alertid):
    Connection.Instance().cur.execute("Select alertname from alerts where alertid = %s;", [alertid])
    return Connection.Instance().cur.fetchall()[0][0]

def getAlertId(alertname):
    Connection.Instance().cur.execute("Select alertid from alerts where alertname = %s;", [alertname])
    return Connection.Instance().cur.fetchall()[0][0]

def getAlertIdwithUserId(alertname, userid):
    Connection.Instance().cur.execute("Select alertid from alerts where alertname = %s and userid = %s;", [alertname, userid])
    return Connection.Instance().cur.fetchall()[0][0]

# Gives alerts as lists
def getAlertList(userid):
    Connection.Instance().cur.execute("Select * from alerts where userid = %s;", [userid])
    var = Connection.Instance().cur.fetchall()
    alerts = [{'alertid':i[0], 'name':i[2], 'keywords':i[3].split(","), 'lang': i[5].split(","),\
               'status': i[6], 'creationTime': i[7]} for i in var]
    alerts = sorted(alerts, key=lambda k: k['alertid'])
    for alert in alerts:
        alert['tweetCount'] = Connection.Instance().db[str(alert['alertid'])].find().count()
    return alerts

def alertExist(alertid):
    Connection.Instance().cur.execute("Select userid from alerts where alertid = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    if var != None:
        return True
    else:
        return False

def checkUserIdAlertId(userid, alertid):
    Connection.Instance().cur.execute("Select userid from alerts where alertid = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    if var != None and len(var) != 0:
        return int(var[0]) == int(userid)
    else:
        return False

# Take alertid and return that alert as not lists
def getAlert(alertid):
    if alertid != None:
        Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
        var = Connection.Instance().cur.fetchone()
        alert = {'alertid': var[0], 'name':var[2], 'keywords':var[3], 'lang': var[5].split(","), 'status': var[6], 'keywordlimit': var[8],\
                 'description': var[9]}
    else:
        alert = {'alertid': "", 'name': "", 'keywords': "", 'lang': "", 'status': False, 'keywordlimit': 10, 'description': ""}
    return alert

# Take alertid and return that alert as not lists
def getAlertAllOfThemList(alertid):
    Connection.Instance().cur.execute("Select * from alerts where alertid = %s;", [alertid])
    var = Connection.Instance().cur.fetchone()
    alert = {'alertid':var[0], 'name':var[2], 'keywords':var[3].split(","), 'lang': var[5].split(","), 'status': var[6]}
    return alert

# Give nextalertid
def getNextAlertId():
    Connection.Instance().cur.execute("select alertid from alerts order by alertid desc limit 1;")
    rows = Connection.Instance().cur.fetchall()
    if(len(rows) == 0):
        return 0
    else:
        for temp in rows:
            return temp[0]+1

def setUserAlertLimit(userid, setType):
    Connection.Instance().cur.execute("select alertlimit from users where userid = %s", [userid])
    fetched = Connection.Instance().cur.fetchall()
    if setType == 'decrement':
        newLimit = fetched[0][0] - 1
    elif setType == 'increment':
        newLimit = fetched[0][0] + 1
    Connection.Instance().cur.execute("update users set alertlimit = %s where userid = %s", [newLimit, userid])
    Connection.Instance().PostGreSQLConnect.commit()

# Take alert information, give an id and add it DB
def addAlert(alert, mainT, userid):
    alert['alertid'] = getNextAlertId()
    now = strftime("%Y-%m-%d", gmtime())
    Connection.Instance().cur.execute("INSERT INTO alerts (alertid, userid, alertname, keywords, languages, creationtime, keywordlimit, isrunning, description) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);", [alert['alertid'], userid, alert['name'], alert['keywords'], alert['lang'], now, alert['keywordlimit'], True, alert['description']])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])
    setUserAlertLimit(userid, 'decrement')
    mainT.addAlert(alert)

# Deletes alert and terminate its thread
def deleteAlert(alertid, mainT, userid):
    alert = getAlertAllOfThemList(alertid)
    setUserAlertLimit(userid, 'increment')
    mainT.delAlert(alert)
    Connection.Instance().db[str(alertid)].drop()
    Connection.Instance().cur.execute("delete from alerts where alertid = %s;", [alertid])
    Connection.Instance().PostGreSQLConnect.commit()

# Updates given alert information and kill its thread, then again start its thread.
def updateAlert(alert, mainT, userid):
    Connection.Instance().cur.execute("update alerts set userid = %s, keywords = %s , languages = %s, isrunning = %s, description = %s where alertid = %s;", [userid, alert['keywords'], alert['lang'], True, alert['description'], alert['alertid']])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alert['alertid'])
    mainT.updateAlert(alert)

# Starts alert streaming.
def startAlert(alertid, mainT):
    alert = getAlertAllOfThemList(alertid)
    Connection.Instance().cur.execute("update alerts set isrunning = %s where alertid = %s;", [True, alert['alertid']])
    Connection.Instance().PostGreSQLConnect.commit()
    mainT.addAlert(alert)

# Stops alert streaming.
def stopAlert(alertid, mainT):
    Connection.Instance().cur.execute("update alerts set isrunning = %s where alertid = %s;", [False, alertid])
    Connection.Instance().PostGreSQLConnect.commit()
    alert = getAlertAllOfThemList(alertid)
    mainT.delAlert(alert)

def getTweets(alertid):
    tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "id":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId' , pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        tweet['created_at'] = strftime('%B %d, %Y', strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a target="_blank" href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
    return tweets

# Runs we scroll the page
def getSkipTweets(alertid, lastTweetId):
    tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$lt': int(lastTweetId)}}, {'tweetDBId': 1, "text":1, "id":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)]).limit(25)
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        tweet['created_at'] = strftime('%B %d, %Y', strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a target="_blank" href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
    return tweets

# Checks periodically new tweets
def checkTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "id":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    return len(tweets)

# Gets newest tweets and returns them
def getNewTweets(alertid, newestId):
    if int(newestId) == -1:
        tweets = Connection.Instance().db[str(alertid)].find({}, {'tweetDBId': 1, "text":1, "id":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    else:
        tweets = Connection.Instance().db[str(alertid)].find({'tweetDBId': {'$gt': int(newestId)}}, {'tweetDBId': 1, 'id': 1, "text":1, "user":1, 'created_at': 1, "_id":0}).sort([('tweetDBId', pymongo.DESCENDING)])
    tweets = list(tweets)
    alert_keywords = getAlertAllOfThemList(alertid)['keywords']
    for tweet in tweets:
        tweet['created_at'] = strftime('%B %d, %Y', strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
        for keyword in alert_keywords:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a target="_blank" href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
    return tweets

# Return preview alert search tweets
def searchTweets(keywords, languages):
    """
    This is for the phares.
    """
    keys = keywords.split(",")
    result_keys = []
    for key in keys:
        if " " in key:
            result_keys.append("\""+key+"\"")
        else:
            result_keys.append(key)
    # ends
    keywords = " OR ".join(result_keys)
    languages = " OR ".join(languages.split(","))
    tweets = search.getTweets(keywords, languages)
    for tweet in tweets:
        for keyword in keys:
            marked = "<mark>" + keyword + "</mark>"
            keyword = re.compile(re.escape(keyword), re.IGNORECASE)
            tweet['text'] = keyword.sub(marked, tweet['text'])
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet['text'])
        if len(urls) != 0:
            for url in urls:
                ahref = '<a target="_blank" href="' + url + '">' + url + '</a>'
                url = re.compile(re.escape(url), re.IGNORECASE)
                tweet['text'] = url.sub(ahref, tweet['text'])
    return tweets

def getNews(alertid, date, cursor):
    dates=['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    feeds = list(Connection.Instance().newsdB[str(alertid)].find({'name': date}, {date: 1}))
    feeds = list(feeds[0][date][cursor:cursor+20])
    cursor = int(cursor) + 20
    if cursor >= 60:
        cursor = 60
    result['next_cursor'] = cursor
    result['cursor_length'] = 60
    result['feeds'] = feeds
    return result
