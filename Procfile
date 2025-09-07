web: gunicorn wsgi:app --workers 4 --timeout 120 --log-file - --log-level debug
worker: python -m app.scheduler