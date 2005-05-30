from view import *
from agent_manager import *
from visual import BoomBoomVisual

class BoomBoomView(BaseView):
	def __init__(self, client):
		BaseView.__init__(self)
		self.visual = BoomBoomVisual()
		self.client = client
		self.game_state = None

	def getActiveCharacter(self):
		if self.game_state==None: return None
		return self.game_state.active_character

	def start(self, host, port):
		BaseView.start(self, host, port)		
		self.visual.start()
		self.registerAgent(0, BoomBoomAgentManager() )
		print "=== BoomBoom ==="
		
	def draw(self):
		self.visual.clear_screen()
		self.visual.render()
