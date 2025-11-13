
#!/bin/bash
SUPERUSER_EMAIL=${SUPERUSER_EMAIL:-"bilaljmal@gmail.com"}


cd /neksio/
/opt/venv/bin/python manage.py createsuperuser --email $SUPERUSER_EMAIL
--noinput || true

#/opt/venv/bin/python manage.py migrate --noinput

