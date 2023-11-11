release: ./release.sh
web: gunicorn e_metric_api.wsgi:application
worker_1: celery -A e_metric_api worker --loglevel=INFO --concurrency=2
worker_2: celery -A e_metric_api beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

