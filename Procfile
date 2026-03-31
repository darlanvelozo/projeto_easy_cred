web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn systempaytec.wsgi --bind 0.0.0.0:$PORT
