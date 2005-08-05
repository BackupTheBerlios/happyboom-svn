from server.bb_agent import BoomBoomAgent, BoomBoomMessage
import time
import math

class Projectile(BoomBoomAgent):
	def __init__(self, **args):
		BoomBoomAgent.__init__(self, "projectile", **args)
		self.x, self.y = 0, 0
		self.start_pos = None
		self.active = False
		self.time = None
		self.speed = None
		self.weapon_angle = None
		self.weapon_strength = None
		self.mass = 10

	def born(self):
		BoomBoomAgent.born(self)
		self.requestRole("command_manager")
		self.requestActions("weapon")
		self.requestActions("character")
		self.requestActions("world")
		self.requestActions("game")
		self.requestActions("network")
		self.sendBroadcastMessage(BoomBoomMessage("new_item", (self.type, self.id)), "network")

	def msg_weapon_strength(self, arg):
		self.weapon_strength = int(arg) * 4
		
	def msg_weapon_angle(self, angle):
		self.weapon_angle = (-int(angle)) * math.pi / 180

	def msg_new_command(self, cmd):
		if cmd == "shoot" and not self.active:
			self.shoot()

	def msg_character_active_coord(self, x, y):
		self.start_pos = (x, y)

	def msg_world_collision(self, x, y):
		self.setActive(False)

	def setActive(self, active):
		self.active = active
		self.sendBBMessage("activate", active)

	def shoot(self):
		if self.weapon_angle==None: return
		if self.weapon_strength==None: return
		self.move(self.start_pos[0], self.start_pos[1])
		self.setActive(True)
		self.time = time.time()
		sx = self.weapon_strength * math.cos(self.weapon_angle)
		sy = self.weapon_strength * math.sin(self.weapon_angle)
		if self.start_pos[0] > 300: # TODO: Bad test to know which character it is
			sx = -sx
		self.speed = (sx, sy,)

	def move(self, x, y):
		self.x = x
		self.y = y
		self.sendBBMessage("move", x, y)

	def live(self):
		BoomBoomAgent.live(self)
		if self.active:
			dt = time.time() - self.time
			x = self.start_pos[0] +self.speed[0] * dt
			y = self.start_pos[1] +self.speed[1] * dt +9.8*dt*dt*self.mass
			self.move (x, y)

	def sync(self):
		self.setActive(self.active)

	def msg_network_sync(self):
		self.sync()