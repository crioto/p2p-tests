import threading, sys, os
from subprocess import call
from subprocess import Popen, PIPE

DaemonRunning = True

class Daemon(threading.Thread):


    def run(self):
        p = Popen(['p2p', 'daemon'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p.communicate(b"")


    def kill(self):
        call(['killall', '-9', 'p2p'])

def check():
    try:
        process = subprocess.Popen('p2p')
        code = process.wait()
    except:
        code=111
    return code

def StartP2P(ehash, ekey):
    return call(['p2p', 'start', '--hash', ehash, '--key', ekey])

def CheckP2P(ehash, ip):
    p = Popen(['p2p', 'status'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"")
    rc = p.returncode
    for line in output.splitlines():
        for i in ip:
            sline = str(line)
            if sline.find(i) > 0 and sline.find("Connected") > 0:
                return True
    return False
