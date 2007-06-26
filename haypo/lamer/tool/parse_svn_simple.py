#!/usr/bin/python
from sys import stderr, argv, exit
import re

def parse(filename):
    infos = {
        'username': None,
        'password': None,
        'svn:realmstring': None,
    }
    next = None
    skip = False
    for line in open(filename):
        if skip:
            skip = False
            continue
        line = line.strip()
        if line in infos.keys():
            next = line
            skip = True
        elif next:
            infos[next] = line
            next = None
    server = infos["svn:realmstring"]
    if not server:
        return
    server = re.sub("^<(.+)> .+$", r"\1", server)

    print "%s -- username=%s -- password=%s" % (
        server, infos["username"], infos["password"])

def main():
    if len(argv) != 2:
        print >>stderr, "usage: %s filename" % argv[0]
        exit(1)
    parse(argv[1])

if __name__ == "__main__":
    main()

