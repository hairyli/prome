#coding:utf-8
#!/usr/bin/python3
import os
import queue
import threading
import abc
import daemon

class Base_push(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ping_test(self):
        pass


class Sub_push(Base_push):
    def ping_test(self):
        creatpinger(queue.Queue(100), '192.168.1.')



class Pinger(threading.Thread):


    def __init__(self, queue, pingIp, pingCoint=1):


        threading.Thread.__init__(self)

        self.queue = queue

        self.pingIp = pingIp

        self.pingCount = pingCoint


    def run(self):

        pingResult = os.popen('ping -n' + ' ' + str(self.pingCount) + ' ' + self.pingIp).read()
        print(111111)
        print(pingResult)

        if '无法访问目标主机' not in pingResult:

            print(self.pingIp, '\t is online')
            while True:
                with open('/tmp/ping.txt', 'a') as fh:
                    fh.write(self.pingIp + '\t is online')

        self.queue.get()



class creatpinger:

    def __init__(self, queue, pingIpParagraph, allcount=255, pingCount=1):


        self.queue = queue

        self.pingIpParagraph = pingIpParagraph

        self.allcount = allcount

        self.pingCount = 1

        self.create()


    def create(self):


        for i in range(1, self.allcount + 1):

            self.queue.put(i)

            Pinger(self.queue, self.pingIpParagraph + str(i), self.pingCount).start()


with daemon.DaemonContext():
    Sub_push().ping_test()






