import pygame
import random
import threading
import numpy as np
import opc
import time
import serial

class Portal(object):
	def __init__(self, faction = 'neutral', level = 1, start_fcclient = True, start_serial = True):
		#
		#---PYGAME SOUNDS---------
		#
		self._buf = 2048
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
		#speech = pygame.mixer.Channel(7)
		
		#triggered on action sounds
		self.reso_deploy = pygame.mixer.Sound('./sounds/sfx_resonator_power_up.ogg')
		self.ada_portal = pygame.mixer.Sound('./sounds/speech_portal_en.ogg')
		self.ada_online = pygame.mixer.Sound('./sounds/speech_online_en.ogg')
		self.ada_goodwork = pygame.mixer.Sound('./sounds/speech_good_work_en.ogg')
		
		#-----Start HW Interfaces
		if start_fcclient:
			init_fcclient(ADDRESS_2='') #init only FC board 1 until we have both set up
			init_serial() #Set USB serial port here if necessary
		
		#--setup lighting color vars etc
		#
		#colors is rgb for L1-L8
		self.colors = [(254, 206, 0),(255, 168, 48),(255, 115, 21),(228, 0, 0),(253, 41, 146),(235, 38, 205),(193, 36, 224),(150, 39, 244)]
		self.blk = [(0,0,0)]
		
		
		self.link_len = 64   #num of LEDs in link, fadecandy max 64 per channel
		self.start_channel = 0
		self.pixels = self.blk*512
		self.pixels2 = self.blk*512   #TODO: list of lists to hold all pixels for all resos?
		self.client.put_pixels(self.pixels) #TODO: channel=all
		self.client.put_pixels(self.pixels)
		self.client2.put_pixels(self.pixels)
		self.client2.put_pixels(self.pixels)
		
		#-----OTHER PORTAL PROPERTIES & VARS
		#   
		#set starting portal properties
		self.faction = faction
		self._faclist = ['neu','enl','res']
		self.level = level
		self._lvl = np.sum(self.resos[0],dtype='float16')/8
		self._fxplay = False
		self.resos = [[0,0,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0]]
	
	#-----LIGHTS-------
	#
	#---------define Fadecandy OPC Client--------------
	def init_fcclient(self, ADDRESS_1 = 'localhost:7890', ADDRESS_2 = 'localhost:7891'):
		
		# Create a client object
		self.client = opc.Client(ADDRESS_1)
		if ADDRESS_2:
			self.client2 = opc.Client(ADDRESS_2)

		# Test if it can connect
		if self.client.can_connect():
			print 'connected to %s' % ADDRESS_1
		else:
		    # We could exit here, but instead let's just print a warning
		    # and then keep trying to send pixels in case the server
		    # appears later
		    print 'WARNING: could not connect to %s... Is fcserver running?\nClient will retry connection each time a pixel update is sent' % ADDRESS_1
		if self.client2.can_connect():
			print 'connected to %s' % ADDRESS_2
		else:
		    # We could exit here, but instead let's just print a warning
		    # and then keep trying to send pixels in case the server
		    # appears later
		    print 'WARNING: could not connect to %s... Is fcserver running?\nClient will retry connection each time a pixel update is sent' % ADDRESS_2
		self.clients = [self.client,self.client2]
	
	def init_serial(self, port = '/dev/ttyUSB0'):
		#----serial interface to Arduino for DMX & Relay switch
		## MAKE SURE TO SET USB PORT FOR CURRENT SYTEM CONFIG!!! 
		self.srl = serial.Serial(port,9600)
		print 'Using serial port %s' % self.srl.name	
	
	#get/set FACTION
	def get_faction(self):
		return self.faction
	
	def set_faction(self, faction):
		if faction != self.faction and (faction in _faclist):
			if pygame.mixer.music.get_busy():
				pygame.mixer.fadeout(self.fadeTime)
				self.faction = faction
				self.play_music()
			else:
				self.faction = faction
			if self.srl.name:
				self.srl.write(self._fac(self.faction))
				if self. faction == 'neutral':
					self.srl.write(bytes(5))
				print 'Faction lighting set to %s' % self.faction
			else:
				print 'Serial connection not enabled, lighting data not set'
			return self.faction
		else:
			return 0
	
	def _fac(self, f):  # 
		return {
			'neu' : bytes('n'),
			'enl' : bytes('e'),
			'res' : bytes('r'),
		}[f]	
	
	#RESOS & PORTAL LEVEL
	# - Resos are stored as the 2d array: resos[reso_level,reso_health]
	# - Array position corresponds to reso slot, starting with reso[0]
	#   as the North slot (red dot in scanner), proceeding clockwise
	#    - get_level() recalculates the portal level from deployed resos,
	#      and returns level as int
	#    - deploy_reso(reso_slot,reso_level) adds a reso at full health &
	#      triggers deploy FX
	#    - 
	def get_level(self):
		self._lvl = np.sum(self.resos[0],dtype='float16')/8
		if self._lvl < 1:
			self.level = 1
		else:
			self.level = int(self._lvl)
		return self.level
		#set-brightness based on health?	
	def deploy_reso(self, loc, rank):
		if rank < 1 or rank > 8:
			raise Warning('Invalid Resonator Level - Not Deployed')
		elif rank <= self.resos[0][loc]:
			raise Warning('Deploy Failed - Not an Upgrade')
		else:
			#reso deploy code here
			o = ''
			self.resos[0][loc] = rank
			self.resos[1][loc] = 100
			self.reso_deploy.play()
			if 0 <= loc <= 2 or loc == 7:
				if self.client.put_pixels(self.pixels):
					self.set_pixel_range(loc)			
					for i in range(self.start_channel,self.start_channel + self.link_len):
						self.pixels[i] = self.colors[rank-1]
						self.client.put_pixels(self.pixels)
						time.sleep(0.05)
					self.client.put_pixels(self.pixels)
					if self._lvl==0:
						self.ada_portal.play()
						time.sleep(self.ada_portal.get_length())
						self.ada_online.play()
						time.sleep(self.ada_online.get_length())
						self.ada_goodwork.play()
					o = 'sent'
				else:
					o = 'Fadecandy1 not connected'
				self.get_level()
				return o
			elif 3 >= loc <= 6:
				if self.client2.put_pixels(self.pixels2):
					self.set_pixel_range(loc)
					for i in range(self.start_channel,self.start_channel + self.link_len):
						self.pixels2[i] = self.colors[rank-1]
						self.client.put_pixels2(self.pixels)
						time.sleep(0.05)
					self.client2.put_pixels(self.pixels)
					if self._lvl==0:
						self.ada_portal.play()
						time.sleep(self.ada_portal.get_length())
						self.ada_online.play()
						time.sleep(self.ada_online.get_length())
						self.ada_goodwork.play()
					o = 'sent'
				else:
					o = 'Fadecandy1 not connected'
				self.get_level()
				return o
	def get_resos(self):
		return self.resos
	def destroy_reso(self, loc):
		self.resos[0][loc] = 0
		self.resos[1][loc] = 0
		self.b = 255
		while self.b >= 20:
			self.set_pixel_range(loc)
			self.put_px_range(self.start_channel, self.link_len, (self.b,self.b,self,b), self.fadecandy)
			time.sleep(0.1)
			self.put_px_range(self.start_channel, self.link_len, self.blk, self.fadecandy)
			self.b = self.b/2
	def set_reso_health(self, loc, health):
		if health < 100:
			raise Warning('Invalid Health Value %h for Reso %l : Health not set' % health,loc)
		elif health <= 0:
			self.destroy_reso(loc)
			print 'Reso %l destroyed' % loc+1
		else:
			self.resos[1][loc] = health
			#TODO set link brightness based on health
			return	'Reso %r=%l,%h' % loc,self.resos[0][loc],self.resos[1][loc]
			
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
		
	def set_pixel_range(self,object_id):  #returns mapping for each lightup object in the form of [start_pixel,length,fadecandy board]
		#object ids: 0-7 are the links going clockwise from rear left link
		if object_id == 0: #chan 0 & 1 for long link 1, North link?, back left corner of tent
			self.link_len = 92
			self.start_channel = 0
			self.fadecandy = 0
		elif object_id == 1: # 2 & 3 for long link 2, back right corner
			self.link_len = 92
			self.start_channel = 2
			self.fadecandy = 0
		elif object_id == 2: #short links, single channel
			self.link_len = 64
			self.start_channel = 4
			self.fadecandy = 0
		elif object_id == 3:
			self.link_len = 64
			self.start_channel = 0
			self.fadecandy = 1
		elif loc == 4: # 1 & 2 for long link reso 5, front right corner
			self.link_len = 92
			self.start_channel = 1
			self.fadecandy = 1
		elif loc == 5:   #3 & 4 for long link reso 6, front left corner
			self.link_len = 92
			self.start_channel = 3
			self.fadecandy = 1
		elif loc == 6: # chan 5 for forward left short link
			self.link_len = 64
			self.start_channel = 5
			self.fadecandy = 1
		elif loc == 7:
			self.link_len = 64
			self.start_channel = 5
			self.fadecandy = 0
			
	def put_px_range(self, _start, _length, _color, _fc, _delay = 0):   #set all pixels in range a color
		for i in range(_start, length):
			if _fc == 0:
				pixels[i] = _color
				if _delay > 0:
					self.client.put_pixels(pixels)
			elif _fc == 1:
				pixels2[i] = _color
				if _delay > 0:
					self.client2.put_pixels(pixels2)
			self.time.wait(_delay)
		if _fc == 0:
			self.client.put_pixels(pixels)
			self.client.put_pixels(pixels)
		elif _fc == 1:
			self.client2.put_pixels(pixels2)
			self.client2.put_pixels(pixels2)
	def set_brightness(self, bright): #set 0-100 brightness
		self._brt = float(bright)/100
		opc.setColorCorection(2.5,_self.brt,_self.brt,_self.brt)
				
