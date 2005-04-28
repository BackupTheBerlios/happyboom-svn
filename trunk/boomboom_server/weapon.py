from server import server_agent

class Weapon(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "weapon")
		self.msg_handler["command"] = {"new": self.evtCommand}
		self.msg_handler["game"] = {"next_turn": self.nextTurn}
		self.angle = 45
		self.force = 50
		self.keep_data = {}
		self.last_team = 1

	def nextTurn(self, cmd):
		char = self.server.getActiveCharacter()
		if char == None: return
		team = char.team
		self.keep_data[self.last_team] = (self.angle, self.force,)
		angle, force = self.keep_data.get(team, (45, 50,))
		self.last_team = team
		self.updateAngle(angle)
		self.updateForce(force)

	def evtCommand(self, cmd):
		if cmd == "move_left":
			self.updateForce (self.force - 10)
		if cmd == "move_right":
			self.updateForce (self.force + 10)
		if cmd == "move_down":
			self.updateAngle (self.angle - 10)
		if cmd == "move_up":
			self.updateAngle (self.angle + 10)

	def updateAngle(self, angle):
		if angle < -80: angle = -80
		elif 80 < angle: angle = 80
		self.angle = angle 
		self.sendMsg("weapon", "angle", "%s" % (angle))

	def updateForce(self, force):
		if force < 10: force = 10
		elif 100 < force: force = 100
		self.force = force
		self.sendMsg("weapon", "force", "%s" % (force))

	def sync(self, client):
		self.updateForce(self.force)
		self.updateAngle(self.angle)
