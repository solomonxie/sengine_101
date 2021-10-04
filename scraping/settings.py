
CELERY_BROKER_URL = ''
CELERY_BACKEND_URL = ''

AWS_ACCESS_ID = ''
AWS_ACCESS_SECRET = ''
BUCKET_NAME = ''

try:
    from scraping.settings_local import *  # NOQA: F401,F403
except Exception:
    pass
