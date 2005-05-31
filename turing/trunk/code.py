import random

class TuringCode:
	min_instr = 1
	max_instr = 1

	def __init__(self, vm, copy=None):
		self.vm = vm
		if copy==None:
			self.code = []
			self.use_regs = self.vm.regs.keys()
			self.use_instr = self.vm.instruction.keys()
		else:
			self.code = copy.code[:]
			self.use_regs = copy.use_regs[:]
			self.use_instr = copy.use_instr[:]
			
	def copy(self):
		return TuringCode(self.vm, copy=self)

	def load(self, f):
		self.code = f.load() 
		self.use_regs = f.load() 
		self.use_instr = f.load() 

	def save(self, f):
		f.dump( self.code )
		f.dump( self.use_regs )
		f.dump( self.use_instr )
			
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

	def str(self):
		s = ""
		for instr in self.code:
			s = s + " %s;" % self.vm.instr2str(instr)
		return "Code:%s" % (s)

	def regenerate(self):
		self.code = []
		nb = random.randint(TuringCode.min_instr, TuringCode.max_instr)
		for i in range(nb):
			self.code.append( self.gen_instr() )

	def run(self):
		if len(self.code) == 0: self.regenerate()
		self.vm.run(self.code)

	def mutation(self):
		if len(self.code) == 0: self.regenerate()
		r = random.random()
		
		# 15% of new instruction
		if r < 0.15:
			if len(self.code) < TuringCode.max_instr:
				index = random.randint(0, len(self.code))
				instr = self.gen_instr()
				self.code.insert(index, instr)

		# 15% of delete instruction
		elif r < 0.30:
			if TuringCode.min_instr < len(self.code):
				index = random.randint(0, len(self.code)-1)
				del self.code[index]

		# 20% of instruction exchange
		elif r < 0.50:
			if 2 < len(self.code):
				a = random.randint(0, len(self.code)-1)
				b = random.randint(0, len(self.code)-1)
				while a == b:
					b = random.randint(0, len(self.code)-1)
				tmp = self.code[a]
				self.code[a] = self.code[b]
				self.code[b] = tmp

		# 50% of code mutation (one instruction)
		else:
			index = random.randint(0, len(self.code)-1)
			instr = self.gen_instr()
			self.code[index] = instr 
