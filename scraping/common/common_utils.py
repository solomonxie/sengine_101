# Copyright (c) 2020 App Annie Inc. All rights reserved.
import os
import gzip
import time
import uuid
import pickle
import signal
import shutil
import hashlib
from glob import glob
from flask import request
from functools import wraps, partial

from logging import getLogger
logger = getLogger(__name__)


def cmp(x, y):
    return (x > y) - (x < y)


def split_app_id(app_ids):
    unified_app_ids, individual_app_ids = [], []
    for app_id in app_ids:
        if is_unified_app(app_id):
            unified_app_ids.append(app_id)
        else:
            individual_app_ids.append(app_id)
    return unified_app_ids, individual_app_ids


def is_unified_app(app_id):
    return isinstance(app_id, int) and 1000600000000000 < app_id < 1000900000000000


def memoize_at_local_disk(func=None, ttl=None, use_cache=True, *d_args, **d_kwargs):
    """
    AVOID USING FILE-LOCK BY TRY-CATCH OF LOADING UN-STREAM DATA
    """

    if func is None:
        # 1. With dec-args, func == None 2. Without dec-args, func != None
        # Here it's executed while "decorating", not while func "running"
        return partial(memoize_at_local_disk, *d_args, ttl=ttl, use_cache=use_cache, **d_kwargs)
    ttl = ttl or 60 * 5

    @wraps(func)
    def wrapper(*args, **kwargs):
        if use_cache is False:
            return func(*args, **kwargs)

        # PREPARE CACHING IDENTIFICATION
        func_path = '{}.{}'.format(func.__module__, func.__name__)
        sorted_kwargs = ', '.join(['{}: {}'.format(k, kwargs[k]) for k in sorted(kwargs.keys())])
        func_bytes = (func_path + str(args) + sorted_kwargs).encode('utf-8')
        func_md5 = hashlib.md5(func_bytes).hexdigest()
        cache_path = '/tmp/file_cache.{}.{}.cache'.format(func_path, func_md5)
        timer_path = '/tmp/file_cache.{}.{}.timer'.format(func_path, func_md5)
        tmp_path = '/tmp/file_cache.{}.tmp'.format(uuid.uuid4().hex)

        # TIMEOUT FOR CACHE
        cache_files = list(glob('/tmp/file_cache*.cache'))
        for fpath in cache_files:
            ftimerpath = fpath[:fpath.rfind('.cache')] + '.timer'
            if not os.path.exists(ftimerpath):
                continue
            try:
                with open(ftimerpath, 'r') as f:
                    start_time = float(f.read())
                # if time.time() - start_time > TTL and int(time.time()) % 10 == 0:
                if time.time() - start_time > ttl:
                    os.remove(fpath)
                    os.remove(ftimerpath)
                    print('[ Removed ] cache: [{}]'.format(fpath))
            except Exception as ex:
                print('Cannot clean cache [{}]: {}'.format(fpath, str(ex)))

        # READ DATA FROM CACHE
        cache = None
        try:
            with open(cache_path, 'rb') as f:
                cache = pickle.loads(gzip.decompress(f.read()))
            print('[ HIT ] cache at [{}]...'.format(cache_path))
            return cache
        except Exception:
            print('[ MISS ] cache for [{}]'.format(cache_path))

        # GENERATE NEW DATA FROM FUNC
        result = func(*args, **kwargs)
        try:
            with open(tmp_path, 'wb') as f:
                cache = gzip.compress(pickle.dumps(result))
                f.write(cache)
            shutil.copyfile(tmp_path, cache_path)
            os.remove(tmp_path)
            print('[ SAVED ] cache at: {}'.format(cache_path))
            with open(timer_path, 'w') as f:
                f.write(str(time.time()))
        except Exception as ex:
            print('[ FAILED ] when saving cache for [{}]: {}'.format(cache_path, str(ex)))
        finally:
            return result
    return wrapper


def timeout(func=None, ttl=1, default=None, *d_args, **d_kwargs):
    """ DOESN'T WORK IN THREADS """

    if func is None:
        # 1. With dec-args, func == None 2. Without dec-args, func != None
        # Here it's executed while "decorating", not while func "running"
        return partial(timeout, *d_args, ttl=ttl, **d_kwargs)

    def err_handler(n_sig, frame):
        raise RuntimeError('Exceed time limit: {}sec'.format(ttl))

    @wraps(func)
    def wrapper(*args, **kwargs):
        signal.signal(signal.SIGALRM, err_handler)
        signal.alarm(ttl)
        result = default
        try:
            result = func(*args, **kwargs)
        except RuntimeError as ex:
            print('[ TIMEOUT ] Exceed {}sec & force shutdown function: {}.{}'.format(
                ttl, func.__module__, func.__name__
            ))
            raise ex
        finally:
            signal.alarm(0)
        return result

    return wrapper


def timeit(func=None, *d_args, **d_kwargs):
    if func is None:
        # 1. With dec-args, func == None 2. Without dec-args, func != None
        # Here it's executed while "decorating", not while func "running"
        return partial(timeit, *d_args, **d_kwargs)

    @wraps(func)
    def wrapper(*args, **kwargs):
        ptag = d_kwargs.get('ptag') or 'BREADCRUMB PROFILING'
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        req_args = request.args.to_dict() or {}
        logger.info('[ {} ] COST {:.3f}sec'.format(ptag, duration), extra={'tags': {
            'breadcrumb_duration': duration,
            'request_args': req_args,
            'request_url': request.url,
            'api_tag': ptag,
        }})
        return result

    return wrapper


@timeout(ttl=2, default={})
def test_timeout():
    while True:
        time.sleep(1)


@memoize_at_local_disk(ttl=3)
def test_memoize(a, b):
    return a + b


@timeit
def test_timeit():
    print(1)


if __name__ == '__main__':
    test_timeit()
    test_timeout()
    result = test_memoize(1, 2)
    print(result)
