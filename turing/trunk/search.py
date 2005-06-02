import time
import sys # sys.stdout
from actor import Actor
from turing import Turing
from exception import TuringException
import random

class SearchTuring:
	def __init__(self):
		# Mutation arguments
		self.take_bad = 0.001
		self.max_nb_mutation = 5

		# Crossing arguments
		self.cross_quality = 0.50
		if False:
			# Don't use crossing
			self.best_run_crossing = False
			self.nb_cross = 10
			self.next_cross_delta = 20000
		else:
			# Use crossing
			self.best_run_crossing = True 
			self.nb_cross = 20
			self.next_cross_delta = 5 

		# Search arguments
		self.max_steps = 1500
		self.verbose = False 

		# (internal)
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
		self.log = None
		self.next_cross = self.next_cross_delta

	def load(self, f):
		self.step = f.load()
		self.retest_result = f.load()
		self.excepted_quality = f.load()
		self.best_quality = f.load()
		self.best_index = f.load()
		self.use_instr = f.load()
		self.use_regs = f.load()
		self.next_cross = f.load()
		self.population = f.load()
		self.start()
		print "************* LOAD ACTORS"
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
		f.dump(self.next_cross)
		f.dump(self.population)
		for actor in self.actor: actor.save(f)

	def writeLog(self, str):
		self.log.write(str)
		self.log.flush()

	def start(self):
		if len(self.actor) != 0: return

		self.log = open('log', 'w')
		self.writeLog("-------------- START NEW --------------\n\n")
		
		for i in range(self.population):
			actor = Actor(self)
			if self.use_instr != None: actor.code.use_instr = self.use_instr
			if self.use_regs != None: actor.code.use_regs = self.use_regs
			self.actor.append(actor)
	
	def doRunActor(self,actor):
		self.vm.reset_stack()
		self.vm.reset_regs()
		if self.init_vm_func != None: self.init_vm_func (self, actor)
		try:
			actor.eval()
			actor.quality = self.eval_quality_func (self, actor)
		except TuringException, msg:
			actor.quality = -1 

	def runActor(self, actor):
		old_quality = actor.quality

		# Test the actor
		self.doRunActor(actor)
		
		# Shouldn't the actor be retested ?
		if self.random_vm_func == None: return
		if actor.quality < 0: return

		# Retest the actor to be sure of it's quality
		test = 0
		new_quality = actor.quality
		while test < self.retest_result and new_quality <= actor.quality:
			self.random_vm_func(self)
			self.doRunActor(actor)
			test = test + 1
		if actor.quality < new_quality:
			if old_quality != None:
				actor.quality = old_quality
			else:
				actor.quality = -1 
		else:
			actor.quality = new_quality		

	def compareActor(self, a, b):
		return cmp(b.quality, a.quality)

	def crossStartEnd(self, actor):
		code_len = len(actor.code.code)
		if code_len < 2: return (0, 0,)
		start = random.randint(0, code_len-1)
		end = random.randint(0, code_len-1)
		while start == end:
			end = random.randint(0, code_len-1)
		if end < start:
			tmp = end
			end = start
			start = tmp
		return (start, end,)

	def crossTwoActors(self, a, b):
		# Create two children
		childa = a.copy()
		childb = b.copy()

		# Choose part of code to exchange
		a_start, a_end = self.crossStartEnd(a)
		b_start, b_end = self.crossStartEnd(b)
		
		# Exchange part of code
		childa.code.code[a_start:a_end] = b.code.code[b_start:b_end]
		childb.code.code[b_start:b_end] = a.code.code[a_start:a_end]

		# Trunc code to maximum number of instruction
		while a.code.max_instr < len(childa.code.code):
			del childa.code.code[ random.randint(0, len(childa.code.code)-1) ]
		while b.code.max_instr < len(childb.code.code):
			del childb.code.code[ random.randint(0, len(childb.code.code)-1) ]
	
		self.actorMutation(childa)
		self.actorMutation(childb)

		childa.quality = None
		self.runActor(childa)
		childb.quality = None 
		self.runActor(childb)
		return (childa, childb,)

	# Cross actors to produce new children
	def crossActors(self):
		self.updateLog()
		self.writeLog("   *** Cross ***\n")
		self.actor.sort(self.compareActor)
		self.best_index = 0
		children = []
		for i in range(self.nb_cross):
			# Cross one good and one bad actor
			a = random.randint(0, self.cross_quality * self.population)
			b = random.randint(0, self.cross_quality * self.population)
#			b = random.randint(self.cross_quality * self.population, self.population-1)
			while a == b:
				b = random.randint(0, self.cross_quality * self.population)
#				b = random.randint(self.cross_quality * self.population, self.population-1)
			
			a = self.actor[a]
			b = self.actor[b]
			childa, childb = self.crossTwoActors(a,b)
			children.append( childa )			
			children.append( childb )

		if False:
			# Insert randomly children
			while 0<len(children):
				self.actor.insert( random.randint(0, len(self.actor)-1), children[-1] )
				del children[-1]
		else:
			# Only keep best actors in new population
			self.actor.extend(children)
			self.actor.sort(self.compareActor)
		del self.actor[self.population:]

		self.actor.sort(self.compareActor)
		self.best_index = 0
		self.updateLog()

	def actorMutation(self, actor):
		actor.quality = None
		nb = random.randint(1,self.max_nb_mutation)
		for i in range(nb):	actor.mutation()

	# Search new best actor in population
	# Return True is new best actor is found
	def searchNewBest(self):
		actor_index = 0
		new_best = False
		for actor in self.actor:							
			if self.best_quality < actor.quality:
				self.best_quality = actor.quality 
				self.best_index = actor_index
				new_best = True

				if self.verbose and 0 < self.best_quality:
					print "\n[Step %u] New best quality = %.2f%% (actor %u)" % (self.step, self.best_quality, self.best_index)
					print "> Code %s" % (self.best_actor.code.str())
					self.writeLog ("  New best actor (%s:%.2f).\n" % (self.best_index, self.best_actor.quality))
			actor_index = actor_index + 1
		return new_best

	# Eval all actors
	def evalActors(self):
		if self.random_vm_func != None: self.random_vm_func(self)
	
		actor_index = 0 
		for actor in self.actor:
			if actor.quality == None: self.runActor(actor)

			# Do mutation on actor
			new_actor = actor.copy()
			self.actorMutation(new_actor)
			self.runActor(new_actor)
			
			# Is the new actor better ?
			take_bad = random.random()
			if take_bad < self.take_bad or (actor.quality < new_actor.quality):
				if take_bad < self.take_bad:
					self.writeLog ("  Take bad.\n")
				self.writeLog ("  Change actor %u.  -  " % actor_index)
				self.writeLog (" %.5f/%.5f :: %.2f/%.2f\n" % \
					(take_bad, self.take_bad, actor.quality, new_actor.quality))
				self.actor[actor_index] = new_actor
				actor = new_actor

			actor_index = actor_index + 1
		return self.searchNewBest()
		
	def live(self):
		# New search step
		self.step = self.step + 1

		# Eval actors quality
		new_best = self.evalActors()

		# Need to cross actors ?
		if self.next_cross < self.step or (new_best and self.best_run_crossing):
			self.next_cross = self.step + self.next_cross_delta
			self.crossActors()
			self.searchNewBest()
		else:
			self.updateLog()

		# Quit ?
		self.quit = (self.excepted_quality <= self.best_quality)
	
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

	def updateLog(self):
		self.writeLog ("%04u) " % (self.step))
		for actor in self.actor:
			self.writeLog ("%.2f  " % actor.quality)
		self.writeLog ("\n")

	def printDump(self):
		self.writeLog("\n")
		i = 0
		for actor in self.actor:
			self.writeLog("=== Actor %u ===\n" % i)
			#self.writeLog("Quality = %.2f\n" % actor.quality)
			self.writeLog("Quality = %.2f" % actor.quality)
			if actor.quality<0.50:
				self.writeLog("<0.5\n")
			else:
				self.writeLog(">=0.5\n")
			self.writeLog("Code : %s\n" % actor.code.str())
			i = i + 1

	def run(self):
		try:
			self.doRun()
		except KeyboardInterrupt:
			print "Step (interrupted): %u" % (self.step)
			self.printDump()
			self.log.close()
			raise
		self.printDump()
		self.log.close()
			
	def doRun(self):
		self.start()
		t = time.time()
		t_sec = time.time()

		# Main loop
		local_step = 0
		while not self.quit:
			local_step = local_step + 1
			self.live()
#			if self.timeout < time.time() - t:
#				print "Seach timeout!"
#				break
			if self.max_steps < local_step:
				print "*********** Seach timeout (too much steps)! ************"
				break
#			if 1.0 < time.time() - t_sec:
#				t_sec = time.time()
#				q = self.computeActorQuality()
#				print "\n   Search (step=%u, quality=[%.2f %.2f %.2f] -> %.2f, time=%us) ..." \
#					% (self.step, q[0], q[1], q[2], self.best_quality, time.time() - t)
#				print "   > Old best code: %s" % (self.best_actor.code.str())
#			time.sleep(0.010)

		# End
		if self.quit:
			if self.verbose: print "=== Winner : %u ===" % self.best_index
			print "Code : %s" % (self.best_actor.code.str())
			print "Quality: %.2f%%" % (self.best_quality)
		print "Step: %u" % (self.step)
