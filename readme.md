Steps to initialize:

Start Worker:
celery -A app.celery_app worker --loglevel=info

Start Flask Server:
python app.py
