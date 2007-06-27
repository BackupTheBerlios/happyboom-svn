#!/usr/bin/python
import re
from lamer import Lamer

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
            self.write('Account "%s@%s" with password "%s"' % (
                data["name"], data["hostname"], data["password"]))
        except LookupError:
            pass

Gajim(False).extract()

