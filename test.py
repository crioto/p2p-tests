#!/usr/bin/python3

import http.client
import requests
import json
import time
import yaml
import pinger
import p2p
import result


class Bazaar:

    username = ''
    password = ''
    cookie = ''
    envName = ''

    def __init__(self, username, password, envName):
        self.username = username
        self.password = password
        self.envName = envName


    def auth(self):
        print("Authenticating "+self.username)
        r = requests.post("https://masterbazaar.subutai.io/rest/v1/client/login", data={'email': self.username, 'password': self.password})
        if r.status_code != 200:
            print(r.status_code, r.reason)
            print("Authentication failed")
            return False
        else:
            print("Authenticated")
            self.cookie = r.cookies['SUBUTAI_HUB_SESSION']
            return True

    def peers(self):
        print("Requesting user peers")
        self.peers = []
        if self.cookie == '':
            print("Can't retrieve peers: no cookies")
            return self.peers

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)

        r = requests.get("https://masterbazaar.subutai.io/rest/v1/client/peers/favorite", cookies=cookies)

        if r.status_code == 200:
            j = json.loads(r.text)
            for peer in j:
                self.peers.append(peer['peer_id'])

        else:
            print(r.status_code, r.reason)

        return self.peers


    def variables(self):
        print("Requesting blueprint variables")
        if self.cookie == '':
            return False

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)

        chosenPeers = []
        for peer in self.peers:
            chosenPeers.append(peer)
            if len(chosenPeers) >= 3:
                break

        r = requests.put("https://masterbazaar.subutai.io/rest/v1/client/blueprint/variables", cookies=cookies, data={'blueprint': self.readBlueprint(), 'peers': chosenPeers})
        if r.status_code == 200:
            print(r.text)
        else:
            print(r.status_code, r.reason)


    def build(self):
        print("Building blueprint")
        if self.cookie == '':
            return False

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)
        if len(self.peers)<3:
            print("You don't have enough peers. This blueprint requires 3 peers, but only 2 is available. Please add own peers or select favorites.")
            exit(15)

        chosenPeers = ""
        pc = 0
        for peer in self.peers:
            pc = pc + 1
            chosenPeers = chosenPeers + peer
            if pc < 3:
                chosenPeers = chosenPeers + ','
            else:
                break

        print(chosenPeers)

        r = requests.post("https://masterbazaar.subutai.io/rest/v1/client/blueprint/build", cookies=cookies, data={'blueprint': self.readBlueprint(), 'variables': '[]', 'peers': chosenPeers})
        if r.status_code == 200 or r.status_code == 202:
            print(r.text)
        else:
            print(r.status_code, r.reason)
            print(r.text)


    def destroy(self, name):
        print("Destroying " + name)
        envid = ''
        for env in self.envs:
            if env['environment_name'] == name:
                envid = env['environment_id']

        if envid == '':
            print("Requested environment was not found")
            return False

        if self.cookie == '':
            return False

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)
        r = requests.delete("https://masterbazaar.subutai.io/rest/v1/client/environments/"+envid, cookies=cookies)
        if r.status_code == 202:
            return True
        else:
            print(r.status_code, r.reason)
            print(r.text)
            return False


    def environments(self):
        if self.cookie == '':
            return False

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)
        r = requests.get("https://masterbazaar.subutai.io/rest/v1/client/environments", cookies=cookies)
        if r.status_code == 200:
            self.envs = json.loads(r.text)
            return True
        else:
            print(r.status_code, r.reason)
        return False


    def readBlueprint(self):
        print("Reading Subutai.json")
        file = open("Subutai.json", "r")
        return file.read()


    def isEnvExists(self, name):
        print("Checking if environment " + name + " exists")

        for env in self.envs:
            if env['environment_name'] == name:
                return True

        return False

    def wait(self):
        print("Waiting for build process to finish: 300 seconds")
        maxTime = 300
        passed = 0
        updatePeriod = 10

        while True:
            if passed > maxTime:
                print("Couldn't finish for environment to finish build for " + str(maxTime))
                return False

            time.sleep(updatePeriod)
            passed = passed + updatePeriod
            self.environments()
            for env in self.envs:
                if env['environment_name'] == self.envName:
                    if env['environment_status'] == 'UNHEALTHY':
                        print("Failed to build healthy environment")
                        return False
                    if env['environment_status'] == 'HEALTHY':
                        print("Environment has been built")
                        return True

        return False

    def hosts(self):
        ips = []
        for env in self.envs:
            for container in env['environment_containers']:
                ips.append(container['rh_ip'])

        return ips

    def getHashes(self):
        hashes = []
        for env in self.envs:
            if env['environment_name'] != self.envName:
                continue

            t = (env['environment_hash'], env['environment_key'])
            hashes.append(t)

        return hashes


    def getHash(self):
        for env in self.envs:
            if env['environment_name'] == self.envName:
                return env['environment_hash']

        return ''


envName = "p2p-integration-test"
maxDestroyWait = 300
destroyWaitPeriod = 10
try:
    with open("config.yaml", 'r') as stream:
        try:
            data = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            print("Check if config.yaml exists and it's readable")
            exit(2)
except:
    print("Check if config.yaml exists and it's readable")
    exit()

if data['email'] == '' or data['password'] == '':
    print("Wrong data has been provided in config ")
    exit(3)

b = Bazaar(data['email'], data['password'], envName)
rc = b.auth()
if rc != True:
    print("Terminating")
    exit()

if b.environments() != True:
    print("Failed to get environments")
    exit(4)

destroyInProgress = False
if b.isEnvExists(envName) == True:
    print("Environment already exists. Destroying it")
    rc = b.destroy(envName)
    if rc != True:
        print("Failed to destroy environment")
        exit(5)
    else:
        print("Destroy process has been started")
        destroyInProgress = True

if destroyInProgress == True:
    attempts = 0
    while destroyInProgress == True:
        time.sleep(destroyWaitPeriod)
        b.environments()
        if b.isEnvExists(envName) == True:
            attempts = attempts + 1
        else:
            print("Environment was destroyed")
            destroyInProgress = False
        if attempts > maxDestroyWait / destroyWaitPeriod:
            print("Destroy failed after " + maxDestroyWait + " seconds timeout")
            exit(6)

allPeers = b.peers()
b.variables()
b.build()
rc = b.wait()
if rc != True:
    exit(10)

print("Build completed")

code=p2p.Check()
if code!=0:
    print("Test is stopped. Check if p2p is installed")
    exit(17)

hosts = b.hosts()
daemon = p2p.Daemon()
daemon.start()

time.sleep(10)
hashes = b.getHashes()
for h in hashes:
    rc = p2p.StartP2P(h[0], h[1])
    if rc != 0:
        print("Failed to start P2P instance. Stopping test")
        p2p.DaemonRunning = False
        daemon.kill()

started = time.time()

time.sleep(5)
p2p.CheckP2P(b.getHash(), hosts)

print("\nWaiting 60 seconds\n\n")
#Wait 60 seconds while containers status become READY
time.sleep(60)

print("Start to pinging\n")
p=pinger.Pinger()
for i in hosts:
    r=result.Result(i)
    p.setResult(r)
    p.setIP(i)
    b=p.run()
    if b==True:
        print("PING for",i,"is done")
        print('\n')
    print("\nRESULTS of",i,":\n")
    p.r.produce()
    print('\n')

print("End")
exit(0)
