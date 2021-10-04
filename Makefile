run-celery-worker:
	celery -A scraping.queue.tasks worker -E --loglevel=INFO

launch-celery-hello-world:
	python -m scraping.queue.tasks


run-celery-schedular-hello-world:
	celery -A scraping.queue.tasks beat
