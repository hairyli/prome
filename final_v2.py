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
import aiohttp
import asyncio
from argparse import ArgumentParser



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

        self.filename = os.path.join(os.path.dirname(__file__), args.filename).replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.ips = self.y['pingip']['ip']
        self.targets = self.y['pushgateway']['targets'][0]
        self.type = self.y['pushgateway']['type'][0]
        self.processing()

    async def gather(self, ip):

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
            return await ip, status, timestamp, response_time
        except Exception as e:
            logging.error(e)

    async def processing(self):
        self.registry = CollectorRegistry()
        self.g = Gauge(self.type, '状态-时间', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)

        for ip in self.ips:
            ip, status, timestamp, response_time = await  self.gather(ip)
            self.g.labels(ip, status, timestamp, response_time)
        try:

            pushadd_to_gateway(self.targets, job='pingIP_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))


class Requests_push(Base_push):

    def __init__(self):

        self.filename = os.path.join(os.path.dirname(__file__), args.filename).replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.ip_ports = self.y['webping']['ip_ports']
        self.targets = self.y['pushgateway']['targets'][0]
        self.type = self.y['pushgateway']['type'][1]
        self.processing()

    async def gather(self, ip_port):
        timestamp = time.time()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) \
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ip_port, headers=headers) as response:
                    if response.status_code == 200:
                        status = "ok"
                        response_time = response.elapsed.microseconds / 1000
                        print(response.elapsed.microseconds)
                    else:
                        status = "not ok"
                        response_time = 0
                    return await ip_port, status, timestamp, response_time
        except Exception as e:
            logging.error(str(e))

    async def processing(self):
        self.registry = CollectorRegistry()
        self.g = Gauge(self.type, 'ip_status', ['ip', 'status', 'timestamp', 'response_time'], registry=self.registry)

        for ip_port in self.ip_ports:
            ip, status, timestamp, response_time = await self.gather(ip_port)
            self.g.labels(ip, status, timestamp, response_time)
        try:

            pushadd_to_gateway(self.targets, job='pingIP_status', registry=self.registry, timeout=200)

        except Exception as e:
            logging.error("Failt to push:" + str(e))




if __name__ == '__main__':

    parser = ArgumentParser(description='参数描述')
    parser.add_argument("--verbose", help="Increase output verbosity",
                        action="store_const", const=logging.DEBUG, default=logging.INFO)

    parser.add_argument('--filename', default='pingconf.yml')
    parser.add_argument('--ping', default='ping')
    args = parser.parse_args()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    type = args.ping
    try:
        if type == "ping":
            loop.run_until_complete(Ping_push())
        elif type == "webping":
            loop.run_until_complete(Requests_push())
        else:
            # todo
            pass
    except Exception as e:
        logging.error(e)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()









