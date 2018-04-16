import time

class Result:

    ip = ''
    started = 0
    firstConnected = 0
    success = 0
    fails = 0

    def __init__(self, ip):
        self.ip = ip
        self.started = time.asctime(time.localtime(time.time()))
        return


    def indicateConnected(self):
        if firstConnected == 0:
            firstConnected = time.asctime(time.localtime(time.time()))

        return


    def addPingResults(self, success, fails):
        self.success = success
        self.fails = fails


    def produce(self):
        print("Peer " + self.ip)
        print("Started connection at " + str(self.started))
        print("First connected at " + str(self.firstConnected))
        print("Ping results: ")
        print("\tSucceed: " + str(self.success))
        print("\tFailed: " + str(self.fails))
