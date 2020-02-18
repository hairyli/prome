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
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, pushadd_to_gateway
import re

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

    def __init__(self, queue, pingIp, registry, g,  pingCoint=1):

        threading.Thread.__init__(self)
        self.queue = queue
        self.pingIp = pingIp
        self.registry = registry
        self.pingCount = pingCoint
        self.g=g
        self.ping_ip()

    def ping_ip(self):

        try:
            str_num = os.popen('ping -c' + ' ' + str(self.pingCount) + ' ' + self.pingIp + '>/dev/null 2>&1;echo $?').read()
            return_num = int(str_num)
            ip = self.pingIp
            timestamp = time.time()
            if return_num == 0:
                pingResult = os.popen('ping -c' + ' ' + str(self.pingCount) + ' ' + self.pingIp).read()
                res_time = re.findall(r'.*time=(\d\.?\d*) ms*', pingResult)
                if len(res_time):
                    response_time = float(res_time[0])
                status = "ok"

            if return_num == 1:
                status = "not ok"
                response_time = 0
            self.g.labels(ip,status, timestamp, response_time)
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
        self.registry = CollectorRegistry()
        self.create()


    def create(self):

        self.g = Gauge('ping', '状态-响应时间', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)
        for i in range(1, self.allcount + 1):

            self.queue.put(i)
            Pinger(self.queue, self.start_ip + str(i), self.registry, self.g,  self.pingCount).start()

        try:

            pushadd_to_gateway('localhost:9091', job='pingIP_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))


with daemon.DaemonContext():
    Sub_push().ping_test()







