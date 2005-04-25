from input import *

class ConsoleInput(BaseInput):
	def __init__(self):
		BaseInput.__init__(self)
		self.cmd_ok = ("quit", "+", "-")
