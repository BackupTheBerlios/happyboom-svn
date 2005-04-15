from agent import Agent, AgentMessage

class ViewAgent(Agent):
	def __init__(self):
		Agent.__init__(self)
		self.server = None

	def draw(self):
		pass
