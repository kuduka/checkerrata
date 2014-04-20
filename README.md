checkerrata
===========

Tool in order to check pending erratas from a sosreport

Based on:

 * https://github.com/ssato/sos-analyzer
 * https://github.com/pybliss/rhscheck/blob/master/rhscheck.py
 * checksysreport (looks like the official homepage was deleted long time ago)

Usage:

 ./rhnclone.py --> Clone RHN data
 ./sosreport.py -s <path sosreport> --> Check erratas

TODO:

* Documentation (this)

Configuration file:

# cat .checkerrata
[checkerrata]
USER =  user
PWD = pwd
URL = https://rhn.redhat.com/rpc/api
DBUSER = errata
DBPWD = pwd
DBDATABASE = errata
DBHOST = 127.0.0.1
