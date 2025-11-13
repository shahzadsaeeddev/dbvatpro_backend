#!/bin/bash
/opt/venv/bin/python manage.py collectstatic  --noinput
/opt/venv/bin/python manage.py migrate  --noinput

DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-adminpassword}

# Create a superuser if it doesn't exist
# /opt/venv/bin/python manage.py shell -c "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
#     User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL}', '${DJANGO_SUPERUSER_PASSWORD}');
#     print('Superuser created');
# else:
#     print('Superuser already exists');
# "

APP_PORT=${PORT:-8030}
cd /neksio/
/opt/venv/bin/gunicorn --worker-tmp-dir /dev/shm project.wsgi:application --bind "0.0.0.0:${APP_PORT}"





