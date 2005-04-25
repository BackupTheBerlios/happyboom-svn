class AgentMessage:
	def __init__(self, role, type, arg):
		self.role = role
		self.type = type
		self.arg  = arg
		self.id = -1
		self.msg_handler = {}

	def str(self):
		if self.arg != None:
			return "Message(role=%s, type=%s, arg=%s)" % (self.role, self.type, self.arg)
		else:
			return "Message(role=%s, type=%s)" % (self.role, self.type)

class Agent(object):
	def __init__(self):
		self.mailbox = []
		self.msg_handler = {}

	def hasMessage(self):
		return len(self.mailbox) != 0
		
	def putMessage(self, msg):
		self.mailbox.append(msg)
		
	def getMessage(self):
		if not self.hasMessage(): return None
		msg = self.mailbox[0]
		del self.mailbox[0]
		return msg

	def processMessages(self):
		while self.hasMessage():
			msg = self.getMessage()
			if self.msg_handler.has_key(msg.role):
				handlers = self.msg_handler[msg.role]
				if handlers.has_key(msg.type):
					hdl = handlers[msg.type]	
					hdl(msg.arg)
		
	def start(self):
		for key in self.msg_handler:
			self.server.registerMessage(self, key)

	def live(self):
		self.processMessages()
