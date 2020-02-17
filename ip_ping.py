#coding:utf-8
#!/usr/bin/python3
import os
import queue
import abc
import logging
import yaml
import daemon
import threading
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


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
            start_time = time.time()
            ip = self.pingIp
            timestamp = time.time()
            response_time = timestamp - start_time

            if '无法访问目标主机' not in pingResult:
                status = "ok"
            else:
                status = "not ok"
                # todo
            registry = CollectorRegistry()
            g = Gauge('ping', '状态-响应时间',['ip','status', 'timestamp', 'response_time'], registry=registry)
            g.labels(ip,status, timestamp, response_time)
            push_to_gateway('localhost:9091', job='pingIP_status', registry=registry)

            # todo  这里push_to_gateway 不通的话，写入文件，我看了很多博客，不知道咋写，还有pushgateway 通不通怎么判断，推送255个ip他只返回最后一个
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







