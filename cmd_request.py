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
import requests

logging.basicConfig(
    filename='log.log',
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:%(message)s'
)


class Base_push(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ping_test(self):
        pass

    @abc.abstractmethod
    def requests_test(self):
        pass


class Sub_push(Base_push):
    def ping_test(self):
        creatpinger(queue.Queue())

    def requests_test(self):
        pass


class Requests_push(Base_push):

    def ping_test(self):
        pass

    def requests_test(self):
        Requests_Response()



class Requests_Response():

    def __init__(self):

        self.registry = CollectorRegistry()
        self.push_gate()

    def get_response(self, url):
        timestamp = time.time()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                status = "ok"
                response_time = response.elapsed.microseconds/1000
                print(response.elapsed.microseconds)
            else:
                status = "not ok"
                response_time = 0
            self.g.labels(url, status, timestamp, response_time)
        except Exception as e:
            logging.error(str(e))

    def push_gate(self):

        self.g = Gauge('request_test', '状态-时间', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)
        urls = ['https://www.baidu.com/', 'http://www.sina.com.cn/']

        for url in urls:
            self.get_response(url)
        try:

            pushadd_to_gateway('localhost:9091', job='request_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))


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

if __name__ == '__main__':

    Requests_push().requests_test()
    Sub_push().ping_test()









