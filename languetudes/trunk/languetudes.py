#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys, getopt

usage = """
USAGE:
    %s [--ihm <interface>]
    %s -h | --help

Les IHM disponibles sont :
 ** console : mode interactif dans un terminal texte.
 ** ncurses : interface graphique dans un terminal texte.
 ** tkinter : interface graphique utilisant la bibiotheque TK.
""" % (sys.argv[0], sys.argv[0])

ihm = ("console", "ncurse", "tkinter")

def main():
    ihmModule = "tkinter"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "ihm="])
    except getopt.GetoptError:
        print "ERREUR: usage incorrect."
        print usage
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            print usage
            sys.exit()
        elif o == "--ihm":
            if a in ihm:
                ihmModule = a
            else:
                print "ERREUR: ihm incorrect."
                print usage
                sys.exit(2)
    try:
        src = __import__("src", globals(),  locals(), [ihmModule])
        mod = getattr(src, ihmModule)
        mod.Application()
    except ImportError, errmsg:
        print "Erreur : un module Python est absent alors qu'il est nécessaire."
        print errmsg
        sys.exit(1)

if __name__ == "__main__":
    main()
