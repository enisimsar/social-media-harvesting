from track import StreamCreator
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class AddTrack():
    def __init__(self):
        self.threadDic = {}

    # Starts all alerts 
    def setup(self,alertList):
        for alert in alertList :
            if str(alert['alertid']) not in self.threadDic:
                self.threadDic[str(alert['alertid'])] = StreamCreator(alert)
                self.threadDic[str(alert['alertid'])].start()

    # Kills all alerts
    def killAllThreads(self):
        for alert in self.threadDic:
            self.threadDic[alert].terminate()

    def getThreadDic(self):
        return self.threadDic

    def setThreadDic(self, newDic):
        self.threadDic = newDic

    # Creates the thread and puts it into threadDic
    def addThread(self, alert):
        self.threadDic[str(alert['alertid'])] = StreamCreator(alert)
        self.threadDic[str(alert['alertid'])].start()

    # Terminates the thread and deletes it into threadDic
    def killThread(self, alert):
        self.threadDic[str(alert['alertid'])].terminate()
        del self.threadDic[str(alert['alertid'])] 

    def __getitem__(self):
        return (self.threadDic)
