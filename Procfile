web: gunicorn ecomerce.wsgi
web: daphne ecomerce.asgi:application --port $PORT --bind 0.0.0.0 -v2
chatworker: python manage.py runworker --settings=ecomerce.settings -v2