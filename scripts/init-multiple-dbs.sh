#!/bin/bash
# Creates multiple Postgres databases + a dedicated airflow user on first container start.
# Referenced by docker-compose.yml via docker-entrypoint-initdb.d/.
set -e

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
  echo "Creating databases: $POSTGRES_MULTIPLE_DATABASES"
  for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
      SELECT 'CREATE DATABASE $db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
  done

  # Dedicated airflow role, matching the connection string in docker-compose.yml
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'airflow') THEN
        CREATE ROLE airflow LOGIN PASSWORD 'airflow';
      END IF;
    END
    \$\$;
    GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL
fi
