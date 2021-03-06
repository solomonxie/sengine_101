from datetime import datetime
import sqlalchemy
from sqlalchemy import Column

from sqlalchemy.ext.declarative import declarative_base
BASE = declarative_base()


class PageMeta(BASE):
    __tablename__ = 'page_meta'

    mid = Column(sqlalchemy.BigInteger, primary_key=True)
    url = Column(sqlalchemy.BigInteger, nullable=False)
    state = Column(sqlalchemy.BigInteger, default=0)
    page_type = Column(sqlalchemy.SmallInteger)
    # title = Column(sqlalchemy.TEXT)
    # keywords = Column(sqlalchemy.JSON())
    # sub_links = Column(sqlalchemy.JSON())
    # headers = Column(sqlalchemy.JSON())
    # extra = Column(sqlalchemy.JSON())
    created_time = Column(sqlalchemy.DateTime, default=datetime.now())
    updated_time = Column(sqlalchemy.DateTime, default=datetime.now())
