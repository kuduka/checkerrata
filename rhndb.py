#!/usr/bin/python
"""
    BLAH BLAH GPL

"""

import psycopg2
import psycopg2.extras
import datetime

class RHNdb(object):
    """ Class for interactions with our DB """

    con =  ''
    cursor = ''

    def __init__(self, host, dbname, user, pwd):
        """ DSN and connect to the database """

        dsn = 'host=%s dbname=%s user=%s password=%s' % (host, dbname,
                                                        user, pwd)
        self.con = psycopg2.connect(dsn)
        self.cursor = self.con.cursor(
                        #cursor_factory = psycopg2.extras.DictCursor)
                        cursor_factory = psycopg2.extras.RealDictCursor)

    def get_package_id(self, name, ver, rel, arch):
        """ Get package id from database """

        self.cursor.execute('''select package_id from packages
                            where package_name = %s
                            and package_version = %s
                            and package_release like %s
                            and package_arch_label like %s ''', (name, ver,
                                                            rel, arch))
        return self.cursor.fetchall()

    def get_errata_pkg_id(self, errata):
        """ Get packages in errata from database """

        self.cursor.execute('''select package_id from erratas_packages
                            where errata_advisory = %s ''', (errata,))
        return self.cursor.fetchall()

    def get_package(self, pkgid):
        """ Get package if exists from database """

        self.cursor.execute('''select * from packages
                                where package_id = %s''', (pkgid,))
        return self.cursor.fetchone()

    def set_unsupported_channels(self):
        """
            Set unsupported debuginfo and beta channels,
            supported arch base channels: i386 && x86_64

            rhel-i386-server-6
            rhel-x86_64-server-6
            rhel-i386-server-5
            rhel-x86_64-server-5
            ...
        """

        self.cursor.execute('''update channels set channel_supported = False
                                where (channel_label like '%-beta'
                                or channel_label like '%-4-%'
                                or channel_label like '%-4'
                                or channel_label like '%.z'
                                or channel_label like '%.z-%'
                                or channel_label like '%-els'
                                or channel_label like '%-debuginfo'
                                or channel_label like '%-s390'
                                or channel_label like '%-s390x'
                                or channel_label like '%-ia64'
                                or channel_label like '%-s390x-%'
                                or channel_label like '%-ppc-%'
                                or channel_label like '%-ia64-%')''')
        self.con.commit()

    def get_all_kernels(self):
        """ Get all supported kernels """

        self.cursor.execute('''select package_name || '-' || package_version || '-' ||
                           package_release || '.' || package_arch_label as kernel,
                           package_id from packages
                           where package_name = 'kernel'
                           or package_name = 'kernel-PAE'
                           or package_name = 'kernel-xen' ''')
        return self.cursor.fetchall()

    def get_all_supported_channels(self):
        """ Get all supported channels from database. """

        self.cursor.execute('''select * from channels
                            where channel_supported = True''')
        return self.cursor.fetchall()

    def get_errata(self, advisory):
        """ Get an errata from database. """

        self.cursor.execute('''select * from erratas
                            where errata_advisory = %s''',
                            (advisory,))
        return self.cursor.fetchone()

    def get_errata_channel(self, advisory, channel):
        """ Get an errata that belongs to a channel from database. """

        self.cursor.execute('''select * from erratas_channel
                                where errata_advisory = %s
                                and channel_label = %s''',
                                (advisory, channel))
        return self.cursor.fetchone()

    def get_package_channel(self, pid, channel):
        """ Get a package in a channel from database. """

        self.cursor.execute('''select * from packages_channel
                                where package_id = %s
                                and channel_label = %s''',
                                (pid, channel))
        return self.cursor.fetchone()

    def get_all_packages_channel(self, channel):
        """ Get all packages from a channel """

        self.cursor.execute('''select p.package_id,package_name,package_version,
                package_release,package_epoch,package_arch_label,package_last_modified
                from packages as p, packages_channel as pc
                where channel_label = %s
                and p.package_id = pc.package_id''',(channel,))
        return self.cursor.fetchall()

    def get_channel(self, channel):
        """ Get a channel from database. """

        self.cursor.execute('''select * from channels
                                where channel_label = %s''',
                            (channel,))
        return self.cursor.fetchone()

    def get_channel_supported(self, channel):
        """ Get a supported channel from database. """

        self.cursor.execute('''select * from channels
                                where channel_label = %s
                                and channel_supported = True''',
                            (channel,))
        return self.cursor.fetchone()

    def get_bugzilla(self, bugzilla):
        """ Get a bugzilla from database. """

        self.cursor.execute('''select * from bugzilla
                                where bugzilla_id = %s''',
                                (bugzilla,))
        return self.cursor.fetchone()

    def get_errata_bugzilla_advisory(self, bugzilla, advisory):
        """ Get a erratas bugzilla from database. """

        self.cursor.execute('''select * from erratas_bugzilla
                                where bugzilla_id = %s
                                and errata_advisory = %s''',
                                (bugzilla, advisory))
        return self.cursor.fetchone()

    def get_errata_bugzilla(self, advisory):
        """ Get a erratas bugzilla from database. """

        self.cursor.execute('''select * from erratas_bugzilla
                                where errata_advisory = %s''',
                                (advisory,))
        return self.cursor.fetchall()


    def get_errata_package(self, advisory, pid):
        """ Get an errata package from database. """

        self.cursor.execute('''select * from erratas_packages
                                where package_id = %s
                                and errata_advisory = %s''',
                                (pid, advisory))
        return self.cursor.fetchall()

    def get_errata_per_package(self, pid):
        """ Get all erratas that applies to a package """

        self.cursor.execute('''select * from erratas_packages
                                where package_id = %s''',
                                (pid,))
        return self.cursor.fetchall()

    def get_package_change(self, pcpk):
        """ Get a package change from database. """

        self.cursor.execute('''select * from packages_changes
                        where package_change_pk = %s''',
                        (pcpk,))
        return self.cursor.fetchone()

    def update_sync_packages(self, channel):
        """ Update supported channel with the latest sync package date """

        now = datetime.datetime.utcnow().strftime("%Y%m%d")
        self.cursor.execute('''update channels set channel_sync_packages=%s
                                where channel_label = %s''',
                                (now, channel))
        self.con.commit()

    def update_sync_erratas(self, channel):
        """ Update supported channel with the latest sync erratas date """

        now = datetime.datetime.utcnow().strftime("%Y%m%d")
        self.cursor.execute('''update channels set channel_sync_erratas=%s
                                where channel_label = %s''',
                                (now, channel))
        self.con.commit()

    def update_eof_channels(self, supported, channel):
        """ Update eof from all channels """

        self.cursor.execute('''update channels set channel_supported = %s
                                where channel_label = %s''',
                                (supported, channel))
        self.con.commit()

    def insert_channel(self, chan, name, parent, eol, arch, csync, psync, sup):
        """ Insert a channel """

        self.cursor.execute('''insert into channels
                            values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                            (chan, name, parent, eol, arch,
                            csync, psync, sup))
        self.con.commit()


    def get_package_file(self, digest):
        """ get files related to a digest """

        self.cursor.execute('''select * from packages_files
                                where package_file_pk = %s''', (digest, ))
        return self.cursor.fetchone()

    def get_package_file_package(self, pid):
        """ get files related to a packge """

        self.cursor.execute('''select * from packages_files
                                where package_id = %s''', (pid, ))
        return self.cursor.fetchall()

    def insert_package_files(self, digest, pid, fpath, ftype, fmod, fmd5, fchk, fsize, flink):
        """ insert files belonging to a package"""

        self.cursor.execute('''insert into packages_files
                           values (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                           (digest, pid, fpath, ftype, fmod, fmd5, fchk, fsize, flink))
        self.con.commit()

    def update_channel(self, supported, eol, channel):
        """ Update a channel """

        self.cursor.execute('''update channels set channel_supported = %s ,
                                channel_end_of_life = %s
                                where channel_label = %s''',
                                (supported, eol, channel))
        self.con.commit()

    def insert_errata_package(self, advisory, pid):
        """ Insert errata package """

        self.cursor.execute('''insert into erratas_packages values (%s,%s)''',
                            (advisory, pid))
        self.con.commit()

    def insert_bugzilla(self, bgz, bsumm):
        """ Insert bugzilla """

        self.cursor.execute('''insert into bugzilla values (%s,%s)''',
                                (bgz, bsumm))
        self.con.commit()

    def insert_errata_bugzilla(self, advisory, bgz):
        """ Insert errata bugzilla """

        self.cursor.execute('''insert into erratas_bugzilla values (%s,%s)''',
                            (advisory, bgz))
        self.con.commit()

    def insert_errata(self, adv, idate, udate, syno, advt, mdate):
        """ Insert errata """

        self.cursor.execute('''insert into erratas
                                values (%s,%s,%s,%s,%s,%s)''',
                                (adv, idate, udate, syno,
                                advt, mdate))
        self.con.commit()

    def insert_errata_channel(self, advisory, channel):
        """ Insert errata channel """

        self.cursor.execute('''insert into erratas_channel
                                values (%s,%s)''',
                                (advisory, channel))
        self.con.commit()

    def insert_package_change(self, digest, pid, author, date, txt):
        """ Insert package change """

        self.cursor.execute('''insert into packages_changes
                            values (%s,%s,%s,%s,%s)''',
                            (digest, pid, author, date, txt))
        self.con.commit()

    def set_all_packages_channel_latest(self, channel):
        """ Set all packages channel to false """

        self.cursor.execute('''update packages_channel set package_latest=%s
                               where channel_label = %s''',
                                (False, channel))
        self.con.commit()

    def get_latest_packages_channel(self, channel):
        """ get latest packages from a channel """

        self.cursor.execute('''select p.package_id,package_name,
            package_version,package_release,package_epoch,
            package_arch_label,package_last_modified
            from packages_channel as pc, packages as p
            where pc.channel_label = %s
            and pc.package_latest = True and
            pc.package_id = p.package_id''',(channel,))
        return self.cursor.fetchall()

    def get_child_channels(self, channel):
        """ get child channels from a base channel """
        self.cursor.execute('''select * from channels
                            where channel_parent_label = %s
                            and channel_supported = True''',(channel,))
        return self.cursor.fetchall()

    def set_package_channel_latest(self, pid, channel):
        """ Set latest package channel to true """

        self.cursor.execute('''update packages_channel set package_latest=%s
                        where package_id = %s and channel_label = %s''',
                        (True, pid, channel))
        self.con.commit()

    def insert_package(self, pid, pname, pver, prel, pepoch, parch, pmod):
        """ Insert package """
        self.cursor.execute('''insert into packages
                                values (%s,%s,%s,%s,%s,%s,%s)''',
                                (pid, pname, pver, prel, pepoch,
                                parch, pmod))
        self.con.commit()

    def insert_package_channel(self, pid, channel):
        """ Insert package channel """

        self.cursor.execute('''insert into packages_channel
                                values (%s,%s,%s)''',
                                (pid, channel, False))
        self.con.commit()
