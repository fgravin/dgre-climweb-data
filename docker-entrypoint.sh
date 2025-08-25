#!/bin/sh

echo "Setup Schema"
flask --app=dgrehydro setup_schema

echo "Running Migrations"
flask --app=dgrehydro db upgrade

echo "Create PG Functions"
flask --app=dgrehydro create_pg_functions

echo "Load geometries"
flask --app=dgrehydro load_geometries

# ensure cron is running
service cron start
service cron status

exec "$@"
