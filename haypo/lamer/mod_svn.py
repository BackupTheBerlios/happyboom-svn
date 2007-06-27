#!/usr/bin/python
import re
from lamer import Lamer

class Subversion(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "subversion", verbose)

    def parse(self, filename):
        infos = {}
        next = None
        skip = False
        for line in open(filename):
            if skip:
                skip = False
                continue
            line = line.strip()
            if line in ('username', 'password', 'svn:realmstring'):
                next = line
                skip = True
            elif next:
                infos[next] = line
                next = None
        try:
            server = infos["svn:realmstring"]
            if not server:
                return
            server = re.sub("^<(.+)> .+$", r"\1", server)

            credentials = "--username=%s" % infos["username"]
            if "password" in infos:
                credentials += "--password=%s" % infos["password"]
            elif self.skip_no_password:
                return
            self.write("svn co %s %s" % (server, credentials))
        except KeyError:
            return

    def _extract(self):
        for filename in self.glob("~/.subversion/auth/svn.simple/*"):
            self.parse(filename)

def main():
    Subversion(False).extract()

if __name__ == "__main__":
    main()