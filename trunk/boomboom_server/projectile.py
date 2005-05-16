from server import server_agent
import time
import math

class Projectile(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "projectile")
		self.msg_handler["command"] = {"new": self.evtCommand}
		self.msg_handler["weapon"] = {\
			"angle": self.updateWeaponAngle,
			"force": self.updateWeaponForce}

		self.x, self.y = 0, 0
		self.start_pos = None
		self.active = False
		self.time = None
		self.speed = None
		self.weapon_angle = None
		self.weapon_force = None
		self.mass = 10

	def updateWeaponForce(self, arg):
		self.weapon_force = int(arg)*4
		
	def updateWeaponAngle(self, angle):
		self.weapon_angle = (-int(angle))*math.pi/180

	def evtCommand(self, cmd):
		if cmd == "shoot": self.shoot()

	def setActive(self, active):
		self.active = active
		self.sendMsg("projectile", "activate", "%u" % (active))

	def shoot(self):
		character = self.server.getActiveCharacter()
		if character==None: return
		if self.weapon_angle==None: return
		if self.weapon_force==None: return

		self.start_pos = (character.x, character.y, )
		self.move(character.x, character.y)
		self.setActive (True)
		self.time = time.time()
		sx = self.weapon_force * math.cos(self.weapon_angle)
		sy = self.weapon_force * math.sin(self.weapon_angle)
		if 300<character.x: # TODO: Bad test to know which character it is
			sx = -sx
		self.speed = (sx, sy,)

	def move(self, x, y):
		self.x = x
		self.y = y
		if self.server.world.hitGround(x,y):
			self.setActive(False)
			self.sendMsg("projectile", "hit_ground")
			self.sendMsg("game", "next_turn")
			return
		self.sendMsg("projectile", "move", "%i,%i" % (x,y), skippable=True)

	def live(self):
		server_agent.ServerAgent.live(self)
		if not self.active:return

		dt = time.time() - self.time
		x = self.start_pos[0] +self.speed[0] * dt
		y = self.start_pos[1] +self.speed[1] * dt +9.8*dt*dt*self.mass
		self.move (x, y)

	def sync(self, client):
		self.move(self.x, self.y)
		self.setActive (self.active)
