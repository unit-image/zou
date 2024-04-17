#!/bin/bash
while ! nc -z $DB_HOST $DB_PORT; do
    echo Waiting for database service to start...;
    sleep 1;
done

retry_counter=0
while ! nc -zu $COLLECTD_HOST $COLLECTD_SQLALCHEMY_PORT; do
    if [ $retry_counter -ge 10 ]; then
        echo "$COLLECTD_HOST:$COLLECTD_SQLALCHEMY_PORT not reachable, giving up"
        break
    else
        echo Waiting for collectd sqlalchemy plugin to start... Retry count: $retry_counter;
        retry_counter=$((retry_counter+1))
        sleep 1;
    fi
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
