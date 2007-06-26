#!/usr/bin/python
from errno import ENOENT
from sys import stderr
import re
from os.path import normpath, expanduser

class Lamer:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose
        if self.verbose:
            print >>stderr, "[ Module %s ]" % self.name

    def extract(self):
        try:
            self._extract()
        except IOError, err:
            if err.errno == ENOENT:
                print err
                pass
            else:
                raise

    def open(self, filename, mode='r'):
        filename = expanduser(filename)
        filename = normpath(filename)
        return open(filename, mode)

    def readText(self, filename):
        for line in self.open("~/.gajim/config"):
            yield line.rstrip()

class Gajim(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "gajim", verbose)

    def _extract(self):
        accounts = {}
        for line in self.readText("~/.gajim/config"):
            match = re.match("^accounts\.([a-z0-9.-]+)\.([a-z0-9-]+) = (.*)$", line)
            if match:
                account = match.group(1)
                key = match.group(2)
                value = match.group(3)
                if not account in accounts:
                    accounts[account] = {}
                accounts[account][key] = value
        for account in accounts.itervalues():
            self.displayAccount(account)

    def displayAccount(self, data):
        try:
            print "Jabber: login=%s@%s -- password=%s" % (
                data["name"], data["hostname"], data["password"])
        except LookupError:
            pass

Gajim(False).extract()

