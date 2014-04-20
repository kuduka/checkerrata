#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
    GPL BLAH BLAH BLAH

    Let's fill our database with RHN info!

    By default we only support RHEL[56] and i386/x86_64 (02/12/2013)

"""

import rhnapi
import rhndb
import sys
import ConfigParser
import os
import datetime
import hashlib
import xmlrpclib
import psycopg2

#TODO: check_eof_channels && update_channels -> child labels eof if parent eof?
#TODO: update_erratas case2 if needed
#TODO: update_packages case2 if needed
#TODO: EOL -> string to datetime
#TODO: socket.error: [Errno 111] Connection refused --> Fix 10 retries


class RHNclone(object):
    """ Clone RHN database locally """

    inisyncdate = '19800101'
    rhndb = ''
    rhnapi = ''

    def __init__(self, rhnuser, rhnpwd, dbhost, dbname, dbuser, dbpwd):
        """ Init class and define DB/RHN connection"""

        self.rhndb =  rhndb.RHNdb(dbhost, dbname, dbuser, dbpwd)
        self.rhnapi = rhnapi.RHNapi(rhnuser, rhnpwd)
        self.rhnapi.login()

    def check_eof_channels(self):
        """ Set unsupported channels if EOF is <= now(). """

        channels = self.rhndb.get_all_supported_channels()
        now = datetime.datetime.utcnow()
        supported = False
        for chan in channels:
            eol = chan['channel_end_of_life']
            channel = chan['channel_label']
            if (eol and eol <= now):
                self.rhndb.update_eof_channels(supported, channel)

    def update_channels(self):
        """
            Update all channels in database:
            Case 1) New channel and check if it's supported or not
            Case 2) Channel already exists in db and supported but eof changed
        """
        supported = True
        channels = self.rhnapi.get_channels()
        now = datetime.datetime.utcnow()
        for chan in channels:
            channel = chan['channel_label']
            name = chan['channel_name']
            parent = chan['channel_parent_label']
            arch = chan['channel_arch']
            eol =  chan['channel_end_of_life']
            if not eol:
                eol = None
            dbchannel = self.rhndb.get_channel(channel)
            if not dbchannel: #Update channel if does not exist
                #if (eol and eol <= now):
                #    supported = False
                self.rhndb.insert_channel(channel, name, parent,
                                eol, arch, self.inisyncdate,
                                self.inisyncdate, supported)
            else: #channel in db
                dbeol = dbchannel['channel_end_of_life']
                dbsupported = dbchannel['channel_supported']
                if (dbsupported and dbeol != eol): #only supported channels
                    if (eol and eol <= now):
                        supported = False
                    elif (eol and eol > now):
                        supported = True
                    else: #this should never happen!
                        msgerr = "*ERROR* Channel: %s new eol: %s" % (channel,
                                                                        eol)
                        sys.exit(msgerr)
                    self.rhndb.update_channel(supported, eol, channel)
        self.rhndb.set_unsupported_channels()

    def update_errata_packages(self, advisory):
        """
            Update errata packages from errata advisory:
            Case1) bugzilla errata packages doesn't exist
            Case2) bugzilla errata packages already exists
        """
        packages = self.rhnapi.get_erratas_packages(advisory)
        if packages:
            for pkg in packages:
                pid = pkg['package_id']
                dberrpkg = self.rhndb.get_errata_package(advisory, int(pid))
                if not dberrpkg:
                    self.rhndb.insert_errata_package(advisory, int(pid))

    def update_bugzilla(self, advisory):
        """
            Update bugzillas for a errata adivsory:
            Case1) Bugzilla doesn't exist
            Case2) Bugzilla already exists
        """

        bugzillas = self.rhnapi.get_bugzillas(advisory)
        for bgz in bugzillas:
            bugzilla = bgz
            bsumm = bugzillas[bgz].encode("utf-8")
            dbbugzilla = self.rhndb.get_bugzilla(int(bugzilla))
            if not dbbugzilla:
                self.rhndb.insert_bugzilla(int(bgz), bsumm)
            dberrbug = self.rhndb.get_errata_bugzilla_advisory(int(bugzilla), advisory)
            if not dberrbug:
                self.rhndb.insert_errata_bugzilla(advisory, int(bgz))
            self.update_errata_packages(advisory)

    def update_erratas(self):
        """
            Update erratas from all supported channels:
            Case1) Errata doesn't exist
            Case2) Errata already exists but mdate has been changed
        """

        channels = self.rhndb.get_all_supported_channels()
        for chan in channels:
            channel = chan['channel_label']
            sync = chan['channel_sync_erratas']
            sync = sync - datetime.timedelta(days=3)
            print "Erratas -> %s - %s" % (channel, sync.strftime("%Y%m%d"))
            erratas = self.rhnapi.get_erratas(channel, sync.strftime("%Y%m%d"))
            for err in erratas:
                advisory = err['errata_advisory']
                idate = err['errata_issue_date']
                udate = err['errata_update_date']
                synopsis = err['errata_synopsis']
                advtype = err['errata_advisory_type']
                mdate = err['errata_last_modified_date']
                dbadvisory = self.rhndb.get_errata(advisory)
                if not dbadvisory:
                    self.rhndb.insert_errata(advisory, idate, udate,
                                            synopsis, advtype, mdate)
                #else:
                #    mdate = datetime.datetime.strptime(mdate,
                #                                       '%Y-%m-%d %H:%M:%S')
                #    dbmdate = dbadvisory['errata_last_modified_date']
                #    dseconds = mdate - dbmdate
                #    if	dseconds.total_seconds() > 600:
                #        print "ERRATA HAS BEEN MODIFIED: %s - %d" % (advisory,
                #                                                   dseconds)
                dberrchnl = self.rhndb.get_errata_channel(advisory, channel)
                if not dberrchnl:
                    self.rhndb.insert_errata_channel(advisory, channel)
                self.update_bugzilla(advisory)
            self.rhndb.update_sync_erratas(channel)

    def update_files(self, pid):
        """
            Update all files from a package
            Case1: package_file doesn' exist
        """
        files = self.rhnapi.get_files(pid)
        for fil in files:
            fpath = fil['file_path']
            ftype = fil['file_type']
            fmod = fil['file_last_modified_date']
            fmd5 = fil['file_md5sum']
            fchk = fil['file_checksum']
            fsiz = fil['file_size']
            flnk = fil['file_linkto']
            sha = hashlib.sha256()
            sha.update(str(pid))
            sha.update(fpath)
            sha.update(ftype)
            sha.update(fmod)
            sha.update(fmd5)
            sha.update(fchk)
            sha.update(str(fsiz))
            sha.update(flnk)
            digest = sha.hexdigest()
            dbfil = self.rhndb.get_package_file(digest)
            if not dbfil:
                self.rhndb.insert_package_files(digest, pid, fpath, ftype, fmod, fmd5, fchk, fsiz, flnk)

    def update_changelog(self, pid):
        """
            Update changelog for a package
            Case1) changelog doesn't exist as we don't have PK
        """

        chglogs = self.rhnapi.get_changelogs(pid)
        if chglogs:
            for chg in chglogs:
                auth = chg['entry_author']
                date = chg['entry_date']
                txt = chg['entry_text']
                sha = hashlib.sha256()
                sha.update(str(pid))
                sha.update(auth.encode('utf-8'))
                sha.update(date)
                sha.update(txt.encode('utf-8'))
                digest = sha.hexdigest()
                dbchg = self.rhndb.get_package_change(digest)
                if not dbchg:
                    self.rhndb.insert_package_change(digest, pid, auth, date, txt)

    def update_latest_packages(self, channel):
        """
            Update latest packages in a channel
            Case1) Just set them to true
        """

        latest = self.rhnapi.get_latest_packages(channel)
        self.rhndb.set_all_packages_channel_latest(channel)

        for lat in latest:
            pid = lat['package_id']
            self.rhndb.set_package_channel_latest(int(pid), channel)

    def update_packages(self):
        """
            Update packages from all supported channels
            Case1) Package doesn't exist
            Case2) package already exists but pmod has been changed
        """
        channels = self.rhndb.get_all_supported_channels()
        for chan in channels:
            channel = chan['channel_label']
            sync = chan['channel_sync_packages']
            sync = sync - datetime.timedelta(days=3)
            print "Packages -> %s - %s" % (channel,
                                            sync.strftime("%Y%m%d"))
            packages = self.rhnapi.get_packages(channel,
                                            sync.strftime("%Y%m%d"))
            for pkg in packages:
                pname = pkg['package_name']
                pver = pkg['package_version']
                prel = pkg['package_release']
                pepoch = pkg['package_epoch']
                pid = pkg['package_id']
                parch = pkg['package_arch_label']
                pmod = pkg['package_last_modified']
                dbpkg = self.rhndb.get_package(int(pid))
                if not dbpkg:
                    self.rhndb.insert_package(int(pid), pname, pver, prel,
                                                pepoch, parch, pmod)
                dbpkgchan = self.rhndb.get_package_channel(int(pid), channel)
                if not dbpkgchan:
                    self.rhndb.insert_package_channel(int(pid), channel)
                self.update_changelog(int(pid))
                if pname == "kernel" or pname == "kernel-PAE" or pname == "kernel-xen" :
                    self.update_files(int(pid))
            self.update_latest_packages(channel)
            self.rhndb.update_sync_packages(channel)

################ MAIN ###################

config = ConfigParser.RawConfigParser()
try:
    config.read(os.path.expanduser('~/.checkerrata'))
    USER = config.get('checkerrata','USER')
    PWD = config.get('checkerrata','PWD')
    URL = config.get('checkerrata','URL')
    DBUSER = config.get('checkerrata','DBUSER')
    DBPWD = config.get('checkerrata','DBPWD')
    DBDATABASE = config.get('checkerrata','DBDATABASE')
    DBHOST = config.get('checkerrata','DBHOST')
except ConfigParser.Error:
    sys.exit('*ERROR* reading config file: $HOME/.checkerrata!')


try:
    news = RHNclone(USER, PWD, DBHOST, DBDATABASE, DBUSER, DBPWD)
    news.update_channels()
    news.check_eof_channels()
    news.update_packages()
    news.update_erratas()

except xmlrpclib.Fault, fault:
    if fault.faultCode == -2:
        msg = '*ERROR* User/pwd not OK'
        sys.exit(msg)

except psycopg2.DatabaseError, dberr:
    msg = '*Error* DatabaseError %s' % dberr
    sys.exit(msg)
