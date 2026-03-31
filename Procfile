web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py popular_banco_prod && gunicorn systempaytec.wsgi --bind 0.0.0.0:$PORT
