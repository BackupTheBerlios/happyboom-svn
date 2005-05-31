from search import SearchTuring
from test import *
import pickle
import os # os.remove

class MainIA:
	def __init__(self):
		self.x = 0
		self.search_func = None
		self.search = SearchTuring()
		self.test_name = "add"
		self.first_run = True
		self.valid_test = { \
			"add": test_add,
			"add3": test_add3,
			"sign": test_sign}

	def init(self, arg):
		self.test_name = arg["test"]
		self.search_func = self.valid_test[self.test_name]
		self.load()

	def stateFilename(self):
		return self.test_name+"_state"

	def load(self):
		filename = self.stateFilename()
		try:
			f = open(filename, 'r')
		except IOError, code:
			return
			
		print "Load ia from %s." % (filename)
		try:
			unpick = pickle.Unpickler(f)
			self.test_name = unpick.load()
			self.search.load(unpick)
			self.first_run = False
		except EOFError:
			print "Load error."

	def save(self):
		filename = self.stateFilename()

		# Result found : remove old state
		if self.search.quit:
			try:
				os.remove(filename)
			except:
				pass
			return

		# Save state
		print "Save ia into %s." % (filename)
		try:
			f = open(filename, 'w')
		except IOError, code:
			print "Can't save state :-("
			return
		pick = pickle.Pickler(f)
		pick.dump(self.test_name)
		self.search.save(pick)

	def run(self):
		try:
			if self.search_func == None:
				raise Exception("Invalid search function")
			self.search_func (self)
		except KeyboardInterrupt:
			pass
		self.save()
