#!/bin/bash

DATABASE="errata"
USER="errata"
CLIUSER="checkerrata"
PASSWORD="xxxx"
CLIPASSWORD="xxxx"
BKPSQL="/tmp/dump.sql"
BKPSRC="/tmp/db.sql"

exit 1

if [ ! -f $BKPSRC ]; then
    print "*ERROR*: Unable to find schmea $BKPSRC"
    exit 1
fi

if [ -f $BKPSQL ]; then
    rm $BKPSQL
fi


#TODO checks

#sudo yum install -y postgresql-server.x86_64 python-psycopg2 python-mechanize
#sudo chkconfig postgresql on
#sudo service postgresql initdb
#sudo service postgresql start

#TODO: remove user if exists $CLIUSER $USER

#sudo -u postgres pg_dump $DATABASE > $BKPSQL
#sudo -u postgres /usr/bin/psql template1 -c "drop database if exists $DATABASE"
#sudo -u postgres /usr/bin/psql template1 -c "create database $DATABASE"
sudo -u postgres /usr/bin/psql template1 -c "create user $USER with password '$PASSWORD'"
sudo -u postgres /usr/bin/psql template1 -c "create user $CLIUSER with password '$CLIPASSWORD'"
sudo -u postgres /usr/bin/psql template1 -c "alter database $DATABASE owner to $USER"
sudo -u postgres /usr/bin/psql errata -c "grant all privileges on database $DATABASE to $USER"
#
#sudo -u postgres /usr/bin/psql $DATABASE -f $BKPSRC


#su postgres -c 'psql $DATABASE -c "select 'grant select on '|| relname ||' to $CLIUSER;' from pg_class join pg_namespace on pg_namespace.oid= pg_class.relnamespace where nspname = 'public' and relkind in ('r','v');"'

