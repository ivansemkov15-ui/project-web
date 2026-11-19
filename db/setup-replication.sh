#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -v replication_password="$REPLICATION_PASSWORD" <<'SQL'
CREATE ROLE replicator WITH LOGIN REPLICATION PASSWORD :'replication_password';
SQL

printf '\nhost replication replicator all scram-sha-256\n' >> "$PGDATA/pg_hba.conf"
pg_ctl -D "$PGDATA" reload
