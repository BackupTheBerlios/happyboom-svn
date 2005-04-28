from bb_view import *
from bb_input import *
import pygame
import time

class BoomBoomClient:
	def __init__(self):
		self.view = BoomBoomView(self)
		self.input = BoomBoomInput(self)

	def thread_input(self):
		try:
			while self.view.loop and (not self.input.quit):
				self.input.live()
			self.input.stop()
		except Exception, msg:
			print "INPUT CLIENT EXCEPTION!"
			print "ERROR MSG: %s" % (msg)
			self.input.stop()
			raise
		
	def thread_view(self):
		try:
			while self.view.loop and (not self.input.quit):
				self.view.live()
			self.view.stop()
		except Exception, msg:
			print "VIEW CLIENT EXCEPTION!"
			print "ERROR MSG: %s" % (msg)
			self.view.stop()
			raise

	def start(self, host, view_port, input_port):
		pygame.init()	
		self.view.start(host, view_port)
		self.input.start(host, input_port)
		thread.start_new_thread( self.thread_view, ())
		thread.start_new_thread( self.thread_input, ())

	def live(self):
		time.sleep(0.100)

	def stop(self):
		self.view.stop()
		self.input.stop()