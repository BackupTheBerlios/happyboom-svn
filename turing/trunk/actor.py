from code import TuringCode

class Actor:
	def __init__(self, turing, copy=None):
		self.turing = turing
		if copy==None:
			self.code = TuringCode(self.turing)
			self.step = 0
			self.verbose = False
			self.name = "no name"
			self.quality = 0.0
		else:
			self.code = copy.code.copy()
			self.step = copy.step
			self.name = copy.name
			self.verbose = copy.verbose
			self.quality = copy.quality

	def copy(self):
		return Actor(self.turing, copy=self)

	def load(self, f):
		self.step = f.load() 
		self.name = f.load()
		self.verbose = f.load()
		self.quality = f.load()
		self.code.load (f)

	def save(self, f):
		f.dump( self.step ) 
		f.dump( self.name )
		f.dump( self.verbose )
		f.dump( self.quality )
		self.code.save(f)

	def eval(self):
		self.step = self.step + 1
		if self.verbose: print "Actor step %u" % (self.step)
		self.code.run()

	def mutation(self):
		self.code.mutation()
