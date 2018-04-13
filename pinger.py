import threading, sys, os
from subprocess import call
import result

PingRunning = True

class Pinger(threading.Thread):

    ip = ''
    r=result.Result


    def setIP(self, ip):
        self.ip = ip

    def setResult(self,r):
        self.r=r


    def run(self):
        if self.ip == '':
            print("No IP provided")
            return False
        global PingRunning
        PingRunning=True
        success = 0
        fails = 0
        while PingRunning == True:
            for i in range(10):
                rc = call(['ping', self.ip, '-c', '1'])
                if rc == 0:
                    success = success + 1
                else:
                    fails = fails + 1
            PingRunning=False
        self.r.addPingResults(success,fails)
        return True
