import logging
import asyncio
import aiohttp

from lxml import html


__author__ = "Andrew Gafiychuk"


class Scraper(object):
    """
    Simple class for parsing "https://coinmarketcap.com/".
    Parse it for all data about each coin.
    Return list of tuples with name, market_cap,
    price, circulating supply, volume(24h), change in %(24h)
    
    """
    def __init__(self):
        """
        Constructor.
        
        """
        logging.debug("[+] Scraper initial...")

        self.url = "https://coinmarketcap.com/all/views/all/"
        self.session = None

    async def _init_session(self):
        """
        Private method for init sessions params.
        Header, connector.
        
        """
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
        self.session = aiohttp.ClientSession(connector=connector,
                                             headers=HEADER)

        logging.debug("[+] HEADER's init complete!!!")

    def start(self):
        """
        Main method for start parsing.
        
        """
        logging.debug("[+] Start scrap task...")

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

        try:
            event_loop.run_until_complete(self._init_session())
            data = event_loop.run_until_complete(self._main_task())

            return data

        except Exception as err:
            logging.error("[+] Some error in event_loop init...\n"
                          "{0}".format(err))

        finally:
            self.session.close()
            event_loop.close()

            logging.debug("[+] Scrap complete!!!")

    async def _main_task(self):
        """
        Create task and start it.
        Return results if success, else print error.
        
        """
        logging.debug("[+] Main task started...")

        tasks = [self._scrap(self.url)]
        results = []

        try:
            for task in asyncio.as_completed(tasks):
                data = await task
                results.extend(data)
                task.close()

            logging.debug("[+] Main task complete!!!")
            return results

        except Exception as err:
            logging.error("[+] Main task error...\n"
                          "{0}".format(err))

    async def _scrap(self, url):
        """
        Private method for GET data from host.
        Parse page for data and create result list.
        
        """
        async with self.session.get(url) as response:
            if response.status == 200:
                page = await response.text()

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
            else:
                logging.error("[+] Response error...\n"
                              "{0}".format(response.status))
