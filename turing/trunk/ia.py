#!/usr/bin/python
import random
import traceback

from search import Actor
from search import SearchTuring

from test import *

def test_add():
	search = SearchTuring()
	Actor.max_instr = 10
	search.init_vm_func = init_vm_add
	search.eval_quality_func = eval_quality_add
	search.excepted_quality = 0.95
	search.population = 10
	search.timeout = 10.0
	search.best_instr_len = 2
	search.result = 7
	print "Start add(a,b) test : search %s%% <= quality." % (search.excepted_quality)
	search.run()

def test_add3():
	search = SearchTuring()
	Actor.max_instr = 10
	search.init_vm_func = init_vm_add3
	search.eval_quality_func = eval_quality_add
	search.excepted_quality = 0.99
	search.population = 10
	search.timeout = 30.0
	search.best_instr_len = 3
	search.result = 17
	print "Start add(a,b,c) test : search %s%% <= quality." % (search.excepted_quality)
	search.run()


def main():
	random.seed()

	try:
#		test_add()
		test_add3()
	
	except Exception, msg:
		print "EXCEPTION :"
		print msg
		traceback.print_exc()

if __name__=="__main__": main()
