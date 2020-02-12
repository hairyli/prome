#!/usr/bin/env python
# encoding: utf-8
import time
import asyncio
import aiohttp
import sys

host = 'http://www.baidu.com'
loop = asyncio.get_event_loop()


async def fetch(url):
    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.get(url) as response:
            response = await response.read()
            # print(response)
            return response


if __name__ == '__main__':

    start = time.time()
    tasks = [fetch(host) for i in range(int(sys.argv[1]))]
    loop.run_until_complete(asyncio.gather(*tasks))
    print("spend time : %s" % (time.time() - start))
    loop.close()