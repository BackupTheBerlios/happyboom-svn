from view import *

class ViewChat(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.msg_handler["chat"] = {"message": self.onMessage}
		self.messages = []
		self.log_message = 5 

	def onMessage(self, msg):
		if len(self.messages)==self.log_message: del self.messages[0]
		self.messages.append(msg)
		if self.server.verbose: print "Chat: ",msg

	def draw(self):
		if len(self.messages) != 0 and (not self.server.verbose):
			print "Chat :"
			for msg in self.messages:
				print "* %s" % (msg)
