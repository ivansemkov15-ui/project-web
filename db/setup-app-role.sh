#!/bin/bash
set -e

: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -v app_password="$APP_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE phonebook_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'phonebook_app')
\gexec

SELECT format('ALTER ROLE phonebook_app WITH LOGIN PASSWORD %L', :'app_password')
\gexec

GRANT CONNECT ON DATABASE phonebook TO phonebook_app;
GRANT USAGE ON SCHEMA public TO phonebook_app;
GRANT SELECT, INSERT ON TABLE users TO phonebook_app;
GRANT SELECT, INSERT, DELETE ON TABLE groups TO phonebook_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE contacts TO phonebook_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO phonebook_app;
SQL
