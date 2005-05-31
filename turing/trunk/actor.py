from turing import *
import random

class Actor:
	min_instr = 1
	max_instr = 5

	def __init__(self, copy=None):
		if copy==None:
			self.vm = Turing()
			self.step = 0
			self.verbose = False
			self.name = "no name"
			self.use_regs = self.vm.regs.keys()
			self.use_instr = self.vm.instruction.keys()
			self.quality = 0.0
		else:
			self.vm = copy.vm.copy()
			self.step = copy.step
			self.name = copy.name
			self.verbose = copy.verbose
			self.use_regs = copy.use_regs[:]
			self.use_instr = copy.use_instr[:]
			self.quality = copy.quality

	def copy(self):
		return Actor(self)

	def gen_value(self, func):
		return random.randint(-9,9)

	def gen_reg(self, func):
		i = random.randint(0, len(self.use_regs)-1)
		return self.use_regs[i]
	
	def gen_arg(self, func, type):
		if type == "R":
			return self.gen_reg(func)
		else:
			return self.gen_value(func)

	def gen_instr(self):
		i = random.randint(0, len(self.use_instr)-1)
		func = self.use_instr[i]
		result = [ func ]
		instr = self.vm.instruction[ func ]
		for type in instr[1:]:
			result.append( self.gen_arg(func, type) )
		return result

	def regenerate_code(self):
		self.vm.reset_code()
		nb = random.randint(Actor.min_instr, Actor.max_instr)
		for i in range(nb):
			self.vm.code.append( self.gen_instr() )

	def mutation(self):
		if len(self.vm.code) == 0: self.regenerate_code()
		r = random.random()
		
		# 15% of new instruction
		if r < 0.15:
			if len(self.vm.code) < Actor.max_instr:
				index = random.randint(0, len(self.vm.code))
				instr = self.gen_instr()
				if self.verbose: print "New instr. %s at %u" \
					% (self.vm.instr2str(instr), index)
				self.vm.code.insert(index, instr)
			else:
				if self.verbose: print "Don't add new instr."

		# 15% of delete instruction
		elif r < 0.30:
			if Actor.min_instr < len(self.vm.code):
				index = random.randint(0, len(self.vm.code)-1)
				if self.verbose: print "Remove instr. %u" % (index)
				del self.vm.code[index]
			else:
				if self.verbose: print "Cannot remove any instr."

		# 20% of instruction exchange
		elif r < 0.50:
			if 2 < len(self.vm.code):
				a = random.randint(0, len(self.vm.code)-1)
				b = random.randint(0, len(self.vm.code)-1)
				while a == b:
					b = random.randint(0, len(self.vm.code)-1)
				tmp = self.vm.code[a]
				self.vm.code[a] = self.vm.code[b]
				self.vm.code[b] = tmp

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


