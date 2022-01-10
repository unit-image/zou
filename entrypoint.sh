#!/bin/bash
apt install -y netcat

while ! nc -z $DB_HOST $DB_PORT; do
    echo Waiting for database service to start...;
    sleep 1;
done

if [ -v ALEMBIC_REVISION ]; then
    cd /opt/zou/zou/migrations
    export FLASK_APP=/opt/zou/zou/app/__init__.py
    if [ "$ALEMBIC_REVISION" == "head" ]; then
        alembic upgrade head
    else
        alembic downgrade $ALEMBIC_REVISION || alembic upgrade $ALEMBIC_REVISION
    fi
fi

cd /opt/zou
exec "$@"
