from agent_manager import *
from view import *

class ConsoleView(BaseView):
	def start(self, host, port):
		BaseView.start(self, host, port)
		self.registerAgent(0, ConsoleAgentManager() )

	def draw(self):
		if self.clear_screen:
			print "\33[2J\33[1;1H"
			print "=== HappyBoom text viewer ==="
		for key in self.agents:	
			agent = self.agents[key]
			agent.draw()
