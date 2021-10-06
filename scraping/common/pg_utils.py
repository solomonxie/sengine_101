import psycopg2
import sqlalchemy
from time import time
from retry import retry
from contextlib import contextmanager
from sqlalchemy.pool import QueuePool
from requests.structures import CaseInsensitiveDict
from sqlalchemy.orm import sessionmaker, scoped_session

import settings

from logging import getLogger
logger = getLogger(__name__)


SESSION_MAKER = {0: None}


def create_sqlalchemy_engine(conn_url):
    assert bool(settings.PG_CONN_URL), 'PG CONNECTION URL IS EMPTY...'
    engine = sqlalchemy.create_engine(
        conn_url,
        echo=True,
        # isolation_level='AUTOCOMMIT',  # IMPORTANT: R/O USER SHOULD HAVE THIS
        poolclass=QueuePool,
        pool_recycle=30,
        pool_size=50,
    )
    return engine


def get_session_maker():
    """
    CONNECTION MANAGEMENT STRATEGY:
    - EACH THREAD HAS 1 ENGINE (CONNECTION POOL) TO KEEP THREAD SAFE
    - SESSION MAKER SHOULD BE AT TOP LEVEL IN THE APPLICATION
    """
    if SESSION_MAKER[0]:
        return SESSION_MAKER[0]

    logger.info('Creating new SQLALchemy Engine...')
    engine = create_sqlalchemy_engine(settings.PG_CONN_URL)
    maker = sessionmaker(bind=engine, autocommit=True)
    SESSION_MAKER[0] = maker
    return maker


@contextmanager
def get_context_session():
    session = scoped_session(get_session_maker())
    try:
        yield session
    except psycopg2.OperationalError as ex:
        # Remove Global Session Maker if it's expired
        SESSION_MAKER[0] = None
        raise ex
    except Exception as ex:
        session.rollback()
        raise ex
    finally:
        session.close()


@retry((psycopg2.OperationalError, ), tries=5, delay=0.5, jitter=0.3, logger=logger)
def _run_sql_with_session(sql, params, **kwargs):
    """ SEPARATE ACTUAL IMPL FOR EASIER MOCK IN UT """
    start = time()
    with get_context_session() as session:
        logger.debug('Session created in {:.3f}sec'.format(time() - start))
        rows = session.execute(sql, params).fetchall()
    if kwargs.get('insensitive_dict') is not False:
        rows = [CaseInsensitiveDict(x) for x in rows]
    return rows


def run_sql(sql, params, **kwargs):
    start = time()
    rows = _run_sql_with_session(sql, params, **kwargs)
    duration = time() - start
    logger.info('Cost {:.2f}sec at executing the query'.format(duration), extra={'tags': {
        'sql_stmt': sql, 'sql_prams': str(params), 'sql_duration': str(duration), 'sql_rows_count': len(rows),
    }})

    return rows


def get_sql_execution_plan(sql, params):
    sql = 'EXPLAIN ANALYZE ' + sql
    rows = _run_sql_with_session(sql, params)
    steps = [r.get('QUERY PLAN', '') for r in rows]
    exec_time = ''
    for step in steps[-5:]:
        if 'execution time' in step.lower():
            exec_time = step
            break
    return exec_time, steps


def test_fetch():
    sql = """SELECT * FROM mytable LIMIT 1 """
    rows = run_sql(sql, {})
    print(rows)
    return rows


def main():
    test_fetch()


if __name__ == '__main__':
    main()
