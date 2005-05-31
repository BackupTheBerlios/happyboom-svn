from exception import TuringException

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


