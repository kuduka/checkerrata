#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
    BLAH BLAH GPL
    https://github.com/pybliss/rhscheck/blob/master/rhscheck.py
    https://github.com/ssato/sos-analyzer

"""

import argparse
import sys
import os
import re
from rpmUtils.miscutils import compareEVR
import ConfigParser
import rhndb

#TODO: detect kernel type --> PAE, xen or normal
#TODO: check latest kernel installed and get RHSA about the latest one

# IMPROVMENTS:
# - zstream channels not supported by design, also not enabled in rhnclone

class SOScheck(object):
    """ Class for checking sos reports"""

    sosfile = ''
    rhndb = ''
    rhelarch = ''
    rhelver = 0
    rhelkernel = ''
    rhelflavour = ''
    rhelbchan = ''
    rhelchilds = []
    rhelpackages = []
    rhelpkgsupported = []
    rhelpkgunsupported = []
    rhelpkgold = []
    rhelpkgupdates = []
    rhelmod = []

    def __init__(self, sosfile, dbuser, dbpwd, dbname, dbhost):
        """ Init variables """

        self.sosfile = sosfile
        self.rhndb =  rhndb.RHNdb(dbhost, dbname, dbuser, dbpwd)

    def get_file_sos(self, fname):
        """ Get file contents from sosreport. """

        pfile = self.sosfile + "/" + fname
        try:
            pfile = self.sosfile + "/" + fname
            fil = open(pfile,'r')
            content = fil.read()
            fil.close()
            return content
        except Exception, err:
            msg = '*ERROR*: Unable to read: %s ' % (pfile)
            print err
            sys.exit(msg)

    def get_kernel_tainted(self):
        """ Get if kernel has been tainted """
        tainted = self.get_file_sos('proc/sys/kernel/tainted')
        print "-------------------------------------------------------------------------"
        print " KERNEL TAINTED "
        print "-------------------------------------------------------------------------"
        tainted =tainted.strip()
        if tainted == "0":
            print "Kernel is not tainted"
        elif tainted == "1":
            print "All modules loaded have a GPL or compatible license or any proprietary module has been loaded"
        elif tainted == "2":
            print "Any module was force loaded by insmod -f"
        elif tainted == "3":
            print "SMP kernel running on hardware that hasn't been certified as safe to run multiprocessor"
        elif tainted == "4":
            print "Module was force unloaded by rmmod -f"
        elif tainted == "5":
            print "Any processor has reported a Machine Check Exception"
        elif tainted == "6":
            print "Page-release function has found a bad page reference or some unexpected page flags"
        elif tainted == "7":
            print "A user or user application specifically requested that the Tainted flag be set"
        elif tainted == "8":
            print "Kernel has died recently, i.e. there was an OOPS or BUG"
        elif tainted == "9":
            print "ACPI table has been overridden"
        elif tainted == "10":
            print "A warning has previously been issued by the kernel"
        elif tainted == "12":
            print "Kernel is working around a severe bug in the platform firmware"
        elif tainted == "29":
            print "Hardware is unsupported by the distribution"
        else:
            print "Unknown tainted kernel value"

    def get_kernel_sos(self):
        """ Get kernel version from uname in sosreport """

        uname = self.get_file_sos('uname')
        regex = re.compile(r"^Linux (\S+) (\S+) #", re.MULTILINE)
        if regex.search(uname):
            return regex.search(uname).group(2)
        sys.exit('*ERROR*: Kernel not supported: %s ' % uname)

    def get_arch(self):
        """ Get arch. """

        uname = self.get_file_sos('uname')
        pattern = ['i386','x86_64']
        for pat in pattern:
            if re.search(pat, uname):
                self.rhelarch = pat
                return self.rhelarch

        msg = '*ERROR*: arch not supported: %s ' % (uname)
        sys.exit(msg)

    def get_release(self):
        """ Get release from sosreport """

        release = self.get_file_sos('etc/redhat-release')
        regex5 = r"Red Hat Enterprise Linux\s+(\S+)\s+release 5.*\(Tikanga\)"
        regex6 = r"Red Hat Enterprise Linux\s+(\S+)\s+release 6.*\(Santiago\)"
        regex7 = r"Red Hat Enterprise Linux\s+(\S+)\s+release 7.*\(Maipo\)"
        data = re.compile(regex5)
        if (data.search(release)):
            self.rhelver = 5
            return self.rhelver
        data = re.compile(regex6)
        if (data.search(release)):
            self.rhelver = 6
            return self.rhelver
        data = re.compile(regex7)
        if (data.search(release)):
            self.rhelver = 7
            return self.rhelver
        sys.exit("*ERROR*: Release not found: %s" % release)

    def get_flavour(self):
        """ Get flavour from sosreport """

        release = self.get_file_sos('etc/redhat-release')
        regex = r"Red Hat Enterprise Linux\s+(\S+)"
        data = re.compile(regex)
        if data.search(release):
            self.rhelflavour = data.search(release).group(1).lower()
            return self.rhelflavour
        sys.exit("*ERROR*: Unable to get flavour: %s" % release)

    def get_kernel(self):
        """ Get kernel from sosreport. """

        kver = self.get_kernel_sos()
        self.rhelkernel = kver
        return self.rhelkernel

    def get_base_channel(self):
        """ Get base channel from sosreport:
             rhel-<arch>-<flavour>-<relase>
             rhel-i386-server-6
             rhel-x86_64-server-6
             rhel-i386-server-5
             rhel-x86_64-server-5
        """

        bchan = 'rhel-%s-%s-%s' % (self.rhelarch, self.rhelflavour, self.rhelver)
        channel = self.rhndb.get_channel_supported(bchan)
        if channel:
            self.rhelbchan = channel
            return self.rhelbchan
        else:
            sys.exit("*ERROR*: Base channel is not in our DB or not supported: %s" % bchan)

    def get_installed_rpms(self):
        """ get installed rpms"""

        listrpm = []
        rpms = open(self.sosfile + "/installed-rpms",'r')
        for r in rpms:
            regex = r"^(.*)-(.*)-(.*)[\.-](\S+)\s+.*$"
            data = re.compile(regex)
            package = data.match(r)
            if package:
                dpackage = {}
                dpackage['package_name'] = package.group(1)
                dpackage['package_version'] = package.group(2)
                dpackage['package_release'] = package.group(3)
                dpackage['package_arch_label'] = package.group(4)
                listrpm.append(dpackage)
            else:
                if (len(r)>1):
                    sys.exit("*ERROR*: Unable to parse package: %s" % r)
        rpms.close()
        self.rhelpackages = listrpm
        return self.rhelpackages

    def get_loaded_modules(self):
        """ get loaded modules in kernel """

        listmod = []
        modules = self.get_file_sos('lsmod')
        regex = r"^(\S+)\s+\d+"
        data = re.compile(regex, re.MULTILINE)
        for m in data.findall(modules):
            if m != 'Module':
                exceptions = ['i2c_piix4','i2c_core','crc_t10dif','dm_mirror',
                               'dm_region_hash','dm_log','dm_mod','ide_cd','dm_raid45',
                               'dm_message','dell_wmi','uhci_hcd','ohci_hcd','ehci_hcd',
                               'dm_multipath','dm_mem_cache','acpi_cpufreq','i2c_i801',
                               'snd_hda_codec_hdmi','snd_hda_codec_realtek',
                               'snd_hda_intel','snd_hda_codec','snd_hwdep','snd_seq',
                               'snd_seq_device','snd_pcm','snd_timer','snd_page_alloc',
                               'aesni_intel','dm_crypt','sdhci_pci','xhci_hcd',
                               'i2c_algo_bit']
                if m in exceptions:
                    m = m.replace('_','-')
                if m == 'dm-region-hash' and self.rhelver == 5:
                    m = 'dm-region_hash'
                listmod.append(m)
        self.rhelmod = listmod

    def get_child_channels(self):
        """ get all child channels from basechannel """

        listchan = self.rhndb.get_child_channels(self.rhelbchan['channel_label'])
        self.rhelchilds = listchan
        return self.rhelchilds

    def get_latest_packages(self):
        """ get latest packages from base channel and childs """

        supported = self.rhndb.get_latest_packages_channel(self.rhelbchan['channel_label'])
        for cc in self.rhelchilds:
            csupported = self.rhndb.get_latest_packages_channel(cc['channel_label'])
            for p in csupported:
                supported.append(p)
        self.rhelpkgsupported = supported
        return self.rhelpkgsupported

    def get_unsupported_rpms(self):
        """ get unsupported rpms """

        listrpms = []
        for p in self.rhelpackages:
            supported = False
            pname = p['package_name']
            for ps in self.rhelpkgsupported:
                if pname == ps['package_name']:
                    supported = True
                    break
            if supported == False:
                listrpms.append(p)

        self.rhelpkgunsupported = listrpms

        print "-------------------------------------------------------------------------"
        print " Unsupported RPMS "
        print "-------------------------------------------------------------------------"
        for l in listrpms:
            print "%s-%s-%s-%s" % (l['package_name'], l['package_version'], l['package_release'], l['package_arch_label'])

    def get_old_rpms(self):
        """ get olds rpms """

        listrpms = []
        for p in self.rhelpackages:
            updated = False
            pname = p['package_name']
            pver = p['package_version']
            prel = p['package_release']

            for ps in self.rhelpkgsupported:
                psname = ps['package_name']
                psver = ps['package_version']
                psrel = ps['package_release']
                if (pname == psname and pver == psver and prel == psrel):
                    updated = True
                    break

            if updated == False:
                supported = True
                for u in self.rhelpkgunsupported:
                    if u['package_name'] == pname:
                        supported = False
                        break
                if supported == True:
                    listrpms.append(p)

        self.rhelpkgold = listrpms

    def get_new_rpms(self):
        """ List new packages for package """

        listrpm = []
        allrpms = []
        allrpms = self.rhndb.get_all_packages_channel(self.rhelbchan['channel_label'])
        for cc in self.rhelchilds:
            childrpms = self.rhndb.get_latest_packages_channel(cc['channel_label'])
            for rpm in childrpms:
                allrpms.append(rpm)

        for pkg1 in self.rhelpkgold:
            for pkg2 in allrpms:
                p1name = pkg1['package_name']
                p2name = pkg2['package_name']
                p1arch = pkg1['package_arch_label']
                p2arch = pkg2['package_arch_label']
                if (p1name == p2name and p1arch == p2arch):
                    if self.package_newer(pkg1, pkg2) == True:
                        listrpm.append(pkg2)
        self.rhelpkgupdates = listrpm

    def package_newer(self, pkg1, pkg2):
        """ Compare if a pkg1 is newer than pkg2 """

        listrpm = []
        n1 = pkg1['package_name']
        n2 = pkg2['package_name']

        if n1 != n2:
            sys.exit("*ERROR* Unable to compare packages with different name %s - %s" % (n1, n2))

        # we need to get pkg1 from database as we don't have his package_epoch (not listed in rpm -qa)
        pkgid = self.rhndb.get_package_id(pkg1['package_name'],
                    pkg1['package_version'], pkg1['package_release'],
                    pkg1['package_arch_label'])
        if not pkgid:
            sys.exit("*ERROR* Unable to find package in our DB: %s" % (n1))
        pkg1 = self.rhndb.get_package(pkgid[0]['package_id'])

        e1 = pkg1['package_epoch']
        v1 = pkg1['package_version']
        r1 = pkg1['package_release']
        e2 = pkg2['package_epoch']
        v2 = pkg2['package_version']
        r2 = pkg2['package_release']
        if compareEVR((e1, v1, r1), (e2, v2, r2)) == -1:
            return True
        return False

    def get_erratas(self):
        """ get erratas for new packages """

        print "-------------------------------------------------------------------------"
        print " PACKAGES TO UPGRADE"
        print "-------------------------------------------------------------------------"
        for rpm in self.rhelpkgupdates:
            print "-------------------------------------------------------------------------"
            print "%s-%s-%s-%s    (%s)" % (rpm['package_name'], rpm['package_version'], rpm['package_release'], rpm['package_arch_label'],
            rpm['package_id'])
            print "-------------------------------------------------------------------------"
            pkgid = rpm['package_id']
            erratas = self.rhndb.get_errata_per_package(pkgid)
            for e in erratas:
                print e['errata_advisory']
                errbugzillas = self.rhndb.get_errata_bugzilla(e['errata_advisory'])
                for errbg in errbugzillas:
                    bugzilla = self.rhndb.get_bugzilla(errbg['bugzilla_id'])
                    print "\t" + bugzilla['bug_summary']

    def get_unsupported_modules(self):
        """ Get unsupported kernel modules """

        kmods = []
        kernels = self.rhndb.get_all_kernels()

        #TODO KERNEL PAE + XEN
        if self.rhelver == 5:
            if self.rhelarch == "i386":
                findkernel = 'kernel-' + self.rhelkernel + '.i686'
            else:
                findkernel = 'kernel-' + self.rhelkernel + '.' + self.rhelarch
        else:
            findkernel = 'kernel-' + self.rhelkernel
        found = 0
        for k in kernels:
            if k['kernel'] == findkernel:
                found = 1
                files = self.rhndb.get_package_file_package(k['package_id'])
                for f in files:
                    fpath =  f['file_path']
                    pattern=r"^/lib/modules/(.*)/(\S+)\.k?o$"
                    if re.compile(pattern).search(fpath):
                        kmods.append(re.compile(pattern).search(fpath).group(2))
                break
        print "-------------------------------------------------------------------------"
        print " UNSUPPORTED MODULES "
        print "-------------------------------------------------------------------------"
        if found != 1:
            print "*ERROR*: Kernel %s not found" % findkernel
        else:
            for i in self.rhelmod:
                if i not in kmods:
                    print i

    #def get_xsos(self):
    #    """ Print xsos data """
    #    print "-------------------------------------------------------------------------"
    #    print " XSOS "
    #    print "-------------------------------------------------------------------------"
    #    command = './xsos-direct -a ' + self.sosfile
    #    os.system(command)

    def get_all(self):
        """ Get all. """

        self.get_arch()
        self.get_kernel()
        self.get_release()
        self.get_kernel_tainted()
        self.get_loaded_modules()
        self.get_unsupported_modules()
        self.get_flavour()
        self.get_base_channel()
        self.get_child_channels()
        self.get_latest_packages()
        self.get_installed_rpms()
        self.get_unsupported_rpms()
        self.get_old_rpms()
        self.get_new_rpms()
        self.get_erratas()
        #self.get_xsos()

if __name__ == "__main__":

    config = ConfigParser.RawConfigParser()
    try:
        config.read(os.path.expanduser('~/.checkerrata'))
        DBUSER = config.get('checkerrata','DBUSER')
        DBPWD = config.get('checkerrata','DBPWD')
        DBDATABASE = config.get('checkerrata','DBDATABASE')
        DBHOST = config.get('checkerrata','DBHOST')
    except ConfigParser.Error:
        sys.exit('*ERROR* reading config file: $HOME/.checkerrata!')

    par = argparse.ArgumentParser(description = 'SOScheck from a SOSreport')
    par.add_argument('-s', '--sosreport', nargs = 1, required = 1,
                        help = 'sosreport directory path')
    opts = par.parse_args()
    test = SOScheck(opts.sosreport[0], DBUSER, DBPWD, DBDATABASE, DBHOST)
    test.get_all()
