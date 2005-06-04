import random
from test import *

# Calculate new random value in [-max,-min] or [min,max]
def myRandomAdd(min,max):
	x = random.randint(min,max)
	if random.random() < 0.5: x = -x
	return x

# Randomize arguments to test add(a,b)
def random_vm_add(search):
	search.arga = myRandomAdd(5,100)
	search.argb = myRandomAdd(5,100)
	while abs(search.arga + search.argb) < 5:
		search.argb = myRandomAdd(5,100)
	search.result = search.arga + search.argb
	
# Initialize VM for test "add(a,b)"
def init_vm_regab(search, actor):
	actor.turing.set_reg("a", search.arga)
	actor.turing.set_reg("b", search.argb)			

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

# Initialise everything to test add(a,b)
def test_add(ia):
	ia.search.init_vm_func = init_vm_regab
	ia.search.eval_quality_func = eval_quality_add
	ia.search.random_vm_func = random_vm_add
	
	ia.search.population = 10
	ia.search.retest_result = 10
	ia.search.excepted_quality = 1.0
	ia.search.timeout = 20.0
#	ia.search.use_instr = ["add", "push"]
#	ia.search.use_regs = ["a", "b"]

	ia.search.best_instr_len = 2
	TuringCode.min_instr = 2
	TuringCode.max_instr = 10
	test_message("add(a,b)", ia.search)
	ia.search.run()
