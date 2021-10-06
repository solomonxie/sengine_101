import requests

import settings
from scraping.base_scraper import BaseScraper

import logging
logger = logging.getLogger(__name__)


class GeneralScraper(BaseScraper):
    def __init__(self, **kwargs):
        self.headers = kwargs.get('headers') or settings.SCRAPER_HEADERS
        self.url2resp = {}

    def scrape(self, url):
        assert url not in ['', None], 'SHOULD GIVE URL'
        try:
            __import__('pudb').set_trace()
            resp = requests.head(url, headers=self.headers)
            assert resp.status_code == 200, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
            resp = requests.get(url, headers=self.headers)
            assert resp.status_code == 200, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
            self.url2resp[url] = resp
        except Exception as e:
            logger.error(e)


def main():
    scraper = GeneralScraper()
    scraper.scrape('https://www.wikipedia.org/')
    __import__('pudb').set_trace()
    print('OK.')


if __name__ == '__main__':
    main()
