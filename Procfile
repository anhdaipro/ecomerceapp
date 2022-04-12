
release: python manage.py migrate
web: daphne ecomerce.asgi:application --port $PORT --bind 0.0.0.0 -v2
worker: python manage.py runworker channels --settings=ecomerce.settings -v2