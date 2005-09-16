from server.bb_agent import Agent, Message
from happyboom.common.log import log

class Weapon(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "weapon", gateway, **args)
        self.angle = 45 
        self.strength = 50
        self.last_values = {}
        self.currentTeam = None
        self.nextTeam = None
        self.registerEvent("gateway")

    def born(self):
        Agent.born(self)
        self.requestRole("command_manager")
        self.requestActions("weapon")
        self.requestActions("game")
        self.requestActions("network")
        self.sendBroadcast(Message("new_item", (self.type, self.id)), "network")

    def msg_game_next_character(self, char, team):
        self.nextTeam = team

    def msg_game_next_turn(self):
        self.last_values[self.currentTeam] = (self.angle, self.strength,)
        self.currentTeam = self.nextTeam
        angle, strength = self.last_values.get(self.currentTeam, (45, 50,))
        self.updateAngle(angle)
        self.updateStrength(strength)

    def updateAngle(self, angle):
        if angle < -80: angle = -80
        elif 80 < angle: angle = 80
        self.angle = angle 
        self.send("setAngle", angle)
        self.sendNetMsg("weapon", "setAngle", angle)

    def msg_weapon_askSetAngle(self, angle):
        self.updateAngle(angle)

    def msg_weapon_askSetStrength(self, strength):
        self.updateStrength(strength)

    def updateStrength(self, strength):
        if strength < 10: strength = 10
        elif 100 < strength: strength = 100
        self.strength = strength
        self.send("setStrength", strength)
        self.sendNetMsg("weapon", "setStrength", strength)

    def evt_gateway_syncClientCreate(self, client):
        self.netCreateItem(client)

    def evt_gateway_syncClient(self, client):
        self.updateStrength(self.strength)
        self.updateAngle(self.angle)
