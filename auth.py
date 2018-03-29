#!/bin/python3

import http.client
import requests
import json

class Bazaar:
    
    username = ''
    password = ''
    cookie = ''

    def __init__(self, username, password):
        self.username = username
        self.password = password


    def auth(self):
        print("Authenticating "+self.username)
        r = requests.post("https://masterbazaar.subutai.io/rest/v1/client/login", data={'email': self.username, 'password': self.password})
        if r.status_code != 200:
            print(r.status_code, r.reason)
            return False
        else:
            print("Authenticated: ", r.cookies['SUBUTAI_HUB_SESSION'])
            self.cookie = r.cookies['SUBUTAI_HUB_SESSION']
            return True

    def peers(self):
        print("Requesting user peers")
        if self.cookie == '':
            return False

        cookies = dict(SUBUTAI_HUB_SESSION=self.cookie)

        r = requests.get("https://masterbazaar.subutai.io/rest/v1/client/peers/favorite", cookies=cookies)
        if r.status_code == 200:
            j = json.loads(r.text)
            print(j[0]['peer_id'])
        else:
            print(r.status_code, r.reason)


b = Bazaar('', '')
rc = b.auth()
if rc != True:
    print("Terminating")
    exit

b.peers()

