from actor import Actor
import time
import sys # sys.stdout
from turing import TuringException
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
		self.best_index = None
		self.best_actor = None
		self.use_instr = None
		self.use_regs = None
		self.actor = []

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
		self.best_actor = self.actor[self.best_index]
		print "Restore search: step=%u, quality=%.2f%%" % (self.step, self.best_quality)
		
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
			actor = Actor()
			if self.use_instr != None: actor.use_instr = self.use_instr
			if self.use_regs != None: actor.use_regs = self.use_regs
			self.actor.append(actor)
	
	def run_actor(self,actor):
		actor.vm.reset_stack()
		actor.vm.reset_regs()
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
		i = 0
		new_best = False
		for actor in self.actor:
			actor.name = "Actor %u" % (i)

			nb = random.randint(1,3)
			for i in range(nb):	actor.mutation()

			self.run_actor(actor)

			new_quality = actor.quality
			if 0 <= self.best_quality and self.best_quality < new_quality and self.random_vm_func != None:
				test = 0
				while test < self.retest_result and new_quality <= actor.quality:
					self.random_vm_func(self)
					self.run_actor(actor)
					test = test + 1
				if actor.quality < new_quality: new_quality = -1

			if self.best_quality < new_quality:
				self.best_quality = new_quality 
				self.best_actor = actor
				self.best_index = i
				new_best = True

				print "New best quality = %.2f%%" % (self.best_quality)
				self.best_actor.vm.print_code()

			i = i + 1

#		best_actor.vm.print_code();
#		if self.best_quality>=0.25:
#			print "Step %u" % (self.step)
#			self.actor[self.best_index].vm.print_code()
#			time.sleep(0.250)

		self.quit = (self.excepted_quality <= self.best_quality)
		if self.quit:
			print "=== Winner : %s ===" % self.best_actor.name 
			actor = self.best_actor.copy()
			actor.vm.reset_stack()
			actor.vm.reset_regs()
			if self.init_vm_func != None: self.init_vm_func (self, actor)
			sys.stdout.write("Initial ")
			actor.vm.print_regs()

			self.best_actor.vm.print_code()
			self.best_actor.vm.print_stack()
			self.best_actor.vm.print_regs()

			print "Quality: %.2f%%" % (self.best_quality)
			return

		if new_best:
			self.actor = [self.best_actor.copy() for i in range(self.population)]

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
				print "Search (step=%u, quality=%.2f, time=%us) ..." \
					% (self.step, self.best_quality, time.time() - t)
			time.sleep(0.010) # CPU limit for laptop :-)
		print "Step: %u" % (self.step)
