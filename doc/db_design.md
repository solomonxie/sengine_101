# DB Design



## ~Postgres~

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


## Sqlite + JSON.gz

The PG is not a good choice to store billions of page meta.
So the solution can be:

Sqlite to store the minimal url info as index,
and the full page & meta will be stored with JSON.gz and organized into directory named under each domain.


Sqlite columns:
- id
- url
- fpath


There will be multiple JSON files for the same page:
- Raw Response
- Parsed HTML/Text
- Page Meta
