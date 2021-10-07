import re
import urllib
import requests
import tldextract

import settings
from database.models import db_models
from scraping.common import db_utils
from scraping.common import redis_utils
from scraping.base_scraper import BaseScraper
from scraping.core.impl import filter_new_links

import logging
logging.basicConfig(level=logging.DEBUG)
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

    resp = requests.head(url, headers=headers, allow_redirects=True)
    assert 200 <= resp.status_code < 400, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
    assert 'html' in str(resp.headers.get('content-type')), 'Target is not HTML page'

    resp = requests.get(url, headers=headers, allow_redirects=True)
    assert 200 <= resp.status_code < 400, 'Failed scraping target with status[{}]: {}'.format(resp.status_code, url)
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
    new_links = filter_new_links(links)
    records = [db_models.PageMeta(url=x, state=0) for x in new_links]
    # with db_utils.get_session('pg') as session:
    with db_utils.get_session('sqlite') as session:
        session.begin()
        session.bulk_save_objects(records)
        # session.add_all(records)  # TOO SLOW, IT SENDS REQUEST 1BY1
        session.commit()
    return len(records)


class GeneralScraper(BaseScraper):
    def __init__(self, **kwargs):
        self.headers = kwargs.get('headers') or settings.SCRAPER_HEADERS
        self.url2resp = {}

    def start(self, url: str):
        links = scrape(url, headers=self.headers)
        count = save_links(links)
        return count


def main():
    scraper = GeneralScraper()
    __import__('pudb').set_trace()
    scraper.start('https://zh.wikipedia.org')
    __import__('pudb').set_trace()
    logger.info('OK.')


if __name__ == '__main__':
    main()
