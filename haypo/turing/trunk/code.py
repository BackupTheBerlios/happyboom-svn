import random
import copy

class TuringCode:
	min_instr = 1
	max_instr = 1

	# src is used to copy a TuringCode
	def __init__(self, search, src=None):
		self.search = search
		self.vm = self.search.vm
		if src==None:
			self.code = []
			self.use_regs = self.vm.regs.keys()
			self.use_instr = self.vm.instruction.keys()
		else:
			self.code = copy.deepcopy(src.code)
			self.use_regs = copy.deepcopy(src.use_regs)
			self.use_instr = copy.deepcopy(src.use_instr)
			
	def copy(self):
		return TuringCode(self.search, src=self)

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

	def contains(self, name):
		for instr in self.code:
			if instr[0]==name: return True
		return False

	def str(self):
		s = ""
		for instr in self.code:
			if len(s) != 0: s = s + " "
			s = s + "%s;" % self.vm.instr2str(instr)
		return s 

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

		# 20% of instruction move 
		elif r < 0.50:
			if 2 < len(self.code):
				a = random.randint(0, len(self.code)-1)
				b = random.randint(0, len(self.code)-1)
				while a == b:
					b = random.randint(0, len(self.code)-1)
				instr = self.code[a]
				del self.code[a]
				self.code.insert(b, instr)

		# 20% of code mutation (one instruction)
		elif r < 0.70:
			index = random.randint(0, len(self.code)-1)
			instr = self.gen_instr()
			self.code[index] = instr 

		# 30% of parameter mutation (one parameter)
		else:
			# Choose instruction
			index = random.randint(0, len(self.code)-1)

			# Choose parameter
			func = self.code[index][0]
			instr = self.vm.instruction[ func ]
			param = random.randint(1, len(instr)-1)
			type = instr[param]

			# Generate new argument
			self.code[index][param] = self.gen_arg(func, type)

	# Quality of code length (1.0 is best, 0.0 is worst)
	def length_quality(self):
		code_len = len(self.code)
		best = self.search.best_instr_len
		if code_len < best: return 1.0
		if TuringCode.max_instr == best: return 1.0
		code_len = float(code_len-best) / (TuringCode.max_instr-best)
		return 1.0 - code_len