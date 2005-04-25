from view import *

class DebugMsgAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.last_msg = []
		self.total_msg = 0
		self.keep_msg_nb = 10

	def start(self):
		self.server.on_recv_message = self.receiveMsg

	def receiveMsg(self, msg):
		self.total_msg = self.total_msg + 1
		if self.keep_msg_nb <= len(self.last_msg):
			del self.last_msg[0]
		self.last_msg.append (msg)
		if self.server.verbose:
			print "New messages : %s" % (msg.str())

	def draw(self):
		if self.server.verbose: return
		print "Last messages (total=%u) :" % (self.total_msg)
		for msg in self.last_msg:
			print "* %s" % (msg.str())
