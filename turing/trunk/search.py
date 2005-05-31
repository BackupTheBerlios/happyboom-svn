import time
import sys # sys.stdout
from actor import Actor
from turing import Turing
from exception import TuringException
import random

class SearchTuring:
	def __init__(self):
		self.population = 1 
		self.quit = False
		self.step = 0
		self.retest_result = 0
		self.excepted_quality = 0.5
		self.random_vm_func = None
		self.init_vm_func = None
		self.eval_quality_func = None
		self.timeout = 3.0 # seconds
		self.best_quality = -1
		self.best_index = 0 
		self.use_instr = None
		self.use_regs = None
		self.actor = []
		self.vm = Turing()
		self.step_sleep = 0.0

	def load(self, f):
		self.step = f.load()
		self.retest_result = f.load()
		self.excepted_quality = f.load()
		self.best_quality = f.load()
		self.best_index = f.load()
		self.use_instr = f.load()
		self.use_regs = f.load()
		self.population = f.load()
		self.start()
		for actor in self.actor: actor.load(f)
		print "Restore search: step=%u, quality=%.2f%%" % (self.step, self.best_quality)
		
	def getBestActor(self):
		return self.actor[self.best_index]
	best_actor = property(getBestActor)
		
	def save(self, f):
		f.dump(self.step)
		f.dump(self.retest_result)
		f.dump(self.excepted_quality)
		f.dump(self.best_quality)
		f.dump(self.best_index)
		f.dump(self.use_instr)
		f.dump(self.use_regs)
		f.dump(self.population)
		for actor in self.actor: actor.save(f)

	def start(self):
		self.actor = []
		for i in range(self.population):
			actor = Actor(self)
			if self.use_instr != None: actor.code.use_instr = self.use_instr
			if self.use_regs != None: actor.code.use_regs = self.use_regs
			self.actor.append(actor)
	
	def run_actor(self,actor):
		actor.turing.reset_stack()
		actor.turing.reset_regs()
		if self.init_vm_func != None: self.init_vm_func (self, actor)
		try:
			actor.eval()
			actor.quality = self.eval_quality_func (self, actor)
		except TuringException, msg:
			actor.quality = 0.0
		
	def live(self):
		if self.eval_quality_func == None:
			raise Exception("SearchTuring can't live without eval_quality function!")
		self.step = self.step + 1

		if self.random_vm_func != None: self.random_vm_func(self)
	
		quality = {}
		actor_index = 0
		new_best = False
		for actor in self.actor:
			actor_index = actor_index + 1
			actor.name = "Actor %u" % (actor_index)

			if actor.quality==None: self.run_actor(actor)
			
			new_actor = actor.copy()
			nb = random.randint(1,3)
			for i in range(nb):	new_actor.mutation()

			self.run_actor(new_actor)
			take_bad = random.random()
			if take_bad < 0.002 or (actor.quality < new_actor.quality):
				self.actor[actor_index-1] = new_actor
				actor = new_actor
			else:
				continue
			
			if self.best_quality < actor.quality and self.random_vm_func != None:
				test = 0
				new_quality = actor.quality
				while test < self.retest_result and new_quality <= actor.quality:
					self.random_vm_func(self)
					self.run_actor(actor)
					test = test + 1
				if actor.quality < new_quality:
					actor.quality = 0.0
					
			if self.best_quality < actor.quality:
				self.best_quality = actor.quality 
				self.best_index = actor_index-1
				new_best = True

				print "\nNew best quality = %.2f%% (index=%u)" % (self.best_quality, self.best_index)
				print "> Code %s" % (self.best_actor.code.str())

		# Print all codes
#		i = 0
#		for actor in self.actor:
#			i = i + 1
#			if i == self.best_index: sys.stdout.write ("* ")
#			print "%s [%.2f%%] : %s" % (actor.name, actor.quality, actor.code.str())

		self.quit = (self.excepted_quality <= self.best_quality)
		if self.quit:
			print "=== Winner : %s ===" % self.best_actor.name 
			print self.best_actor.code.str()
			print "Quality: %.2f%%" % (self.best_quality)
			return

		if new_best:
			self.actor = [self.best_actor.copy() for i in range(self.population)]
	
	def computeActorQuality(self):
		qmin = qavg = qmax = self.actor[0].quality
		i = 0
		for actor in self.actor[1:]:
			i = i + 1
			if qmin>actor.quality: qmin = actor.quality
			if qmax<actor.quality: qmax = actor.quality
			qavg = qavg + actor.quality
		qavg = float(qavg) / len(self.actor)
		return [qmin, qavg, qmax]

	def run(self):
		self.start()
		t = time.time()
		t_sec = time.time()
		while not self.quit:
			self.live()
			if self.timeout < time.time() - t:
				print "Seach timeout!"
				break
			if 1.0 < time.time() - t_sec:
				t_sec = time.time()
				q = self.computeActorQuality()
				print "\n   Search (step=%u, quality=[%.2f %.2f %.2f] -> %.2f, time=%us) ..." \
					% (self.step, q[0], q[1], q[2], self.best_quality, time.time() - t)
				print "   > Old best code: %s" % (self.best_actor.code.str())
#			time.sleep(0.010)
		print "Step: %u" % (self.step)
