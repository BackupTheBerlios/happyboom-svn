#!/usr/bin/python
import re
from lamer import Lamer

class Gajim(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "gajim", verbose)

    def _extract(self):
        accounts = {}
        for line in self.readText("~/.gajim/config"):
            match = re.match("^accounts\.([a-z0-9.-]+)\.([a-z0-9_-]+) = (.*)$", line)
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
            message = 'Account "%s@%s"' % (data["name"], data["hostname"])
            if "custom_port" in data:
                message += ' port %s' % data["custom_port"]
            if "usessl" in data:
                message += ' (SSL)'
            if "password" in data:
                message += ' with password "%s"' % data["password"]
            elif self.skip_no_password:
                return
            self.write(message)
        except LookupError:
            return

Gajim(False).extract()

