from code import TuringCode
import random
import time
import sys # stdout
from turing import Turing

def test_message(test_name, search):
	if not search.verbose: return
	print ""
	print "=== Start test \"%s\" ===" % (test_name)
	print "Quality >= %.2f" % (search.excepted_quality)
	print "Population = %u" % (search.population)
	print "Max. instr = %u" % (TuringCode.max_instr)
	print ""

# Just test Turing for small code
def test_turing_max(ia):
	sys.stdout.write("Turing max test: ")
	c = TuringCode(ia.search.vm)
	c.code.append( ("store", "a", 2,) )
	c.code.append( ("store", "b", 8,) )
	c.code.append( ("cmp_gt", "a", "b", "c") )
	c.code.append( ("jumpif", "c", 1, ) )
	c.code.append( ("copy", "b", "a",) )
	c.run()
	if c.vm.get_reg("a")==8:
		print "ok."
	else:
		print "fail!"
