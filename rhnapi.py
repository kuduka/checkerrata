#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
    GPL INFO BLAH BLAH
"""

import xmlrpclib
import sys
import errno
from socket import error as socket_error

class RHNapi(object):
    """ RHN API in order to interact with RHN """

    apiurl = ''
    apiuser = ''
    apipwd  = ''
    apikey = ''
    errors = 0
    maxerrors = 100
    channels_cache = {}
    packages_cache = {}
    erratas_cache = {}
    changelogs_cache = {}
    latest_packages_cache = {}

    def __init__(self, user, pwd, url = 'https://rhn.redhat.com/rpc/api'):
        """ Init class with RHN api per defautl."""

        self.apiurl = url
        self.apiuser = user
        self.apipwd = pwd
        self.apiserver = xmlrpclib.Server(self.apiurl)

    def login(self):
        """ Login to RHN. """

        try:
            if self.errors <= self.maxerrors:
                key = self.apiserver.auth.login(self.apiuser, self.apipwd)
                self.apikey = key
                self.errors = self.errors + 1
                return 0
            else:
                sys.exit('*ERROR*: Too many logins failed to RHN')
        except xmlrpclib.Fault:
            raise

    def get_channels(self):
        """ Get all channels in RHN. """

        if(len(self.channels_cache)):
            return self.channels_cache
        try:
            channels = self.apiserver.channel.listSoftwareChannels(self.apikey)
            #self.channels_cache = channels
            return channels
        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_channels()

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_channels()
            else:
                raise

    def get_packages(self, channel, date = '19800101'):
        """ Get all packages from a channel. """

        if(self.packages_cache.has_key(channel)):
            return self.packages_cache[channel]
        try:
            packages = self.apiserver.channel.software.listAllPackages(
                            self.apikey, channel, date)
            #self.packages_cache[channel] = packages
            return packages
        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_packages(channel)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_packages(channel)
            else:
                raise

    def get_erratas(self, channel, date = '19800101'):
        """ Get erratas from a channel from date. """

        if(self.erratas_cache.has_key(channel)):
            return self.erratas_cache[channel]
        try:
            erratas =  self.apiserver.channel.software.listErrata(
                        self.apikey, channel, date)
            #self.erratas_cache[channel] = erratas
            return erratas
        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_erratas(channel, date)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_erratas(channel, date)
            else:
                raise

    def get_bugzillas(self, errata):
        """ Get all bugzilla from an advisory errata. """

        try:
            bugzillas = self.apiserver.errata.bugzillaFixes(self.apikey,
                                                            errata)
            return bugzillas

        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_bugzillas(errata)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_bugzillas(errata)
            else:
                raise

    def get_changelogs(self, packageid):
        """ Get all changelogs in a package. """

        if (self.changelogs_cache.has_key(str(packageid))):
            return self.changelogs_cache[str(packageid)]
        try:
            changelogs = self.apiserver.packages.listChangelog(self.apikey,
                                                            int(packageid))
            return changelogs
        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_changelogs(packageid)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_changelogs(packageid)
            else:
                raise

    def get_files(self, packageid):
        """ Get all files in a package. """

        try:
            files = self.apiserver.packages.listFiles(self.apikey,
                                                    int(packageid))
            return files

        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_files(packageid)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_files(packageid)
            else:
                raise

    def get_erratas_packages(self, errata):
        """ Get packages affected for an errata advisory. """

        try:
            packages = self.apiserver.errata.listPackages(self.apikey, errata)
            return packages

        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_erratas_packages(errata)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_erratas_packages(errata)
            else:
                raise

    def get_latest_packages(self, channel):
        """ Get latest packages from a channel. """

        if(self.latest_packages_cache.has_key(channel)):
            return self.latest_packages_cache.has_key(channel)
        try:
            packages = self.apiserver.channel.software.listLatestPackages(
                                                    self.apikey, channel)
            #self.latest_packages_cache[channel] = packages
            return packages
        except socket_error as serr:
            if serr.errno == errno.ECONNREFUSED:
                self.login()
                return self.get_latest_packages(packages)

        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_latest_packages(packages)
            else:
                raise

    def get_childs_channel(self, channel):
        """ Get all child channels for a channel. """

        childs = []
        channels = self.get_channels()
        for chan in channels:
            if chan['channel_parent_label'] == channel :
                childs.append(chan['channel_label'])
        return childs

    def get_base_channels(self):
        """ Get all base channels. """

        base = []
        try:
            channels = self.apiserver.channel.listSoftwareChannels(self.apikey)
            for chan in channels:
                if not chan['channel_parent_label']:
                    base.append(chan['channel_label'])
            return base
        except xmlrpclib.Fault, fault:
            if fault.faultCode == -20:
                self.login()
                return self.get_channels()
            else:
                raise
