#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
    GPL INFO BLAH BLAH
"""

import mechanize
import sys
import re
import os
import rhndb

#TODO: Check user/pwd login OK
#TODO: get_package_url -> remove test = 1

class RHNdownloader(object):
    """ Downloads RPM from RHN """

    rhnurl = 'https://www.redhat.com/wapps/sso/login.html'
    rhnpkg = 'https://rhn.redhat.com/rhn/software/packages/details/Overview.do?pid='
    tmppath = '/tmp/'
    rhnbr = ''
    rhndb = ''
    pkgsrc = 0
    pkgdbg = 0

    def __init__(self, rhnuser, rhnpwd, dbhost, dbname, dbuser, dbpwd):
        """ Init class with RHN credentials """

        self.rhndb = rhndb.RHNdb(dbhost, dbname, dbuser, dbpwd)
        self.loginrhn(rhnuser, rhnpwd)

    def loginrhn(self, rhnuser, rhnpwd):
        """ Login to RHN """
        self.rhnbr = mechanize.Browser()
        try:
            self.rhnbr.open(self.rhnurl)
            self.rhnbr.select_form(nr=0)
            self.rhnbr.form['username'] = rhnuser
            self.rhnbr.form['password'] = rhnpwd
            self.rhnbr.submit()
        except:
            msg = "*ERROR* : Unable to fetch %s" % (self.rhnurl)
            sys.exit(msg)

    def get_package_id(self, name, ver, rel, arch):
        """ Get package id from database """

        packages = self.rhndb.get_package_id(name, ver, rel, arch)
        if not packages:
            msg = '*ERROR*: Package %s-%s-%s-%s not found in DB' % (name, ver,
                                                                    rel, arch)
            sys.exit(msg)
        return packages

    def get_errata_pkg_id(self, errata):
        """ Get packages from an errata in database """

        errataid = self.rhndb.get_errata_pkg_id(errata)
        if not errataid:
            msg = '*ERROR*: Errata %s not found in DB' % (errata)
            sys.exit(msg)
        return errataid

    def get_filename(self, fileurl):
        """ Parse filename from URL"""

        regex = r"NULL/([\dA-Za-z_\.-]+)/([\dA-Za-z_\.-]+)/([\dA-Za-z_\.-]+)/([\dA-Za-z_\.-]+)"
        data = re.search(regex, fileurl)
        if not data:
            msg = "*ERROR* Parsing fileurl: %s" % (fileurl)
            sys.exit(msg)
        return data.group(4)

    def download_rpm(self, fileurl):
        """ Download RPM file """

        pkgname = self.get_filename(fileurl)
        if not os.path.isfile(self.tmppath + pkgname):
            try:
                data = self.rhnbr.open(fileurl)
                fil = open(self.tmppath + pkgname, 'w')
                fil.write(data.read())
                fil.close()
                print "File downloaded: %s" % (self.tmppath + pkgname)
            except Exception, err:
                msg = '*ERROR* Downloading %s' % (fileurl)
                print err
                sys.exit(msg)
        else:
            print "File already downloaded: %s" % (self.tmppath + pkgname)

    def get_package_url(self, pkgid):
        """ Get package URL """

        url = self.rhnpkg + str(pkgid)
        try:
            data = self.rhnbr.open(url)
            html = data.read()
            regex = r"https://content-web.rhn.redhat.com/rhn/public/NULL/(\S+)rpm"
            data = re.compile(regex, re.MULTILINE)
            rpms = data.finditer(html)
            for rpm in rpms:
                fileurl = rpm.group(0)
                if (not self.pkgsrc and ('SRPMS' in fileurl)):
                    #print "SRPMS -> Not Downloaded"
                    test = 1
                elif (not self.pkgdbg and ('debuginfo' in fileurl)):
                    #print "DEBUGINFO -> Not Downloaded"
                    test = 1
                else:
                    self.download_rpm(fileurl)
        except Exception, err:
            msg = '*ERROR*: Unable to open url package: %s' % (url)
            print err
            sys.exit(msg)

    def get_package(self, pkgname, pkgver, pkgrel, pkgarch, pkgdbg, pkgsrc):
        """ Parse package """

        if len(pkgdbg):
            self.pkgdbg = int(pkgdbg[0])
        if len(pkgsrc):
            self.pkgsrc = int(pkgsrc[0])
        if not pkgrel:
            pkgrel = '%'
        else:
            pkgrel = pkgrel[0]
        if not pkgarch:
            pkgarch = '%'
        else:
            pkgarch = pkgarch[0]
        pkgids = self.get_package_id(pkgname[0], pkgver[0], pkgrel, pkgarch)
        for pkgid in pkgids:
            self.get_package_url(pkgid['package_id'])

    def get_errata(self, errata):
        """ Parse errata """
        pkgids = self.get_errata_pkg_id(errata[0])
        for pkgid in pkgids:
            pkgsupported =  self.rhndb.get_package(pkgid['package_id'])
            if pkgsupported:
                self.get_package_url(pkgid['package_id'])
