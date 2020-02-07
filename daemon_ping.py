# -*- coding: utf-8 -*-
#!/usr/bin/python3
import daemon
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import os
import yaml
import time

filename = os.path.join(os.path.dirname(__file__), 'prometheus.yml').replace("\\", "/")
f = open(filename)
y = yaml.load(f,Loader=yaml.FullLoader)
url1 = y['url']['url1']
url2 = y['url']['url2']
url3 = y['url']['url3']
city1 = y['gauge']['city1']
city2 = y['gauge']['city2']
target = y['scrape_configs'][1]['static_configs'][0]['targets'][0]
name = y['gauge']['name']
documentation = y['gauge']['documentation']
labelnames = y['gauge']['labelnames']

registry = CollectorRegistry()


def ping_test():

    with True:
        # Guage(metric_name,HELP,labels_name,registry=registry)
        g = Gauge(name, documentation, labelnames,
                  registry=registry)

        g.labels(url1, city1).set(42.5)
        g.labels(url2, city2).dec(2)
        g.labels(url3, city2).inc()

        push_to_gateway(target, job='ping_status', registry=registry)
        time.sleep(2)

with daemon.DaemonContext():
    ping_test()