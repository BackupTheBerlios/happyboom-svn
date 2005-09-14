from server.bb_agent import BoomBoomAgent, BoomBoomMessage

class Weapon(BoomBoomAgent):
    def __init__(self, **args):
        BoomBoomAgent.__init__(self, "weapon", **args)
        self.angle = None
        self.strength = None
        self.last_values = {}
        self.currentTeam = None
        self.nextTeam = None

    def born(self):
        BoomBoomAgent.born(self)
        self.requestRole("command_manager")
        self.requestActions("game")
        self.requestActions("network")
        self.sendBroadcastMessage(BoomBoomMessage("new_item", (self.type, self.id)), "network")

    def msg_game_next_character(self, char, team):
        self.nextTeam = team

    def msg_game_next_turn(self):
        self.last_values[self.currentTeam] = (self.angle, self.strength,)
        self.currentTeam = self.nextTeam
        angle, strength = self.last_values.get(self.currentTeam, (45, 50,))
        self.updateAngle(angle)
        self.updateStrength(strength)

    def msg_new_command(self, cmd):
        if cmd == "move_left":
            self.updateStrength (self.strength - 5)
        if cmd == "move_right":
            self.updateStrength (self.strength + 5)
        if cmd == "move_down":
            self.updateAngle (self.angle - 5)
        if cmd == "move_up":
            self.updateAngle (self.angle + 5)

    def updateAngle(self, angle):
        if angle < -80: angle = -80
        elif 80 < angle: angle = 80
        self.angle = angle 
        self.sendBBMessage("angle", angle)

    def updateStrength(self, strength):
        if strength < 10: strength = 10
        elif 100 < strength: strength = 100
        self.strength = strength
        self.sendBBMessage("strength", strength)

    def sync(self):
        self.updateStrength(self.strength)
        self.updateAngle(self.angle)

    def msg_network_sync(self):
        self.sync()