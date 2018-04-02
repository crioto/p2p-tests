import threading, sys, os
from subprocess import call

PingRunning = True

class Pinger(threading.Thread):
    
    ip = ''


    def setIP(self, ip):
        self.ip = ip


    def run(self):
        if self.ip == '':
            print("No IP provided")
            return False
        global PingRunning
        success = 0
        fails = 0
        while PingRunning == True:
            rc = call('ping', self.ip, '-c', '1')
            if rc == 0:
                success = success + 1
            else:
                fails = fails + 1

        print("Results for " + self.ip)
        print("Success: " + success)
        print("Fails: " + fails)
        os._exit(1)
        return True