import pygame
import random
import threading
import numpy as np
import opc

class Portal(object):
	def __init__(self, faction = 'neutral', level = '0', buf = 2048):
		#
		#---PYGAME SOUNDS---------
		#
		#init pygame mixer if needed--------------
		if pygame.mixer.get_init() == None:
			pygame.mixer.pre_init(44100, -16, 2, buf)
			pygame.mixer.init()
		#audio params, time in ms
		self.fadeTime = 4000
		self.fxInterval = [2500,6500]
		self.fx_vol = 0.9
		
		#set up soundbanks
		#ENL soundbank
		self.wraith = pygame.mixer.Sound('./sounds/sfx_ambient_alien_wraith.ogg')
		self.wraith2 = pygame.mixer.Sound('./sounds/sfx_ambient_alien_wraith_alt.ogg')
		self.static = pygame.mixer.Sound('./sounds/sfx_ambient_alien_static.ogg')
		self.heartbeat = pygame.mixer.Sound('./sounds/sfx_ambient_alien_heartbeat.ogg')
		
		#common
		self.beeps = pygame.mixer.Sound('./sounds/sfx_ambient_scanner_beeps.ogg')
		self.ring = pygame.mixer.Sound('./sounds/sfx_ambient_scanner_ring.ogg')
		self.swell = pygame.mixer.Sound('./sounds/sfx_ambient_scanner_swell.ogg')
		self.wind = pygame.mixer.Sound('./sounds/sfx_ambient_scanner_wing.ogg')
		
		#RES soundbank
		self.energy =  pygame.mixer.Sound('./sounds/sfx_ambient_human_energy_pulse.ogg')
		self.pulse_stereo =  pygame.mixer.Sound('./sounds/sfx_ambient_human_pulsing_stereo.ogg')
		self.pulse_warm =  pygame.mixer.Sound('./sounds/sfx_ambient_human_pulsing_warm.ogg')
		self.crystal =  pygame.mixer.Sound('./sounds/sfx_ambient_human_crystal.ogg')
		
		#NEUTRAL soundbank
		self.n_crystal =  pygame.mixer.Sound('./sounds/sfx_ambient_neutral_crystal.ogg')
		self.impacts =  pygame.mixer.Sound('./sounds/sfx_ambient_neutral_impacts.ogg')
		self.whale =  pygame.mixer.Sound('./sounds/sfx_ambient_neutral_whale.ogg')
		self.whale_alt =  pygame.mixer.Sound('./sounds/sfx_ambient_neutral_whale_alt.ogg')
		
		#banks
		self.enl = [self.wraith, self.wraith2, self.static, self.heartbeat, self.beeps, self.ring, self.swell, self.wind]
		self.res = [self.energy, self.pulse_stereo, self.pulse_warm, self.crystal, self.beeps, self.ring, self.swell, self.wind]
		self.neu = [self.n_crystal, self.impacts, self.whale, self.whale_alt, self.beeps, self.ring, self.swell, self.wind]
		
		
		#triggered on action sounds
		self.reso_deploy = pygame.mixer.Sound('./sounds/sfx_resonator_power_up.ogg')
		
		#-----LIGHTS-------
		#
		#---------define Fadecandy OPC Client--------------
		ADDRESS = 'localhost:7890'

		# Create a client object
		client = opc.Client(ADDRESS)

		# Test if it can connect
		if client.can_connect():
			print 'connected to %s' % ADDRESS
		else:
		    # We could exit here, but instead let's just print a warning
		    # and then keep trying to send pixels in case the server
		    # appears later
		    raise Warning('WARNING: could not connect to %s' % ADDRESS)
		
		#--setup lighting color vars etc
		#
		#colors is rgb for L1-L8
		colors = [(255, 240, 0),(255, 200, 22),(239, 113, 2),(242, 4, 40),(255, 0, 144),(255, 0, 220),(229, 29, 226),(171, 15, 188)]
		blk = [(0,0,0)]
		
		
		pixels = []     #TODO: list of lists to hold all pixels for all resos?
		link_len = 64   #num of LEDs in link, fadecandy max 64 per channel
		    
		#-----OTHER PORTAL PROPERTIES & VARS
		#   
		#set starting portal properties
		self.faction = faction
		self.level = level
		self._fxplay = False
		self.resos = [[0,0,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0]]
		
		
	
	#get/set FACTION
	def get_faction(self):
		return self.faction
	def set_faction(self, faction):
		if faction != self.faction:
			if pygame.mixer.music.get_busy():
				pygame.mixer.fadeout(self.fadeTime)
				self.faction = faction
				self.play_music()
			else:
				self.faction = faction
			return 1
		else:
			return 0
		
	
	#RESOS & PORTAL LEVEL
	# - Resos are stored as the 2d array: resos[reso_level,reso_health]
	# - Array position corresponds to reso slot, starting with reso[0]
	#   as the North slot (red dot in scanner), proceeding clockwise
	#    - get_level() recalculates the portal level from deployed resos,
	#      and returns level as int
	#    - deploy_resos(reso_slot,reso_level) adds a reso at full health &
	#      triggers deploy FX
	#    - 
	def get_level(self):
		self._lvl = np.sum(self.resos[0],dtype='float16')/8
		if 0 < self._lvl < 1:
			self.level = 1
		else:
			self.level = int(self._lvl)
		return self.level
		#set-brightness based on health?	
	def deploy_reso(self, loc, rank):
		if rank < 0 or rank > 8:
			raise Warning('Invalid Resonator Level - Not Deployed')
		elif rank <= self.resos[0][loc]:
			raise Warning('Deploy Failed - Not an Upgrade')
		else:
			#reso deploy code here
			o = ''
			self.resos[0][loc] = rank
			self.resos[1][loc] = 100
			self.reso_deploy.play()
			pixels = colors[rank]*link_len
			if client.put_pixels(pixels, channel=loc):
				o = 'sent'
			else:
				o = 'not connected'
			return o + self.get_level()
	def get_resos(self):
		return self.resos
	
			
	#PLAY BACKGROUND loop for current faction
	def play_music(self, vol = 1.0):
		if self.faction == 'enlightened':
			self.music = './sounds/sfx_ambient_alien_base.ogg'
		elif self.faction == 'resistance':
			self.music = './sounds/sfx_ambient_human_base.ogg'
		else:
			self.music = './sounds/sfx_ambient_neutral_base.ogg'
		
		pygame.mixer.music.load(self.music)
		pygame.mixer.music.set_volume(vol)
		pygame.mixer.music.play(-1)
	
	def get_music_volume(self):
		return pygame.mixer.music.get_volume()
		
	def set_music_volume(self, mv):
		pygame.mixer.music.set_volume(mv)
		return pygame.mixer.music.get_volume()
	
	def play_fx(self):
		self._fxplay = True
		self.fx = threading.Thread(target=self.fx_loop)
		self.fx.start()
		
	def stop_fx(self, fade = True):
		self._fxplay = False
		if fade == True:
			pygame.mixer.fadeout(self.fadeTime)
			pygame.mixer.music.fadeout(self.fadeTime)
		else:
			pygame.mixer.stop()
			pygame.mixer.music.stop()
		self.fx.join(5000)
	
	def fx_loop(self):
		while self._fxplay:
			pygame.time.wait(random.randrange(self.fxInterval[0],self.fxInterval[1]))
			if self.faction == 'enlightened':
				self.fac = self.enl
			elif self.faction == 'resistance':
				self.fac = self.res
			else:
				self.fac = self.neu
			self.snd = random.choice(self.fac)
			self.snd.set_volume(self.fx_vol)
			self.faded_len = int((self.snd.get_length()*1000)-35)
			self.snd.play(0,0,self.faded_len)
			
	def set_fx_volume(self, fxv):
		self.fx_vol = fxv
		return self.fx_vol
