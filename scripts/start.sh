#!/usr/bin/env bash
set -o errexit

# Migrações e estáticos
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Inicia o servidor
gunicorn chadepanela.wsgi:application --bind 0.0.0.0:${PORT:-8000}
