from input import * 
import pygame

class BoomBoomInput(BaseInput):
	def __init__(self, client):
		BaseInput.__init__(self)
		self.client = client

	def process_event_active(self, character, event):
		delta_angle = -30 
		if event.type == pygame.KEYDOWN: 
			# arrow keys: move character
			if event.key == 9: self.sendCmd("next_character")
			elif event.key == 275: self.sendCmd("move_right")
			elif event.key == 273: self.sendCmd("move_up") 
			elif event.key == 274: self.sendCmd("move_down")
			elif event.key == 276: self.sendCmd("move_left")

	def process_event(self, event):
		if event.type == pygame.KEYDOWN: 
			# q, Q or escape: quit
			if event.unicode in (u'q', u'Q'): self.quit = True
			elif event.key == 27: self.quit = True			
		# Quit event: quit
		elif event.type in (pygame.QUIT, ): self.quit = True
	
		character = self.client.view.getActiveCharacter()
		if character != None: self.process_event_active(character, event)

	def live(self):
		for event in pygame.event.get():
			if self.process_event(event)==False: self.quit = True
