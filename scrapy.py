import datetime
import sys
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import urllib.request as urllib2
from LanCaster import LanCaster
from PuppyFinder import PuppyFinder
from PuppySpot import PuppySpot
from fbase import load_json
import logging

def main():

    logging.basicConfig(filename='log.log', encoding='utf-8', level=logging.DEBUG)

    data = load_json()
    # classList = []
    for url in data["urls"]:
        # if (url.find("www.lancasterpuppies.com") > -1):
        #     scrapy = LanCaster(url)
        #     # classList.append(scrapy)
        #     scrapy.pages()
        #     scrapy.read_all()
        #     scrapy.update_db()
        
        # if (url.find("puppyfinder.com") > -1):
        #     scrapy = PuppyFinder(url)
        #     # classList.append(scrapy)
        #     scrapy.pages()
        #     scrapy.read_all()
        #     scrapy.update_db()
        #     # break

        if (url.find("puppyspot.com") > -1):
            scrapy = PuppySpot(url)
            # classList.append(scrapy)
            scrapy.pages()
            scrapy.read_all()
            scrapy.update_db()
            # break
        # scrapy.parse()
        # scrapy.pages()
        # scrapy.read_all()
        # https://www.puppyspot.com/puppies-for-sale/breed/french-bulldog/

    # for scrap in classList:
    #     scrap.update_db()
    
main()

    