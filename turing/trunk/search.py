import random
from turing import *
import time

class Actor:
	max_instr = 5

	def __init__(self):
		self.vm = Turing()
		self.step = 0
		self.verbose = False
		self.regenerate_code()
		self.quality = 0.0
		self.name = "no name"

	def copy(self):
		copy = Actor()
		copy.vm = self.vm.copy()
		copy.name = self.name
		return copy

	def gen_value(self):
		return random.randint(-9,9)

	def gen_reg(self):
		regs = self.vm.regs.keys()
		i = random.randint(0, len(regs)-1)
		return regs[i]
	
	def gen_arg(self, type):
		if type == "R":
			return self.gen_reg()
		else:
			return self.gen_value()

	def gen_instr(self):
		instr = self.vm.instruction.keys()
		i = random.randint(0, len(instr)-1)
		func = instr[i]
		instr = self.vm.instruction[ func ]
		result = [ func ]
		for type in instr[1:]:
			result.append( self.gen_arg(type) )
		return result

	def regenerate_code(self):
		self.vm.reset_code()
		nb = random.randint(1, Actor.max_instr)
		for i in range(nb):
			self.vm.code.append( self.gen_instr() )

	def live(self):
		r = random.random()
		
		# 25% of new instruction
		if r < 0.25:
			if len(self.vm.code) < Actor.max_instr:
				index = random.randint(0, len(self.vm.code))
				instr = self.gen_instr()
				if self.verbose: print "New instr. %s at %u" \
					% (self.vm.instr2str(instr), index)
				self.vm.code.insert(index, instr)
			else:
				if self.verbose: print "Don't add new instr."

		# 25% of delete instruction
		elif r < 0.50:
			if len(self.vm.code) != 1:
				index = random.randint(0, len(self.vm.code)-1)
				if self.verbose: print "Remove instr. %u" % (index)
				del self.vm.code[index]
			else:
				if self.verbose: print "Cannot remove any instr."

		# 50% of code mutation (one instruction)
		else:
			index = random.randint(0, len(self.vm.code)-1)
			instr = self.gen_instr()
			if self.verbose: print "Change instr. %u to %s" % (index, self.vm.instr2str(instr))
			self.vm.code[index] = instr 

	def eval(self):
		self.step = self.step + 1
		if self.verbose: print "Actor step %u" % (self.step)

		try:
			self.vm.run()
		except TuringException, msg:
			if self.verbose: print "Turing exception: %s" % (msg)
			self.quality = 0.0

class SearchTuring:
	def __init__(self):
		self.population = 10
		self.quit = False
		self.step = 0
		self.excepted_quality = 0.5
		self.init_vm_func = None
		self.eval_quality_func = None
		self.timeout = 3.0 # seconds
		self.best_quality = 0.0

	def start(self):
		self.actor = [Actor() for i in range(self.population)]
	
	def live(self):
		if self.eval_quality_func == None:
			raise Exception("SearchTuring can't live without eval_quality function!")
		self.step = self.step + 1
	
		quality = {}
		i = 0
		best_quality = -1
		best_actor = None
		for actor in self.actor:
			actor.name = "Actor %u" % (i)
			actor.live()

			# Evaluate algorithm
			actor.vm.reset_stack()
			actor.vm.reset_regs()
			if self.init_vm_func != None: self.init_vm_func (self, actor)
			actor.eval()
			actor.quality = self.eval_quality_func (self, actor)
			
			if best_quality < actor.quality:
				best_quality = actor.quality
				best_actor = actor
				best_index = i
			i = i + 1

		self.best_quality = best_quality

		self.quit = (self.excepted_quality <= best_quality)
		if self.quit:
			print "=== Best actor %s ===" % best_actor.name 
			best_actor.vm.print_code()
			best_actor.vm.print_stack()
			print "Quality: %.2f%%" % best_quality
			return

		self.actor = [best_actor.copy() for i in range(self.population)]

	def run(self):
		self.start()
		t = time.time()
		t_sec = time.time()
		while not self.quit:
			self.live()
			if self.timeout < time.time() - t:
				print "Seach timeout!!! (unlimited loop?)"
				break
			if 1.0 < time.time() - t_sec:
				t_sec = time.time()
				print "Search (step=%u, quality=%s) ..." \
					% (self.step, self.best_quality)
		print "Step: %u" % (self.step)
