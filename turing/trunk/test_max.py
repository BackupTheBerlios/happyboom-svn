import random
from test import *
from test_add import init_vm_regab

# Look for new random arguments to send to max(a,b)
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

# Prepare everything to test max(a,b) algorithm
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
