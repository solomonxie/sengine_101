#! python
# FLAKE8: NOQA
import os

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or ''
CELERY_BACKEND_URL = os.environ.get('CELERY_BACKEND_URL') or ''

# S3
AWS_S3_ENDPOINT = os.environ.get('AWS_S3_ENDPOINT') or ''
AWS_S3_REGION = os.environ.get('AWS_S3_REGION') or ''
AWS_S3_ACCESS_ID = os.environ.get('AWS_S3_ACCESS_ID') or ''
AWS_S3_ACCESS_SECRET = os.environ.get('AWS_S3_ACCESS_SECRET') or ''
AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME') or ''

# Redis
SCRAPER_REDIS_URL = os.environ.get('SCRAPER_REDIS_URL') or ''

SCRAPER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-US;q=0.7,en-GB;q=0.6,zh-HK;q=0.5,zh-TW;q=0.4",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Chromium\";v=\"94\", \"Google Chrome\";v=\"94\", \";Not A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "cookie": "GeoIP=US:CA:Los_Angeles:34.05:-118.25:v4; WMF-Last-Access=06-Oct-2021; WMF-Last-Access-Global=06-Oct-2021",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
}

try:
    from scraping.settings_local import *
except Exception:
    pass
