GET_UNSCRAPED_LINKS = """
    SELECT url FROM page_meta WHERE state = 0 LIMIT :size
"""

GET_NEW_LINKS = """
    SELECT url FROM page_meta WHERE url IN (%s)
"""
