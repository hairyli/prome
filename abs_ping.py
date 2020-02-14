#coding:utf-8
#!/usr/bin/python3
import os
import queue
import abc
import logging
import yaml
import daemon
import threading

logging.basicConfig(
    filename='log.log',
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:%(message)s'
)


class Base_push(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ping_test(self):
        pass


class Sub_push(Base_push):
    def ping_test(self):
        creatpinger(queue.Queue())



class Pinger(threading.Thread):

    def __init__(self, queue, pingIp, pingCoint=1):

        threading.Thread.__init__(self)

        self.queue = queue

        self.pingIp = pingIp

        self.pingCount = pingCoint


    def run(self):

        try:

            pingResult = os.popen('ping -n' + ' ' + str(self.pingCount) + ' ' + self.pingIp).read()

            if '无法访问目标主机' not in pingResult:

                print(self.pingIp, '\t is online')
                while True:
                    with open('/tmp/ping.txt', 'a') as fh:
                        fh.write(self.pingIp + '\t is online')
            else:
                with open('/tmp/ping_not.txt', 'a') as fh:
                    fh.write(self.pingIp + '\t is not online')


            self.queue.get()
        except Exception as e:
            logging.error(e)



class creatpinger:

    def __init__(self, queue,  pingCount=1):

        self.filename = os.path.join(os.path.dirname(__file__), 'pingconf.yml').replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.start_ip = self.y['ip']['start_ip']
        self.allcount = self.y['ip']['allcount']
        self.queue = queue
        self.pingCount = pingCount

        self.create()


    def create(self):


        for i in range(1, self.allcount + 1):

            self.queue.put(i)

            Pinger(self.queue, self.start_ip + str(i), self.pingCount).start()


with daemon.DaemonContext():
    Sub_push().ping_test()






