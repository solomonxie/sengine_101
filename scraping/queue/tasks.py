"""
REF: https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#first-steps
REF: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#crontab-schedules
"""

from celery import Celery
# from celery.schedules import crontab

import settings
# from scraping.common import db_utils
# from scraping.common import redis_utils
from scraping.general_scraper import GeneralScraper
from scraping.core.impl import find_batch_unscraped_links

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

T = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)


@T.task(name='dispatch_unscraped_links')
def task__dispatch_unscraped_links(batch_size=10):
    links = find_batch_unscraped_links()
    for url in links:
        start_scraping.delay(url)
        logger.info('[ DISPATCH ] STARTING NEW URL: {}'.format(url))
    return links


@T.task(name='start_scraping')
def start_scraping(url):
    # 1. Check redis domain rate limit
    # TODO...

    # 1. change db state to 1
    # TODO...

    # 2. Start scraping
    scraper = GeneralScraper()
    __import__('pudb').set_trace()
    scraper.start(url)

    # 3. Change db state to 2
    # TODO...

    logger.info('[ OK ] {}'.format(url))


@T.on_after_configure.connect
def schedule_unstarted_tasks(sender, **kwargs):
    _ = kwargs
    sender.add_periodic_task(
        2,  # sec,
        task__dispatch_unscraped_links.s(),
        name='Dispatch unscraped tasks',
        expires=60,
    )


def main():
    __import__('pudb').set_trace()
    start_scraping.delay('https://wikipedia.org')
    logger.info('OK.')


if __name__ == '__main__':
    main()
