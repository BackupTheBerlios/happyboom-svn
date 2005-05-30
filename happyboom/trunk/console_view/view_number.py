import time
from view import *

class ViewN(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.value = 1000
		self.msg_handler = {"number": {"Update": self.evtUpdate}}

	def evtUpdate(self, arg):
		arg = arg.split(",")
		if self.id != int(arg[0]): return
		self.value = int(arg[1])
		self.draw(True)

	def live(self):
		self.processMessages()

	def draw(self, force=False):
		if not self.server.verbose or force:
			print "Number[%u]=%i" % (self.id, self.value)

class ViewFollowN(ViewN):
	def __init__(self):
		ViewN.__init__(self)
		self.msg_handler = {"follow": {"Update": self.evtUpdate}}
		
	def evtUpdate(self, arg):
		self.value = int(arg)

	def draw(self):
		print "Follow[%u] --> %i" % (self.id, self.value)
