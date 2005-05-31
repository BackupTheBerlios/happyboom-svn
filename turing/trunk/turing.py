import sys # sys.stdout

class TuringException(Exception):
	def __init__(self, msg):
		Exception.__init__(self, msg)

class TuringStack:
	def __init__(self):
		self.stack = []
		self.max_size = 256

	def copy(self):
		copy = TuringStack()
		copy.stack = self.stack[:]
		return copy

	def push(self, value):
		if len(self.stack) == self.max_size:
			raise TuringException("Turing stack full (can't push)!")
		self.stack.append(value)

	def top(self):
		if len(self.stack) == 0:
			raise TuringException("Turing stack empty (can't returns top)!")
		return self.stack[-1]

	def pop(self):
		if len(self.stack) == 0:
			raise TuringException("Turing stack empty (can't pop)!")
		value = self.stack[-1]
		del self.stack[-1]
		return value

	def empty(self):
		return len(self.stack) == 0

	def reset(self):
		self.stack = []

class Turing:
	def __init__(self):
		self.code = []
		self.stack = TuringStack() 
		self.instruction = {\
			"add": (self.add, "R", "R", "R"),
			"sub": (self.sub, "R", "R", "R"),
			"neg": (self.neg, "R"),
			"copy": (self.copyreg, "R", "R"),
			"cmp_gt": (self.cmp_gt, "R", "R", "R"),
			"jump": (self.jump, "V"),
			"jumpif": (self.jumpif, "R", "V"),
			"store": (self.store, "R", "V"),
			"pop": (self.pop, "R"),
			"push": (self.push, "R")
			}
		self.regs = {"a": 0, "b": 0, "c": 0, "d": 0}
		self.verbose = False
		self.instr_pointer = 0
		self.conditionnal = False
		self.step = 0
		self.max_step = 20

	def copy(self):
		turing = Turing()
		turing.regs = self.regs.copy()
		turing.stack = self.stack.copy()
		turing.code = self.code[:]
		return turing

	def get_reg(self, reg):
		return self.regs[ reg ]

	def set_reg(self, reg, value):
		self.regs[ reg ] = value

	def copyreg(self, instr):
		val = self.get_reg(instr[1])
		self.set_reg(instr[2], val)

	def cmp_gt(self, instr):
		if self.get_reg(instr[1]) > self.get_reg(instr[2]):
			self.set_reg(instr[3], 1)
		else:
			self.set_reg(instr[3], 0)

	def neg(self, instr):
		val = self.get_reg( instr[1] )
		val = -val
		self.regs[ instr[1] ] = val

	def add(self, instr):
		self.regs[ instr[3] ] = self.regs[ instr[1] ] + self.regs[ instr[2] ]

	def jump(self, instr):
		if instr[1] == -1: 
			raise TuringException("Illegal jump!")
		if instr[1] < 0 and not self.conditionnal:
			raise TuringException("Illegal jump (without conditionnal code)!")
		self.do_jump(instr[1])

	def do_jump(self, diff):
		ip = self.instr_pointer + diff
		if ip < 0 or len(self.code) <= ip:
			raise TuringException("Illegal jump (out of code)!")
		self.instr_pointer = ip		
		
	def jumpif(self, instr):
		if instr[2] == -1: 
			raise TuringException("Illegal jump!")
		if self.get_reg( instr[1] ) == 0: return
		self.conditionnal = (instr[2] < 0)
		self.do_jump(instr[2])

	def sub(self, instr):
		self.regs[ instr[3] ] = self.regs[ instr[1] ] - self.regs[ instr[2] ]

	def push(self, instr):
		self.stack.push( self.regs[ instr[1] ] )
	
	def pop(self, instr):
		self.regs[ instr[1] ] = self.stack.pop()

	def store(self, instr):
		self.regs[ instr[1] ] = instr[2]

	def run_instr(self, instr):
		if self.verbose: print "[ip=%u] Exec %s" % (self.instr_pointer, str(instr) )
		func = self.instruction[ instr[0] ][0]
		func (instr)

	def run(self):
		self.instr_pointer = 0
		self.step = 0
		while self.instr_pointer < len(self.code):
			self.run_instr(self.code[self.instr_pointer])
			self.instr_pointer = self.instr_pointer + 1
			self.step = self.step + 1
			if self.max_step < self.step:
				raise TuringException("To much Turing steps!")

	def print_regs(self):
		sys.stdout.write("Regs: ")
		for name,value in self.regs.items():
			sys.stdout.write("%s=%s, " % (name, value))
		print ""

	def print_stack(self):
		if not self.stack.empty():
			s = ""
			for value in self.stack.stack:
				s = s + "%s, " % (value)
		else:
			s = "(empty)"
		print "Stack: %s" % (s)

	def instr2str(self, instr):
		s = instr[0]+"("
		if len(instr) != 0:
			s = s + str(instr[1])
			for arg in instr[2:]: s = s + "," + str(arg)
		return s + ")"
	
	def print_code(self):
		s = ""
		for instr in self.code:
			s = s + " %s;" % self.instr2str(instr)
		print "Code:%s" % (s)
		
	def print_dump(self):
		print ""
		self.print_regs()
		self.print_stack()
		
	def reset_code(self):
		self.code = []

	def reset_stack(self):
		self.stack.reset()

	def reset_regs(self):
		for name in self.regs:
			self.regs[name] = 0


