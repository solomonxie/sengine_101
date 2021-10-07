import re
import urllib
import requests
import tldextract

import settings
from database.models import pg_models
from scraping.common import db_utils
from scraping.common import redis_utils
from scraping.base_scraper import BaseScraper

import logging
logger = logging.getLogger(__name__)


def get_domain_from_url(url: str):
    o = tldextract.extract(str(url).strip())
    domain = '{}.{}'.format(o.domain, o.suffix)
    return domain


def increase_visit_count(domain, count=1):
    r = redis_utils.get_redis_connection()
    k = 'rate_limit__{}'.format(domain)
    r.incr(k, count)
    return count


def scrape(url: str, headers: dict = None):
    assert bool(url), 'SHOULD GIVE URL'
    domain = get_domain_from_url(url)
    increase_visit_count(domain, 2)

    resp = requests.head(url, headers=headers)
    assert resp.status_code == 200, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
    assert 'html' in str(resp.headers.get('content-type')), 'Target is not HTML page'

    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
    links = extract_links(url, resp.content)
    return links


def extract_links(url: str, html: str):
    """ Store in DB for schedular to dispatch to more individual tasks """
    assert bool(html), 'HTML should not be empty'
    sources = re.findall('href="([^"]*)"', str(html))
    o = urllib.parse.urlparse(url)
    links = set()
    for href in sources:
        if href.startswith('http'):
            links.add(href)
        elif href.startswith('//'):
            x = o.scheme + ':' + href
        elif href.startswith('/'):
            x = o.scheme + '://' + o.netloc + href
        elif not href.startswith('/'):
            x = o.scheme + '://' + href
        else:
            x = href
        try:
            obj = urllib.parse.urlparse(x)
            assert bool(obj.netloc or obj.path)
            links.add(obj.geturl())
        except Exception:
            pass

    return links


def save_links(links: list):
    assert bool(links), 'HTML should not be empty'
    records = [
        pg_models.PageMeta(
            url=x,
            state=0
        ) for x in links
    ]
    with db_utils.get_session('sqlite') as session:
        session.begin()
        session.add_all(records)
        session.commit()
    return


class GeneralScraper(BaseScraper):
    def __init__(self, **kwargs):
        self.headers = kwargs.get('headers') or settings.SCRAPER_HEADERS
        self.url2resp = {}

    def start(self, url: str):
        __import__('pudb').set_trace()
        links = scrape(url, headers=self.headers)
        __import__('pudb').set_trace()
        save_links(links)


def main():
    scraper = GeneralScraper()
    scraper.start('https://www.wikipedia.org/')
    __import__('pudb').set_trace()
    print('OK.')


if __name__ == '__main__':
    main()
