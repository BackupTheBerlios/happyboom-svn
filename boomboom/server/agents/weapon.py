from server.bb_agent import Agent, Message

class Weapon(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "weapon", gateway, **args)
        self.angle = None
        self.strength = None
        self.last_values = {}
        self.currentTeam = None
        self.nextTeam = None

    def born(self):
        Agent.born(self)
        self.requestRole("command_manager")
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
        self.send("angle", angle)

    def updateStrength(self, strength):
        if strength < 10: strength = 10
        elif 100 < strength: strength = 100
        self.strength = strength
        self.send("strength", strength)

    def sync(self):
        self.updateStrength(self.strength)
        self.updateAngle(self.angle)

    def msg_network_sync(self):
        self.sync()
