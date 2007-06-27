#!/usr/bin/python
from lamer import Lamer
from ConfigParser import RawConfigParser

class Pypi(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "pypi", verbose)

    def _extract(self):
        config = RawConfigParser()
        config.readfp(self.open("~/.pypirc"))
        username = config.get("server-login", "username")
        password = config.get("server-login", "password")
        self.write("Connect http://cheeseshop.python.org/ with username=%s and password=%s" % (
            username, password))

if __name__ == "__main__":
    Pypi(False).extract()

