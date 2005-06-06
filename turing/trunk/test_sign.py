import random
from test import *
from test_add import myRandomAdd

# Initialize VM for test "sign(a)"
def init_vm_sign(search, actor):
	actor.turing.set_reg("a", search.arga)
	actor.turing.set_reg("b", 0)

def random_vm_sign(search):
	try:
		result= search.result
	except:
		result=None
	search.arga = myRandomAdd(5,100)
	if search.arga > 0:
		search.result = 1
	else:
		search.result = -1
	if result != None and search.result == result:
		search.arga = -search.arga
		search.result = -search.result

# Evaluate quality of alogithm for test sign(a)
def eval_quality_sign(search, actor):
	# Start with 0%
	quality = 0.0
	
	# +10% for use of jumpif instruction
	if actor.code.contains("jumpif"): quality = quality + 0.10
	
	# +50% for code length
	quality = quality + 0.50 * actor.code.length_quality()

	# +10% for use of cmp_gt instruction
	if actor.code.contains("cmp_gt"): quality = quality + 0.10
	
	value = actor.turing.get_reg("a")
	
	# exit if it not the expected result
	if value != search.result: return quality

	# +30% for expected result
	quality = quality + 0.30
	
	return quality

def test_sign(ia):
	ia.search.init_vm_func = init_vm_sign
	ia.search.eval_quality_func = eval_quality_sign
	ia.search.random_vm_func = random_vm_sign

	if False:
		search.modele = Actor(self)
		search.modele.code.code.append( ["cmp_gt", "a", "b", "a"] )
		search.modele.code.code.append( ["jumpif", "a", 2] )
		search.modele.code.code.append( ["neg", "c"] )
		search.modele.code.code.append( ["store", "a", -1] )
	
	ia.search.population = 10
	ia.search.retest_result = 10
	ia.search.excepted_quality = 1.0
	ia.search.timeout = 60.0

#	ia.search.use_instr = ["neg", "jumpif", "cmp_gt"]
#	ia.search.use_regs = ["a", "b", "c"]
	
	ia.search.best_instr_len = 3
	TuringCode.min_instr = 3
	TuringCode.max_instr = 10
	test_message("sign(a)", ia.search)
	ia.search.run()
