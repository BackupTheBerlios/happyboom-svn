import random
from test import *
from test_add import eval_quality_add
from test_add import myRandomAdd

def random_vm_add3(search):
	search.arga = myRandomAdd(5,100)
	search.argb = myRandomAdd(5,100)
	search.argc = myRandomAdd(5,100)
	while abs(search.arga + search.argb + search.argc) < 5:
		search.argb = myRandomAdd(5,100)
		search.argc = myRandomAdd(5,100)
	search.result = search.arga + search.argb + search.argc

# Initialize VM for test "add(a,b,c)"
def init_vm_add3(search, actor):
	actor.turing.set_reg("a", search.arga)
	actor.turing.set_reg("b", search.argb)			
	actor.turing.set_reg("c", search.argc)

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
