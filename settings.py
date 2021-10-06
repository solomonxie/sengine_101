import os

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or ''
CELERY_BACKEND_URL = os.environ.get('CELERY_BACKEND_URL') or ''

AWS_S3_ACCESS_ID = os.environ.get('AWS_S3_ACCESS_ID') or ''
AWS_S3_ACCESS_SECRET = os.environ.get('AWS_S3_ACCESS_SECRET') or ''
AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME') or ''

try:
    from scraping.settings_local import *  # NOQA: F401,F403
except Exception:
    pass
