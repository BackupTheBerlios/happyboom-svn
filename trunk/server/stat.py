import time
import server_agent 

class ServerStat:
	def __init__(self, server):
		self.started = time.time()
		self.server = server
		self.net_in = 0
		self.net_out = 0

	def start(self):
		self.server.getViewIO().on_send = self.onNetSend
		self.server.getInputIO().on_send = self.onNetSend
		self.server.getViewIO().on_read = self.onNetRead
		self.server.getInputIO().on_read = self.onNetRead

	# Event called on new sent/read data from network
	def onNetSend(self, data):
		self.net_out = self.net_out + len(data)
	def onNetRead(self, data):
		self.net_in = self.net_in + len(data)

	# Number of seconds since server started
	def getUptime(self):
		return int( time.time() - self.started )

	# Current/Maximum number of view/input clients
	def getNbInputs(self):
		return len(self.server.getInputIO().clients)
	def getNbViews(self):
		return len(self.server.getViewIO().clients)
	def getMaxViews(self):
		return self.server.getViewIO().max_clients
	def getMaxInputs(self):
		return self.server.getInputIO().max_clients

class ServerStatAgent(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "server_stat")
		self.uptime = None
		self.nb_view = None
		self.nb_input = None
		self.net_in = None
		self.net_out = None
		self.max_views = None
		self.max_inputs = None
		self.net_time = time.time()
		self.net_time_update = 1.0

	def sync(self, client=None):
		if self.uptime != None:
			self.sendMsg("server_stat", "Uptime", "%u" % self.uptime, client)
		if self.max_views != None:
			self.sendMsg("server_stat", "MaxViews", "%u" % self.max_views, client)
		if self.max_inputs != None:
			self.sendMsg("server_stat", "MaxInputs", "%u" % self.max_inputs, client)
		if self.nb_input != None:
			self.sendMsg("server_stat", "NbInput", "%u" % self.nb_input, client)
		if self.nb_view != None:
			self.sendMsg("server_stat", "NbView", "%u" % self.nb_view, client)
		if (self.net_in != None) and (self.net_out != None):
			self.sendMsg("server_stat", "NetStat", "%u,%u" % (self.net_in, self.net_out), client)
	
	def update(self):
		if self.server.stat == None: return
		
		if self.max_views == None:
			self.max_views = self.server.stat.getMaxViews()
		
		if self.max_inputs == None:
			self.max_inputs = self.server.stat.getMaxInputs()
		
		if self.net_time_update < time.time() - self.net_time:
			self.net_time = time.time()
			if (self.server.stat.net_in != self.net_in) \
			or (self.server.stat.net_out != self.net_out):
				self.net_in = self.server.stat.net_in
				self.net_out = self.server.stat.net_out
				self.sendMsg("server_stat", "NetStat", "%u,%u" % (self.net_in, self.net_out,))
		
		input = self.server.stat.getNbInputs()
		if input != self.nb_input:
			self.nb_input = input
			self.sendMsg("server_stat", "NbInput", "%u" % self.nb_input)
		
		view = self.server.stat.getNbViews()
		if view != self.nb_view:
			self.nb_view = view
			self.sendMsg("server_stat", "NbView", "%u" % self.nb_view)

		uptime = self.server.stat.getUptime()
		if uptime != self.uptime:
			self.uptime = uptime
			self.sendMsg("server_stat", "Uptime", "%u" % self.uptime)			

	def live(self):
		self.update()
