#!/usr/bin/python
"""

GPL BLAH BLAH BLAH
"""

import argparse
import os
import sys
import ConfigParser
import rhndownloaderapi as rhndwapi

#TODO: Too many packages downloaded check firs if are supported in DB

par = argparse.ArgumentParser(description = 'Download errata pkgs from RHN')
par.add_argument('-e', '--errata', nargs = 1,
                    help = 'errata -> ex: RHSA-2013:1778',
                    required = True)
opts = par.parse_args()
config = ConfigParser.RawConfigParser()
try:
    config.read(os.path.expanduser('~/.checkerrata'))
    USER = config.get('checkerrata','USER')
    PWD = config.get('checkerrata','PWD')
    DBUSER = config.get('checkerrata','DBUSER')
    DBPWD = config.get('checkerrata','DBPWD')
    DBDATABASE = config.get('checkerrata','DBDATABASE')
    DBHOST = config.get('checkerrata','DBHOST')
except ConfigParser.Error:
    sys.exit('*ERROR* reading config file: $HOME/.checkerrata!')

rhn = rhndwapi.RHNdownloader(USER, PWD, DBHOST, DBDATABASE, DBUSER, DBPWD)
rhn.get_errata(opts.errata)
