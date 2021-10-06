"""
REF: https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#first-steps
REF: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#crontab-schedules
"""

import time
from celery import Celery
from celery.schedules import crontab

import settings
from scraping.general_scraper import GeneralScraper

T = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL)


@T.task(name='hello')
def hello_world():
    for i in range(10):
        sub_task.delay(i)
        print('distributed a child task: ' + str(i))
        time.sleep(1)
    with open('/tmp/hello.log', 'a') as f:
        f.write('NOW: ' + str(time.time()) + '\n')
    return 0


@T.task(name='hi')
def sub_task(i):
    with open('/tmp/hello.log', 'a') as f:
        f.write('\tSUB: ' + str(i) + '\n')
    return i


@T.task(name='scrape')
def start_scraping(url):
    scraper = GeneralScraper(url)
    resp = scraper.start()
    print(resp)


@T.on_after_configure.connect
def hello_scheduler(sender, **kwargs):
    _ = kwargs
    # Every 2 seconds.
    sender.add_periodic_task(2, sub_task.s(int(time.time())), name='add every 2', expires=60)
    # Every minute
    sender.add_periodic_task(
        crontab(hour=None, minute=None, day_of_week=None),
        hello_world(),
    )


def main():
    resp = hello_world.delay()
    print(resp)

    resp = start_scraping('https://wikipedia.org')
    print(resp)


if __name__ == '__main__':
    main()
