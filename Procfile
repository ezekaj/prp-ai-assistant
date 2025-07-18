web: gunicorn --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY prp_app:app
worker: celery -A prp_tasks worker --loglevel=info --concurrency=$CELERY_CONCURRENCY
beat: celery -A prp_tasks beat --loglevel=info
migrate: python manage.py migrate