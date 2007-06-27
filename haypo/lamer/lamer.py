from errno import ENOENT
from os.path import normpath, expanduser
from sys import stderr
from glob import glob

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

    def normpath(self, filename):
        filename = expanduser(filename)
        filename = normpath(filename)
        return filename

    def glob(self, pattern):
        return glob(self.normpath(pattern))

    def open(self, filename, mode='r'):
        return open(self.normpath(filename), mode)

    def readText(self, filename):
        for line in self.open("~/.gajim/config"):
            yield line.rstrip()

    def write(self, text):
        print "[%s] %s" % (self.name, text)

