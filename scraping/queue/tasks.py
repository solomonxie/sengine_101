"""
REF: https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#first-steps
REF: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#crontab-schedules
"""

from celery import Celery

import settings
from scraping.general_scraper import GeneralScraper

T = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)


@T.task(name='scrape')
def start_scraping(url):
    scraper = GeneralScraper(url)
    resp = scraper.start()
    print(resp)


def main():
    resp = start_scraping('https://wikipedia.org')
    print(resp)


if __name__ == '__main__':
    main()
