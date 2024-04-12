#!/bin/bash
while ! nc -z $DB_HOST $DB_PORT; do
    echo Waiting for database service to start...;
    sleep 1;
done

while ! nc -zu $COLLECTD_HOST $COLLECTD_SQLALCHEMY_PORT; do
    echo Waiting for collectd sqlalchemy plugin to start...;
    sleep 1;
done
export COLLECTD_HOST_IPV4=$(getent hosts collectd | awk '{ print $1 }')

if [ ! -z "$ALEMBIC_REVISION" ]; then
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
