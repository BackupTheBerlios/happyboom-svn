#!/usr/bin/python
from lamer import Lamer
import base64

class Ncftp(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "ncftp", verbose)

    def _extract(self):
        skip = 2
        for line in self.readText("~/.ncftp/bookmarks"):
            # Skip two lines of header
            if skip:
                skip -= 1
                continue

            data = line.split(",")
            server = data[1]
            login = data[2]
            password = data[3]
            if password.startswith("*encoded*"):
                password = base64.b64decode(password[9:])
            if password:
                login = "%s:%s" % (login, password)
            elif self.skip_no_password:
                continue
            port = int(data[7])
            self.write("ftp://%s@%s:%s/" % (login, server, port))

if __name__ == "__main__":
    Ncftp(False).extract()

