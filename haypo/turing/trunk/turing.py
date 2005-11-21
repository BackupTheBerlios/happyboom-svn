import sys # sys.stdout
from stack import TuringStack
from exception import TuringException

class Turing:
	def __init__(self):
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
		self.step = 0
		self.max_step = 20
		self.code = None

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

	def run(self, code):
		self.instr_pointer = 0
		self.step = 0
		self.code = code
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
	
	def print_dump(self):
		print ""
		self.print_regs()
		self.print_stack()
		
	def reset_stack(self):
		self.stack.reset()

	def reset_regs(self):
		for name in self.regs:
			self.regs[name] = 0
