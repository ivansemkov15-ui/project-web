#!/bin/bash
set -e

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    mkdir -p "$PGDATA"
    chown -R postgres:postgres /var/lib/postgresql
    chmod 700 "$PGDATA"

    until pg_isready -h db -p 5432 -U phonebook; do
        sleep 2
    done

    export PGPASSWORD="$REPLICATION_PASSWORD"
    gosu postgres pg_basebackup -h db -p 5432 -U replicator -D "$PGDATA" -Fp -Xs -R
    printf "\nprimary_conninfo = 'host=db port=5432 user=replicator password=%s'\n" \
        "$REPLICATION_PASSWORD" >> "$PGDATA/postgresql.auto.conf"
    chown postgres:postgres "$PGDATA/postgresql.auto.conf"
fi

exec docker-entrypoint.sh postgres -c hot_standby=on
