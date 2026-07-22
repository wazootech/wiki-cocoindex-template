#!/bin/sh
set -eu

pg_ctlcluster 15 main start
exec tail -F /var/log/postgresql/postgresql-15-main.log
