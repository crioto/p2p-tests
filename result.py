import time

class Result:
    
    ip = ''
    started = 0
    firstConnected = 0
    success = 0
    fails = 0

    def __init__(self, ip):
        self.ip = ip
        self.started = time.time()
        return

    
    def indicateConnected(self):
        if firstConnected == 0:
            firstConnected = time.time()

        return

    
    def addPingResults(self, success, fails):
        self.success = success
        self.fails = fails


    def produce(self):
        print("Peer " + self.ip)
        print("Started connection at " + self.started)
        print("First connected at " + self.firstConnected)
        print("Ping results: ")
        print("\tSucceed: " + self.success)
        print("\tFailed: " + self.fails)