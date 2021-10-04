# DB Design



## MongoDB

Table: page_meta
Schema:
```
id int,
url varchar,
state varchar,
title varchar,
page_type varchar,
headers jsonb,
keywords array,
extra jsonb
```
