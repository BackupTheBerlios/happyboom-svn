from bb_view import *
from bb_input import *
import pygame

class BoomBoomClient:
	def __init__(self):
		self.view = BoomBoomView(self)
		self.input = BoomBoomInput(self)
	
	def start(self, host, view_port, input_port):
		pygame.init()	
		self.view.start(host, view_port)
		self.input.start(host, input_port)

	def live(self):
		self.view.live()
		self.input.live()

	def stop(self):
		self.view.stop()
		self.input.stop()
