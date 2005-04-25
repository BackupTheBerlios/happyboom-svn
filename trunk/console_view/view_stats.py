import time
from view import *

class NetworkStatAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.in_bytes = 0
		self.out_bytes = 0
		self.time = time.time()
		self.avg_in = 0
		self.avg_out = 0

	def start(self):
		self.server.io.on_read = self.on_read
		self.server.io.on_write = self.on_write

	def on_write(self, data):
		self.out_bytes = self.out_bytes + len(data)

	def on_read(self, data):
		self.in_bytes = self.in_bytes + len(data)

	def draw(self):
		print "Network stat: avg  in=%.1f KB/s out=%.1f KB/s" \
			% (self.avg_in / 1024, self.avg_out / 1024)
		print "Network stat: curr in=%s B, out=%s B" \
			% (self.in_bytes, self.out_bytes)

	def live(self):
		diff = time.time() - self.time
		self.avg_in = self.in_bytes / diff
		self.avg_out = self.out_bytes / diff

class ViewServerStat(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.uptime = None
		self.nb_view = None
		self.nb_input = None
		self.max_inputs = None
		self.max_views = None
		self.net_in = None
		self.net_out = None
		self.msg_handler["server_stat"] = \
			{"Uptime": self.updateUptime,
			 "NetStat": self.updateNetStat, 
			 "NbInput": self.updateNbInput,
			 "MaxInputs": self.updateMaxInputs,
			 "MaxViews": self.updateMaxViews,
			 "NbView": self.updateNbView}

	def updateNetStat(self, arg):
		arg = arg.split(",")
		self.net_in = int(arg[0])
		self.net_out = int(arg[1])
	def updateUptime(self, arg): self.uptime = int(arg)
	def updateMaxViews(self, arg): self.max_views = int(arg)
	def updateMaxInputs(self, arg): self.max_inputs = int(arg)
	def updateNbView(self, arg): self.nb_view = int(arg)
	def updateNbInput(self, arg): self.nb_input = int(arg)

	def draw(self):
		txt = ""
		if self.uptime != None: txt = txt + " uptime=%u sec" % (self.uptime)
		if self.nb_view != None and self.max_views != None:
			txt = txt + " %u/%u view" % (self.nb_view, self.max_views)
		if self.nb_input != None and self.max_inputs != None:
			txt = txt + " %u/%u input" % (self.nb_input, self.max_inputs)
		if txt == "": txt = " Not yet syncronized with server"
		print "Server stat:%s" % (txt)
		
		txt = ""
		if self.net_in != None: txt = txt + " in=%u B" % (self.net_in)
		if self.net_out != None: txt = txt + " out=%u B" % (self.net_out)
		if txt == "": txt = " Not yet syncronized with server"
		print "Server network:%s" % (txt)
