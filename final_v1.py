#coding:utf-8
#!/usr/bin/python3
import os
import abc
import logging
import sys
import yaml
import daemon
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
    def gather(self):
        raise NotImplementedError

    @abc.abstractmethod
    def processing(self):
        raise NotImplementedError


class Ping_push(Base_push):

    def __init__(self):

        self.filename = os.path.join(os.path.dirname(__file__), 'pingconf.yml').replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.ips = self.y['pingip']['ip']
        self.targets = self.y['pushgateway']['targets'][0]
        self.type = self.y['pushgateway']['type'][0]
        self.processing()

    def gather(self, ip):

        try:
            str_num = os.popen(
                'ping -c1' + ' ' + ip + '>/dev/null 2>&1;echo $?').read()
            return_num = int(str_num)
            timestamp = time.time()
            if return_num == 0:
                pingResult = os.popen('ping -c1' + ' ' + ip).read()
                res_time = re.findall(r'.*time=(\d\.?\d*) ms*', pingResult)
                if len(res_time):
                    response_time = float(res_time[0])
                status = "ok"

            if return_num == 1:
                status = "not ok"
                response_time = 0
            return ip, status, timestamp, response_time
        except Exception as e:
            logging.error(e)

    def processing(self):
        self.registry = CollectorRegistry()
        self.g = Gauge(self.type, '状态-时间', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)

        for ip in self.ips:
            ip, status, timestamp, response_time = self.gather(ip)
            self.g.labels(ip, status, timestamp, response_time)
        try:

            pushadd_to_gateway(self.targets, job='pingIP_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))


class Requests_push(Base_push):

    def __init__(self):

        self.filename = os.path.join(os.path.dirname(__file__), 'pingconf.yml').replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.ip_ports = self.y['webping']['ip_ports']
        self.targets = self.y['pushgateway']['targets'][0]
        self.type = self.y['pushgateway']['type'][1]
        self.processing()

    def gather(self, ip_port):
        timestamp = time.time()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) \
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        }

        try:
            response = requests.get(ip_port, headers=headers)
            if response.status_code == 200:
                status = "ok"
                response_time = response.elapsed.microseconds / 1000
                print(response.elapsed.microseconds)
            else:
                status = "not ok"
                response_time = 0
            return ip_port, status, timestamp, response_time
        except Exception as e:
            logging.error(str(e))

    def processing(self):
        self.registry = CollectorRegistry()
        self.g = Gauge(self.type, 'ip_status', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)

        for ip_port in self.ip_ports:
            ip, status, timestamp, response_time = self.gather(ip_port)
            self.g.labels(ip, status, timestamp, response_time)
        try:

            pushadd_to_gateway(self.targets, job='pingIP_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))


if __name__ == '__main__':

    type = sys.argv[1]
    if type == "ping":
        Ping_push()
    elif type == "webping":
        Requests_push()
    else:
        # todo
        pass









