from turing import *
import random

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

	def gen_value(self, func):
		return random.randint(-9,9)

	def gen_reg(self, func):
		regs = self.vm.regs.keys()
		i = random.randint(0, len(regs)-1)
		return regs[i]
	
	def gen_arg(self, func, type):
		if type == "R":
			return self.gen_reg(func)
		else:
			return self.gen_value(func)

	def gen_instr(self):
		instr = self.vm.instruction.keys()
		i = random.randint(0, len(instr)-1)
		func = instr[i]
		instr = self.vm.instruction[ func ]
		result = [ func ]
		for type in instr[1:]:
			result.append( self.gen_arg(func, type) )
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

		self.vm.run()


