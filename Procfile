release: echo "Running release phase..." && python init_app.py && echo "Release phase complete."
web: gunicorn wsgi_simple:app --workers 2 --timeout 120 --log-file - --log-level debug