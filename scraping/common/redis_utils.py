import redis

import settings


def get_redis_connection():
    __import__('pudb').set_trace()
    r = redis.Redis.from_url(settings.SCRAPER_REDIS_URL)
    return r


def main():
    r = get_redis_connection()
    r.set('foo', 'bar')
    print(r.get('foo'))
    print('OK.')


if __name__ == '__main__':
    main()
