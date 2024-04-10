#!/bin/sh -ex
celery -A backend.celery beat -l info &
celery -A backend.celery worker -l info &
tail -f /dev/null