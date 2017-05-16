import pymongo
from application.Connections import Connection
#from application.TimeOut import timeout
from requests import head
import summary
from goose import Goose
from resource import RLIMIT_DATA, getrlimit, setrlimit
from time import gmtime, strftime, time
from urlparse import urlparse
from tldextract import extract
from Queue import Queue
from threading import Thread
import timeout_decorator

class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, *args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()

rsrc = RLIMIT_DATA
soft, hard = getrlimit(rsrc)
setrlimit(rsrc, (3*512000000, hard)) #limit to one 512mb

unwanted_links = ['ebay', 'gearbest', 'abizy']

def determine_date(date):
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000
    if date == 'yesterday':
        return str(current_milli_time - one_day)
    elif date == 'week':
        return str(current_milli_time - 7 * one_day)
    elif date == 'month':
        return str(current_milli_time - 30 * one_day)
    return '0'

def unshorten_url(url):
    return head(url, allow_redirects=True).url

@timeout_decorator.timeout(30, use_signals=False)
def linkParser(link):
    try:
        count = link['total']
        link = unshorten_url(link['_id'])
        parsed_uri = urlparse(link)
        domain = extract(link).domain
        if domain not in unwanted_links:
            source = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

            #g = Goose({'browser_user_agent': 'Mozilla', 'parser_class':'lxml'})
            #article = g.extract(url=link)
            #image = str(article.top_image.src)
            #description = str(article.meta_description)
            #title = article.title.upper()

            #s = summary.Summary(link)
            #s.extract()
            #image = str(s.image).encode('utf-8')
            #title = str(s.title.encode('utf-8'))
            #description = str(s.description.encode('utf-8'))

            if image != "None" and description != "None":
                dic = {'url': link, 'im':image, 'title': title, 'description': description, 'popularity': int(count), 'source': source}
                if not next((item for item in result if item["title"] == dic['title'] and item["im"] == dic['im']\
                 and item["description"] == dic['description']), False):
                    return dic
                return {}
    except Exception as e:
        return {}
        pass

def calculateLinks(alertid, date):
    print alertid, date
    stringDate = date
    date = determine_date(date)
    links = Connection.Instance().db[str(alertid)].aggregate([{'$match': {'timestamp_ms': {'$gte': date} }},\
                                                         {'$unwind': "$entities.urls" },\
                                                         {'$group' : {'_id' :"$entities.urls.expanded_url" , 'total':{'$sum': 1}}},\
                                                         {'$sort': {'total': -1}},\
                                                         {'$limit': 500}])

    links = list(links)
    result = []
    while len(result) < 60 and links != []:

        link = links.pop(0)
        print stringDate, len(result)
        if link['_id'] != None:
            try:
                dic = linkParser(link)
                if dic != None and dic != {}:
                    result.append(linkParser(link))
            except:
                pass

    if result != []:
        Connection.Instance().newsdB[str(alertid)].remove({'name': stringDate})
        Connection.Instance().newsdB[str(alertid)].insert_one({'name': stringDate, stringDate:result, 'date': strftime("%a, %d %b %Y %H:%M:%S", gmtime())})


def createParameters(alertid_list):
    dates = ['yesterday', 'week', 'month']
    return [[alertid[0],date] for alertid in alertid_list for date in dates]

def main():
    Connection.Instance().cur.execute("Select alertid from alerts;")
    alertid_list = sorted(list(Connection.Instance().cur.fetchall()))
    parameters = createParameters(alertid_list)

    pool = ThreadPool(3)
    pool.map(calculateLinks, parameters)
    pool.wait_completion()

if __name__ == '__main__':
    main()
