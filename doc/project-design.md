# Project Draft

Project vision:
This search engine is NOT a general search engine like Google, but a in-depth domain search engine.


## Features

TODO:
- [ ] PDF searching
- [ ] BaiduPan share links searching


## Inventory

Inventory:
- [ ] EC2 ==> Main host
- [ ] EBS + S3 ==> As elastic cloud storage
- [ ] MongoDB (container on EC2) ==> As document storage
- [ ] Redis (container on EC2) ==> As Message Queue & request rate limiter
- [ ] Postgres (container on EC2) ==> For Indexing


## Architecture | Tech Stach

Stach:
- [ ] Front End ==> Bootstrap + AJAX
- [ ] Backend API ==> Python + FastAPI
- [ ] Backend Scraper ==> Python + requests
- [ ] Searching Algorithm ==> C
- [ ] Parsing & Indexing ==> C


## Antiscrape Strategy

It'll be much effort to implement Proxy strategy for scraping, so in this project we are to use **Single IP** for scraping.

Need to have a `domain-aware` scraping schedular, to avoid too many requests into the same domain.
