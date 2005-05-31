#!/usr/bin/python
import random
import traceback
import sys

from turing import Turing
from search import Actor
from search import SearchTuring

from test import *

def test_message(test_name, search):
	print ""
	print "=== Start test \"%s\" ===" % (test_name)
	print "Quality >= %.2f" % (search.excepted_quality)
	print "Population = %u" % (search.population)
	print "Max. instr = %u" % (Actor.max_instr)
	print ""

def test_sign():
	search = SearchTuring()

	search.init_vm_func = init_vm_sign
	search.eval_quality_func = eval_quality_sign
	search.random_vm_func = random_vm_sign
	
	search.excepted_quality = 0.90
	search.population = 30
	search.timeout = 60.0
	search.retest_result = 20

	search.use_instr = ["store", "jumpif", "cmp_gt"]
	search.use_regs = ["a", "b"]
	
	search.best_instr_len = 3
	Actor.min_instr = 2
	Actor.max_instr = 4
	test_message("sign(a)", search)
	search.run()

def test_add():
	search = SearchTuring()
	Actor.max_instr = 10
	search.init_vm_func = init_vm_add
	search.eval_quality_func = eval_quality_add
	
	search.random_vm_func = random_vm_add
	
	search.excepted_quality = 1.0
	search.population = 10
	search.timeout = 20.0
	search.best_instr_len = 2
	search.use_instr = ["add", "push"]
	search.use_regs = ["a", "b"]
	test_message("add(a,b)", search)
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
	test_message("add(a,b,c)", search)
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

def test_turing_sign():
	sys.stdout.write("Turing jumpif test: ")
	vm = Turing()
	vm.verbose = True
	vm.code.append( ("store", "a", 8,) )
	vm.code.append( ("cmp_gt", "a", "b", "b") )
	vm.code.append( ("store", "a", 1,) )
	vm.code.append( ("jumpif", "b", 1, ) )
	vm.code.append( ("store", "a", -1,) )
	vm.run()
	if vm.get_reg("a")==1:
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
#		test_add()
		test_sign()
#		test_add3()
#		test_turing_jump()
#		test_turing_jumpif()
#		test_turing_sign()
		print ""
	
	except Exception, msg:
		print "EXCEPTION :"
		print msg
		traceback.print_exc()

if __name__=="__main__": main()
