from actor import Actor
import time
from turing import TuringException

class SearchTuring:
	def __init__(self):
		self.population = 1 
		self.quit = False
		self.step = 0
		self.excepted_quality = 0.5
		self.random_vm_func = None
		self.init_vm_func = None
		self.eval_quality_func = None
		self.timeout = 3.0 # seconds
		self.best_quality = 0.0

	def start(self):
		self.actor = [Actor() for i in range(self.population)]
	
	def live(self):
		if self.eval_quality_func == None:
			raise Exception("SearchTuring can't live without eval_quality function!")
		self.step = self.step + 1

		if self.random_vm_func != None: self.random_vm_func(self)
	
		quality = {}
		i = 0
		best_quality = -1
		best_actor = None
		for actor in self.actor:
			actor.name = "Actor %u" % (i)
			actor.live()

			# Evaluate algorithm
			actor.vm.reset_stack()
			actor.vm.reset_regs()
			if self.init_vm_func != None: self.init_vm_func (self, actor)
			try:
				actor.eval()
				actor.quality = self.eval_quality_func (self, actor)
			except:# TuringException, msg:
				raise #actor.quality = 0.0
			
			if best_quality < actor.quality:
				best_quality = actor.quality
				best_actor = actor
				best_index = i
			i = i + 1

		self.best_quality = best_quality
#		best_actor.vm.print_code(); time.sleep(0.5)

		self.quit = (self.excepted_quality <= best_quality)
		if self.quit:
			print "=== Winner : %s ===" % best_actor.name 
			best_actor.vm.print_code()
			best_actor.vm.print_stack()
			print "Quality: %.2f%%" % best_quality
			return

		self.actor = [best_actor.copy() for i in range(self.population)]

	def run(self):
		self.start()
		t = time.time()
		t_sec = time.time()
		while not self.quit:
			self.live()
			if self.timeout < time.time() - t:
				print "Seach timeout!!! (unlimited loop?)"
				break
			if 1.0 < time.time() - t_sec:
				t_sec = time.time()
				print "Search (step=%u, quality=%s) ..." \
					% (self.step, self.best_quality)
		print "Step: %u" % (self.step)
