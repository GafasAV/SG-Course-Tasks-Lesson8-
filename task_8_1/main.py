import logging

from datetime import datetime
from scraper import Scraper
from saver import ExcelDS


__author__ = "Andrew Gafiychuk!"


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("[+] App started...")

    scraper = Scraper()
    data_list = scraper.start()

    print("Data size: {0}".format(len(data_list)))

    file_name = 'test.xls'
    sheet_name = 'Data for {0:%Y-%m-%d-%H-%M-%S}'.format(datetime.now())

    ecl = ExcelDS(file_name, sheet_name)
    ecl.write_data(data_list)

    logging.debug("[+] App complete!!!")
