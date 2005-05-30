from search import Actor

# Initialize VM for test "add(a,b)"
def init_vm_add(search, actor):
	actor.vm.set_reg("a", 5)
	actor.vm.set_reg("b", 2)			

# Initialize VM for test "add(a,b,c)"
def init_vm_add3(search, actor):
	actor.vm.set_reg("a", 5)
	actor.vm.set_reg("b", 2)			
	actor.vm.set_reg("c", 10)

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

