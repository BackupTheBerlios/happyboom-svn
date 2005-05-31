from search import Actor
import random
import time
import sys # stdout
from turing import Turing

# Initialize VM for test "sign(a)"
def init_vm_sign(search, actor):
	actor.vm.set_reg("a", search.arga)

def random_vm_sign(search):
	search.arga = random.randint(-9,9)
	while abs(search.arga) < 2:
		search.arga = random.randint(-9,9)
	if search.arga > 0:
		search.result = 1
	else:
		search.result = -1
	
def random_vm_add(search):
	search.arga = random.randint(-9,9)
	search.argb = random.randint(-9,9)
	while search.arga == search.argb:
		search.argb = random.randint(-9,9)
	search.result = search.arga + search.argb
	
def random_vm_add3(search):
	search.arga = random.randint(-9,9)
	search.argb = random.randint(-9,9)
	while search.arga == search.argb:
		search.argb = random.randint(-9,9)
	search.argc = random.randint(-9,9)
	while search.argc == search.arga or search.argc == search.argb:
		search.argc = random.randint(-9,9)
	search.result = search.arga + search.argb + search.argc
	
# Initialize VM for test "add(a,b)"
def init_vm_add(search, actor):
	actor.vm.set_reg("a", search.arga)
	actor.vm.set_reg("b", search.argb)			

# Initialize VM for test "add(a,b,c)"
def init_vm_add3(search, actor):
	actor.vm.set_reg("a", search.arga)
	actor.vm.set_reg("b", search.argb)			
	actor.vm.set_reg("c", search.argc)

# Evaluate quality of alogithm for test sign(a)
# Result in [0.0 .. 1.0]
def eval_quality_sign(search, actor):
	quality = 0.0
	
	# +25% for use of if instruction
	useif = False
	for instr in actor.vm.code:
		if instr[0] == 'jumpif':
			useif = True
			break
	if not useif: return quality
	quality = quality + 0.25
	
	# exit if it not the expected result
	value = actor.vm.get_reg("a")
	if value != search.result: return quality

	# +25% for expected result
	quality = quality + 0.25

	# +50% for code length
	code_len = len(actor.vm.code)
	best = search.best_instr_len
	if best <= code_len:
		code_len = float(code_len-best) / (Actor.max_instr-best)
		code_len = 1.0 - code_len
	else:
		code_len = 1.0
	quality = quality + 0.50 * code_len

	return quality

# Evaluate quality of alogithm for test add(...)
# Quality of result in [0.0 ; 1.0]
# [0.0 .. 0.5] : expected result
# (0.5 .. 1.0] : very good results (small code, etc.)
def eval_quality_add(search, actor):
	# 0% if result is wrong
	if actor.vm.stack.empty(): return 0.0

	# +20% if stack is not empty
	quality = 0.2

	# +30% for diffence to result
	value = actor.vm.stack.top()
	diff = abs(value - search.result) / 16.0
	diff = 1.0 - diff
	quality = quality + 0.3 * diff

	# Exit if the result is not exaclty to expected one's
	if value != search.result: return quality

	# +5% if stack length equals to one
	stack_len = len(actor.vm.stack.stack)
	if stack_len == 1: quality = quality + 0.05

	# +35% for code length
	code_len = len(actor.vm.code)
	best = search.best_instr_len
	if best <= code_len:
		code_len = float(code_len-best) / (Actor.max_instr-best)
		code_len = 1.0 - code_len
	else:
		code_len = 1.0
	quality = quality + 0.35 * code_len

	# +10% if it doesn't use store trick
	trick = False
	for instr in actor.vm.code:
		if instr[0] == 'store':
			trick = True
			break
	if not trick: quality = quality + 0.10

	# Final quality
	return quality

def test_message(test_name, search):
	print ""
	print "=== Start test \"%s\" ===" % (test_name)
	print "Quality >= %.2f" % (search.excepted_quality)
	print "Population = %u" % (search.population)
	print "Max. instr = %u" % (Actor.max_instr)
	print ""

def test_add(ia):
	Actor.max_instr = 10
	ia.search.init_vm_func = init_vm_add
	ia.search.eval_quality_func = eval_quality_add
	
	ia.search.random_vm_func = random_vm_add
	
	ia.search.excepted_quality = 1.0
	ia.search.population = 10
	ia.search.timeout = 20.0
	ia.search.best_instr_len = 2
	ia.search.retest_result = 3
#	ia.search.use_instr = ["add", "push"]
	ia.search.use_regs = ["a", "b"]
	test_message("add(a,b)", ia.search)
	ia.search.run()

def test_add3(ia):
	ia.search.random_vm_func = random_vm_add3
	ia.search.init_vm_func = init_vm_add3
	ia.search.eval_quality_func = eval_quality_add
	ia.search.excepted_quality = 0.90
	ia.search.population = 10
	ia.search.timeout = 30.0
	ia.search.best_instr_len = 3
	ia.search.retest_result = 2
	ia.search.use_instr = [\
		"add", "sub", "neg", "copy", "push", "store", "pop"]
	Actor.min_instr = 3
	Actor.max_instr = 10
	test_message("add(a,b,c)", ia.search)
	ia.search.run()

def test_sign(ia):
	ia.search.init_vm_func = init_vm_sign
	ia.search.eval_quality_func = eval_quality_sign
	ia.search.random_vm_func = random_vm_sign
	
	ia.search.excepted_quality = 0.90
	ia.search.population = 30
	ia.search.timeout = 60.0
	ia.search.retest_result = 20

	ia.search.use_instr = ["store", "jumpif", "cmp_gt"]
	ia.search.use_regs = ["a", "b"]
	
	ia.search.best_instr_len = 3
	Actor.min_instr = 2
	Actor.max_instr = 10
	test_message("sign(a)", ia.search)
	ia.search.run()

def test_turing_jump(ia):
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

def test_turing_jumpif(ia):
	sys.stdout.write("Turing jumpif test: ")
	vm = Turing()
#	vm.verbose = True
	vm.code.append( ("store", "b", 2,) )
	vm.code.append( ("store", "a", 1,) )
	vm.code.append( ("jumpif", "a", 1, ) )
	vm.code.append( ("store", "b", 5,) )
	vm.run()
	if vm.get_reg("b")==2:
		print "ok."
	else:
		print "fail!"

def test_turing_sign(ia):
	sys.stdout.write("Turing jumpif test: ")
	vm = Turing()
#	vm.verbose = True
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

