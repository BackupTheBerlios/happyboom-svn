#!/usr/bin/python
import random
import traceback
import sys

from turing import Turing
from search import Actor
from search import SearchTuring

from test import *

def test_add():
	search = SearchTuring()
	Actor.max_instr = 10
	search.init_vm_func = init_vm_add
	search.eval_quality_func = eval_quality_add
	
	search.random_vm_func = random_vm_add
	
	search.excepted_quality = 1.0
	search.population = 100
	search.timeout = 20.0
	search.best_instr_len = 2
	print "Start add(a,b) test : search %.2f%% <= quality." % (search.excepted_quality)
	search.run()

def test_add3():
	search = SearchTuring()
	Actor.max_instr = 10
	search.init_vm_func = init_vm_add3
	search.eval_quality_func = eval_quality_add
	search.excepted_quality = 0.90
	search.population = 10
	search.timeout = 30.0
	search.best_instr_len = 3
	search.result = 17
	print "Start add(a,b,c) test : search %.2f%% <= quality." % (search.excepted_quality)
	search.run()

def test_turing_jump():
	sys.stdout.write("Turing jump test: ")
	vm = Turing()
	vm.code.append( ("store", "a", 2,) )
	vm.code.append( ("jump", 1,) )
	vm.code.append( ("store", "a", 5,) )
	vm.run()
	if vm.get_reg("a")==2:
		print "ok."
	else:
		print "fail!"

def test_turing_jumpif():
	sys.stdout.write("Turing jumpif test: ")
	vm = Turing()
	vm.verbose = True
	vm.code.append( ("store", "b", 2,) )
	vm.code.append( ("store", "a", 1,) )
	vm.code.append( ("jumpif", "a", 1, ) )
	vm.code.append( ("store", "b", 5,) )
	vm.run()
	if vm.get_reg("b")==2:
		print "ok."
	else:
		print "fail!"

def main():
	random.seed()

	try:
		test_add()
#		test_add3()
#		test_turing_jump()
#		test_turing_jumpif()
	
	except Exception, msg:
		print "EXCEPTION :"
		print msg
		traceback.print_exc()

if __name__=="__main__": main()
