import logging
import asyncio
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway, pushadd_to_gateway
import os
import yaml
import daemon
import threading

logging.basicConfig(
    filename='logging.log',
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:%(message)s'
)


def io_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

class Push(object):

    def __init__(self):
        self.filename = os.path.join(os.path.dirname(__file__), 'prometheus.yml').replace("\\", "/")
        self.f = open(self.filename)
        self.y = yaml.load(self.f, Loader=yaml.FullLoader)
        self.url1 = self.y['url']['url1']
        self.url2 = self.y['url']['url2']
        self.url3 = self.y['url']['url3']
        self.city1 = self.y['gauge']['city1']
        self.city2 = self.y['gauge']['city2']
        self.target = self.y['scrape_configs'][1]['static_configs'][0]['targets'][0]
        self.name = self.y['gauge']['name']
        self.documentation = self.y['gauge']['documentation']
        self.labelnames = self.y['gauge']['labelnames']

    async def gauge(self):

        registry = CollectorRegistry()
        g = Gauge(self.name, self.documentation, self.labelnames,
                  registry=registry)

        g.labels(self.url1, self.city1).set(42.5)
        g.labels(self.url2, self.city2).dec(2)
        g.labels(self.url3, self.city2).inc()

        push_to_gateway(self.target, job='ping_status', registry=registry)

    def start(self):
        logging.info('daemon start')
        loop = io_loop()
        try:
            while True:
                loop.run_until_complete(Push().gauge())
        except Exception as e:
            logging.error(e)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()



if __name__ == '__main__':
    p = Push()
    t = threading.Thread(target=p.start)
    t.setDaemon(True)
    t.start()
    t.join()