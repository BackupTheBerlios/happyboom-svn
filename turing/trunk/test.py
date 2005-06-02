from code import TuringCode
import random
import time
import sys # stdout
from turing import Turing

# Initialize VM for test "sign(a)"
def init_vm_sign(search, actor):
	actor.turing.set_reg("a", search.arga)

def random_vm_max(search):
	try:
		a= search.arga
		b= search.argb
	except:
		a=b=None
	search.arga = random.randint(-999,999)
	search.argb = random.randint(-999,999)
	while search.arga==search.argb:
		search.arga = random.randint(-999,999)
		search.argb = random.randint(-999,999)
	if a != None:
		ok = a<b and search.arga>search.argb
		ok = ok or (a>b and search.arga<search.argb)
		if not ok:
			tmp = search.arga
			search.arga = search.argb
			search.argb = tmp 
	if search.arga > search.argb:
		search.result = search.arga
	else:
		search.result = search.argb

def random_vm_sign(search):
	try:
		result= search.result
	except:
		result=None
	search.arga = random.randint(-100,100)
	while abs(search.arga)<2: search.arga = random.randint(-100,100)
	if search.arga > 0:
		search.result = 1
	else:
		search.result = -1

	if result != None and search.result == result:
		search.arga = -search.arga
		search.result = -search.result

def myRandomAdd(min,max):
	x = random.randint(min,max)
	if random.random() < 0.5: x = -x
	return x

def random_vm_add(search):
	search.arga = myRandomAdd(5,100)
	search.argb = myRandomAdd(5,100)
	while abs(search.arga + search.argb) < 5:
		search.argb = myRandomAdd(5,100)
	search.result = search.arga + search.argb
	
def random_vm_add3(search):
	search.arga = myRandomAdd(5,100)
	search.argb = myRandomAdd(5,100)
	search.argc = myRandomAdd(5,100)
	while abs(search.arga + search.argb + search.argc) < 5:
		search.argb = myRandomAdd(5,100)
		search.argc = myRandomAdd(5,100)
	search.result = search.arga + search.argb + search.argc
	
# Initialize VM for test "add(a,b)"
def init_vm_regab(search, actor):
	actor.turing.set_reg("a", search.arga)
	actor.turing.set_reg("b", search.argb)			

# Initialize VM for test "add(a,b,c)"
def init_vm_add3(search, actor):
	actor.turing.set_reg("a", search.arga)
	actor.turing.set_reg("b", search.argb)			
	actor.turing.set_reg("c", search.argc)

# Evaluate quality of alogithm for test max(a,b)
# Result in [0.0 .. 1.0]
def eval_quality_max(search, actor):
	quality = 0.00

	# +15% for use of if instruction
	useif = False
	for instr in actor.code.code:
		if instr[0] == 'cmp_gt':
			useif = True
			break
	if not useif: return quality
	quality = quality + 0.15
		
	# +15% for use of if instruction
	if not actor.code.contains("jumpif"): return quality
	quality = quality + 0.15
	
	# exit if it not the expected result
	value = actor.turing.get_reg("a")
	if value != search.result: return quality

	# +20% for expected result
	quality = quality + 0.20
	
	# +50% for code length
	quality = quality + 0.50 * actor.code.length_quality()

	return quality

# Evaluate quality of alogithm for test sign(a)
def eval_quality_sign(search, actor):
	# 10% if program doesn't crash :-)
	quality = 0.10
	
	# +10% for use of jumpif instruction
	if actor.code.contains("jumpif"): quality = quality + 0.10
	
	# +10% for use of cmp_gt instruction
	if actor.code.contains("cmp_gt"): quality = quality + 0.10
	
	# exit if it not the expected result
	value = actor.turing.get_reg("a")
	if value != search.result: return quality

	# +20% for expected result
	quality = quality + 0.20
	
	# +50% for code length
	quality = quality + 0.50 * actor.code.length_quality()

	return quality

# Evaluate quality of alogithm for test add(...)
def eval_quality_add(search, actor):
	# 0% if result is wrong
	if actor.turing.stack.empty(): return 0.0

	# +20% if stack is not empty
	quality = 0.2

	## +30% for diffence to result
	value = actor.turing.stack.top()
#	diff = abs(value - search.result) / 200.0
#	diff = 1.0 - diff
#	quality = quality + 0.3 * diff

	# Exit if the result is not exaclty to expected one's
	if value != search.result: return quality
	
	# +30% if result is exact
	quality = quality + 0.3

	# +5% if stack length equals to one
	stack_len = len(actor.turing.stack.stack)
	if stack_len == 1: quality = quality + 0.05

	# +45% for code length
	quality = quality + 0.45 * actor.code.length_quality()

	# Final quality
	return quality

def test_message(test_name, search):
	if not search.verbose: return
	print ""
	print "=== Start test \"%s\" ===" % (test_name)
	print "Quality >= %.2f" % (search.excepted_quality)
	print "Population = %u" % (search.population)
	print "Max. instr = %u" % (TuringCode.max_instr)
	print ""

def test_add(ia):
	ia.search.population = 10
	TuringCode.min_instr = 2
	TuringCode.max_instr = 10
	ia.search.init_vm_func = init_vm_regab
	ia.search.eval_quality_func = eval_quality_add
	
	ia.search.random_vm_func = random_vm_add
	
	ia.search.excepted_quality = 1.0
	ia.search.timeout = 20.0
	ia.search.best_instr_len = 2
	ia.search.retest_result = 10
#	ia.search.use_instr = ["add", "push"]
#	ia.search.use_regs = ["a", "b"]
	test_message("add(a,b)", ia.search)
	ia.search.run()

def test_add3(ia):
	ia.search.random_vm_func = random_vm_add3
	ia.search.init_vm_func = init_vm_add3
	ia.search.eval_quality_func = eval_quality_add
	ia.search.excepted_quality = 1.0
	ia.search.population = 10
	ia.search.timeout = 30.0
	ia.search.best_instr_len = 3
	ia.search.retest_result = 5
	ia.search.use_instr = [\
		"add", "sub", "neg", "copy", "push", "store", "pop"]
	TuringCode.min_instr = 3
	TuringCode.max_instr = 10
	test_message("add(a,b,c)", ia.search)
	ia.search.run()

def test_sign(ia):
	ia.search.init_vm_func = init_vm_sign
	ia.search.eval_quality_func = eval_quality_sign
	ia.search.random_vm_func = random_vm_sign
	
	ia.search.excepted_quality = 1.0
	ia.search.population = 10
	ia.search.timeout = 60.0
	ia.search.retest_result = 10

#	ia.search.use_instr = ["store", "jumpif", "cmp_gt"]
#	ia.search.use_regs = ["a", "b"]
	
	ia.search.best_instr_len = 3
	TuringCode.min_instr = 2
	TuringCode.max_instr = 10
	test_message("sign(a)", ia.search)
	ia.search.run()

def test_max(ia):
	ia.search.random_vm_func = random_vm_max
	ia.search.init_vm_func = init_vm_regab
	ia.search.eval_quality_func = eval_quality_max
	
	ia.search.excepted_quality = 1.0 
	ia.search.population = 10 
	ia.search.timeout = 60.0
	ia.search.retest_result = 10

#	ia.search.use_instr = ["store", "jumpif", "cmp_gt"]
#	ia.search.use_regs = ["a", "b"]
	
	ia.search.best_instr_len = 3
	TuringCode.min_instr = 2
	TuringCode.max_instr = 10
	test_message("max(a)", ia.search)
	ia.search.run()

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
