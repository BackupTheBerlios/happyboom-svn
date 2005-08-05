from pysma import ActionAgent, ActionMessage

class BoomBoomMessage(ActionMessage):
	def __init__(self, action, arg, kw={}):
		ActionMessage.__init__(self, action, arg, kw)

class BoomBoomAgent(ActionAgent):
	def __init__(self, type, **args):
		ActionAgent.__init__(self, prefix="msg_")
		self.type = type
		self.__debug = args.get("debug", False)

	def born(self):
		self.requestRole(self.type)

	def requestActions(self, type):
		self.requestRole("%s_listener" %type)
		
	def sendBBMessage(self, message):
		self.sendBroadcastMessage(message, "%s_listener" %self.type)

	def messageReceived(self, msg):
		if self.__debug:
			print "Unhandled message : %s -- %s" %(type(self), msg)