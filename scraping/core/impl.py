from scraping.common import db_utils
# from database.models import db_models
from scraping.sqls import page_meta_sqls


def filter_new_links(links):
    # with db_utils.get_session() as session:
    #     records = session.query(db_models.PageMeta).filter(
    #         ~db_models.PageMeta.url._in(list(links))
    #     ).fetch_all()
    #     new_links = {r['url'] for r in records}
    sql = page_meta_sqls.GET_NEW_LINKS % ','.join([f"'{x}'" for x in links])
    records = db_utils.query_sql(sql)
    old_links = {r['url'] for r in records}
    new_links = set(links) - old_links
    return new_links


def find_batch_unscraped_links(batch_size=10):
    sql = page_meta_sqls.GET_UNSCRAPED_LINKS
    params = {'size': batch_size}
    records = db_utils.query_sql(sql, params)
    links = {r['url'] for r in records}
    return links


def main():
    links = find_batch_unscraped_links()
    print(links)
    print('OK.')


if __name__ == '__main__':
    main()
