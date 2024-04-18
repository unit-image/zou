#!/bin/bash
while ! nc -z $DB_HOST $DB_PORT; do
    echo Waiting for database service to start...;
    sleep 1;
done

retry_counter=0
COLLECTD_HOST_IPV4=""
while  [ ! $COLLECTD_HOST_IPV4 ] && [ $retry_counter -le 5 ] ; do
    COLLECTD_HOST_IPV4=$(nslookup -retry=0 -timeout=1 collectd | awk '/^Name:/ {N=$2} ; /^Address:/ {A=$2} ; END {print A}')
    if [ ! $COLLECTD_HOST_IPV4 ]; then
        echo Waiting for collectd sqlalchemy plugin to start... Retry count: $retry_counter;
        retry_counter=$((retry_counter+1))
    fi
done
export COLLECTD_HOST_IPV4=$COLLECTD_HOST_IPV4

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
