import logging
import asyncio
import aiohttp
from lxml import html

url = "https://coinmarketcap.com/all/views/all/"

async def _init_session():
    logging.debug("[+] Created HEADER's...")

    HEADER = {
        'Accept': 'text/html,application/xhtml+xml,'
                'application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;'
                        'q=0.4,uk;q=0.2',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64)'
                    'AppleWebKit/537.36 (KHTML, like Gecko)'
                    'Chrome/57.0.2987.133 Safari/537.36',
    }

    connector = aiohttp.TCPConnector(verify_ssl=True)
    session = aiohttp.ClientSession(connector=connector,
                                         headers=HEADER)

    logging.debug("[+] HEADER's init complete!!!")

    return session

def start():
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    event_loop.run_until_complete(_init_session())
    data = event_loop.run_until_complete(_main_task())

    return data

async def _main_task():
    tasks = [_scrap(url)]
    results = []

    for task in asyncio.as_completed(tasks):
        page = await task
        data = parse(page)

        results.extend(data)
        task.close()

    return results

async def _scrap(url):
    session = _init_session()

    async with session.get(url) as response:
        if response.status == 200:
            page = await response.text()

            return page
        else:
            logging.error("[+] Response error...\n"
                          "{0}".format(response.status))

def parse(page):
    res_list = []

    root = html.fromstring(page)

    table = root.xpath(
        '//table[@id="currencies-all"]/tbody/tr')

    for n, tr in enumerate(table, 1):
        name = tr.xpath(
            './/td[@class="no-wrap currency-name"]'
            '/a/text()')[0]
        symbol = tr.xpath(
            './/td[@class="text-left"]'
            '/text()')[0]
        market_cap = tr.xpath(
            './/td[@class="no-wrap market-cap '
            'text-right"]'
            '/text()')[0].strip()
        price = tr.xpath(
            './/td[@class="no-wrap text-right"]'
            '/a[@class="price"]/text()')[0]
        cs = tr.xpath(
            './/td[@class="no-wrap text-right"]'
            '/a[@target="_blank"]/text() |'
            './/td[@class="no-wrap text-right"]'
            '/span/text()')[0].strip()
        volume = tr.xpath(
            './/td[@class="no-wrap text-right "]'
            '/a/text()')[0]
        changes = tr.xpath(
            './/td[starts-with(@class,"no-wrap percent-")]'
            '/text() |'
            './/td[@class="text-right"]/text()')

        t = (name, symbol, market_cap, price, cs, volume,
             changes[0], changes[1], changes[2])

        res_list.append(t)

    return res_list