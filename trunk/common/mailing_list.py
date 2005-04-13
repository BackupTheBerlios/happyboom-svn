class MailingList:
	def __init__(self):
		self.local_list = {}
		self.net_list = {}
		
	def _register(self, list, role, value):
		if list.has_key(role):
			list[role].append (value)
		else:
			list[role] = [value]

	def register(self, role, agent):
		self._register(self.local_list, role, agent)
		
	def registerNet(self, role, client):
		self._register(self.net_list, role, client)

	def __get(self, list, role):
#		if role == "*":
#			big = []
#			for key in list: big = big + list[key]
#			return big		
		if not list.has_key(role): return []
		return list[role]

	def getLocal(self, role):
		return self.__get(self.local_list, role)
		
	def getNet(self, role):
		return self.__get(self.net_list, role)
