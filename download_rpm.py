#!/usr/bin/python
"""

GPL BLAH BLAH BLAH
"""

import argparse
import os
import sys
import ConfigParser
import rhndownloaderapi as rhndwapi

par = argparse.ArgumentParser(description = 'Download packages from RHN')
par.add_argument('-p', '--pkgname', nargs = 1,
                    help = 'package name -> ex: httpd',
                    required = True)
par.add_argument('-v', '--pkgver', nargs = 1,
                    help = 'version -> ex: 2.2.15',
                    required = True)
par.add_argument('-r', '--pkgrel', nargs = 1,
                    help = 'release -> ex: 29.el6_4')
par.add_argument('-a', '--pkgarch', nargs = 1,
                    help = 'arch -> ex: x86_64')
par.add_argument('-d', '--pkgdbg', nargs = 1, default = '0',
                    choices=['0', '1'], help = 'Download debug package')
par.add_argument('-s', '--pkgsrc', nargs = 1, default = '0',
                    choices = ['0', '1'], help = 'Download src package')
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
rhn.get_package(opts.pkgname, opts.pkgver, opts.pkgrel,
                opts.pkgarch, opts.pkgdbg, opts.pkgsrc)
