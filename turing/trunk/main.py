#!/usr/bin/python
import random # random.seed()
import traceback
from  ia import MainIA
import sys
import getopt
PROGRAM_NAME="Turing"
VERSION="0.0.0"

def usage(defval):
	print "%s version %s" % (PROGRAM_NAME, VERSION)
	print ""
	print "Usage: %s [options] [test]" % (sys.argv[0])
	print
	print "Options :"
	print "\t--help      : Show this help"
	print "\t--dont-load : Don't load old state"
	print "\t--dont-save : Don't save state when interrupted (CTRL+C)"
	print "\ttest        : Turing test (add, add3, sign)"

def parseArgs(ia, val):
	defval = val.copy()
	try:
		short = "h" #:p:dv"
		long = ["help", "dont-load", "dont-save"]
		opts, args = getopt.getopt(sys.argv[1:], short, long)
	except getopt.GetoptError:
		usage(defval)
		sys.exit(2)

	# Set mode ?
	if 0<len(args):
		test = args[0]
		if test in ia.valid_test.keys():
			val["test"] = test
		
	for o, a in opts:
		if o == "--help":
			usage(defval)
			sys.exit(0)
		if o == "--dont-load":
			val["load"] = False
		if o == "--dont-save":
			val["save"] = False
	return val

def main():
	random.seed()
	try:
		ia = MainIA()

		val = { \
			"load": True,
			"save": True,
			"test": "add"}
		val = parseArgs(ia, val)
		
		ia.init(val)
		ia.run()
		print ""
	except SystemExit, code:
		pass
	except Exception, msg:
		print "EXCEPTION :"
		print msg
		print " --"
		traceback.print_exc()

if __name__=="__main__": main()
