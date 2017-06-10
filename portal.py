import pygame
import random
import threading
import numpy as np
import opc
import time
import serial

class Portal(object):
    def __init__(self, faction = 'neu', level = 1, start_fcclient = True, start_serial = False):
        #
        #---PYGAME SOUNDS---------
        #
        self._buf = 307200
        pygame.mixer.quit()
        #init pygame mixer if needed--------------
        if pygame.mixer.get_init() == None:
            pygame.mixer.pre_init(44100, -16, 2, self._buf)
            pygame.mixer.init()
        #audio params, time in ms
        self.fadeTime = 4000
        self.fxInterval = [3,9]
        self.fx_vol = 1.0
        
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
        
        #Extras soundbank
        self.space1 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_female_alt.ogg')
        self.space2 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_lattitude.ogg')
        self.space3 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_grid142.ogg')
        self.space4 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_magnification.ogg')
        self.space5 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_transmission3.ogg')
        self.space6 =  pygame.mixer.Sound('./sounds/sfx_ambient_space_transmission3.ogg')
        self.flipswirl = pygame.mixer.Sound('./sounds/sfx_flipcard_swirl.ogg')
        self.hackparticles = pygame.mixer.Sound('./sounds/sfx_hack_particles.ogg')
        self.hackpop = pygame.mixer.Sound('./sounds/sfx_hack_popout.ogg')
        self.xm = pygame.mixer.Sound('./sounds/sfx_xm_pickup.ogg')
        
        #banks
        self.xtras = [self.space1, self.space2, self.space3, self.space4, self.space5, self.space6, self.flipswirl, self.hackparticles, self.hackpop, self.xm]
        self.enl = [self.wraith, self.wraith2, self.static, self.heartbeat, self.beeps, self.ring, self.swell, self.wind]+self.xtras
        self.res = [self.energy, self.pulse_stereo, self.pulse_warm, self.crystal, self.beeps, self.ring, self.swell, self.wind]+self.xtras
        self.neu = [self.n_crystal, self.impacts, self.whale, self.whale_alt, self.beeps, self.ring, self.swell, self.wind]+self.xtras
        #speech = pygame.mixer.Channel(7)
        
        #triggered on action sounds
        self.reso_deploy = pygame.mixer.Sound('./sounds/sfx_resonator_power_up.ogg')
        self.ada_portal = pygame.mixer.Sound('./sounds/speech_portal_en.ogg')
        self.ada_online = pygame.mixer.Sound('./sounds/speech_online_en.ogg')
        self.ada_goodwork = pygame.mixer.Sound('./sounds/speech_good_work_en.ogg')
        self.destroyed = pygame.mixer.Sound('./sounds/sfx_explode_resonator.ogg')
        self.crit = pygame.mixer.Sound('./sounds/sfx_resonator_critical_hit.ogg')
        self.portal_dead = pygame.mixer.Sound('./sounds/sfx_neutralize_portal.ogg')
        
        #praisejarvis
        self.jarvis1 = pygame.mixer.Sound('./sounds/jarvisredemptionspeech-part1of2.ogg')
        #self.jarvis2 = pygame.mixer.Sound('./jarvisredemptionspeech-part2of2.mp3')
        
        #-----Start HW Interfaces
        if start_fcclient:
            self.init_fcclient() #init only FC board 1 until we have both set up
        if start_serial:
            self.init_serial() #Set USB serial port here if necessary
            self.srl.write('n5')
        else:
            self.init_serial(port = None) #init serial with no port so things don't break
            print "Serial port not started"
        
        #--setup lighting color vars etc
        #
        #colors is rgb for L1-L8
        self.colors = [(254, 206, 0),(255, 168, 48),(255, 115, 21),(228, 0, 0),(253, 41, 146),(235, 38, 205),(193, 36, 224),(150, 39, 244)]
        self.blk = (0,0,0)
        
        
        self.link_len = 64   #num of LEDs in link, fadecandy max 64 per channel
        self.start_channel = 0
        self.pixels = [self.blk]*1024
        self.ledoff = [self.blk]*1024
        #self.pixels2 = [self.blk]*512   #TODO: list of lists to hold all pixels for all resos?
        self.client.put_pixels(self.pixels) #TODO: channel=all
        self.client.put_pixels(self.pixels)
                
        #-----OTHER PORTAL PROPERTIES & VARS
        #   
        #set starting portal properties
        self.faction = faction
        self._faclist = ['neu','enl','res']
        self.level = level
        self._fxplay = False
        self.resos = [[0,0,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0]]
        self._lvl = np.sum(self.resos[0],dtype='float16')/8
    
    #-----LIGHTS-------
    #
    #---------define Fadecandy OPC Client--------------
    def init_fcclient(self, ADDRESS_1 = 'localhost:7890', ADDRESS_2 = ''):
        
        # Create a client object
        self.client = opc.Client(ADDRESS_1)
        
        # Test if it can connect
        if self.client.can_connect():
            print 'connected to %s' % ADDRESS_1
        else:
            # We could exit here, but instead let's just print a warning
            # and then keep trying to send pixels in case the server
            # appears later
            print 'WARNING: could not connect to %s... Is fcserver running?\nClient will retry connection each time a pixel update is sent' % ADDRESS_1
        self.clients = [self.client]
    
    def init_serial(self, port = '/dev/ttyACM0'):
        #----serial interface to Arduino for DMX & Relay switch
        ## MAKE SURE TO SET USB PORT FOR CURRENT SYTEM CONFIG!!! 
        self.srl = serial.Serial(port,9600)
        print 'Using serial port %s' % self.srl.name    
    
    #get/set FACTION
    def get_faction(self):
        return self.faction
    
    def set_faction(self, faction):
        if faction != self.faction and (faction in self._faclist):
            if pygame.mixer.music.get_busy():
                pygame.mixer.fadeout(self.fadeTime)
                self.faction = faction
                self.play_music()
            else:
                self.faction = faction
            if self.srl.name:
                self.srl.write(self._fac(self.faction))
                if self.faction == 'neu':
                    self.srl.write('5')
                else:
                    self.srl.write('9')
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
        
    #DEPLOY ALL THE THINGS    
    def deploy_reso(self, loc, rank, faction=''):
        if rank < 1 or rank > 8:
            raise Warning('Invalid Resonator Level - Not Deployed')
        elif rank <= self.resos[0][loc]:
            raise Warning('Deploy Failed - Not an Upgrade')
        else:
            #reso deploy code here
            o = ''
            self.resos[0][loc] = rank
            self.resos[1][loc] = 100
            self.set_pixel_range(loc)
            self.reso_deploy.play()
            if self.client.put_pixels(self.pixels):
                self.set_pixel_range(loc)   #set range for link       
                self.put_px_range(self.start_channel, self.link_len, self.colors[rank-1], self.fadecandy, 0.02)  #show link animation
                self.set_pixel_range(loc+10)  #set range for associated reso     
                #self.put_px_range(self.start_channel, self.link_len, self.colors[rank-1], self.fadecandy)  #show reso color
                #self.client.put_pixels(self.pixels)
                if self._lvl==0:
                    self.adavoice = self.ada_portal.play()
                    self.adavoice.queue(self.ada_online)
                    if faction and self.get_faction() == 'neu':
                        self.set_faction(faction)
                o = 'sent'
            else:
                o = 'Fadecandy1 not connected'
            #reso lights hotfix shitcode
            if loc == 0:
                self.put_px_range(7*64,64,self.colors[rank-1],0,0.02)
            self.get_level()
            return o
            if self.get_level() == 8:
                self.epic_jarvis()
            
    
    #GET RESOS
    def get_resos(self):
        return self.resos
    
    #DESTROY RESO
    def destroy_reso(self, loc):
        self.resos[0][loc] = 0
        self.resos[1][loc] = 0
        self.b = 255
        self.resobust = self.crit.play()
        time.sleep(self.crit.get_length())
        self.resobust.queue(self.destroyed)
        while self.b >= 20:
            self.set_pixel_range(loc)
            self.put_px_range(self.start_channel, self.link_len, (self.b,self.b,self.b), self.fadecandy)
            self.put_px_range(1023, 1, self.blk, self.fadecandy,0.1) #non-blocking delay hack
            self.put_px_range(self.start_channel, self.link_len, self.blk, self.fadecandy, 0.005)
            self.b = self.b/2
        self.get_level()
        if self._lvl == 0:
            self.portal_dead.play()
            self.set_faction('neu')
            
    def set_reso_health(self, loc, health):
        if health < 100:
            print 'Invalid Health Value %h for Reso %l : Health not set' % health,loc
        elif health <= 0:
            self.destroy_reso(loc)
            print 'Reso %l destroyed' % loc+1
        else:
            self.resos[1][loc] = health
            #TODO set link brightness based on health
            return  'Reso %r=%l,%h' % loc,self.resos[0][loc],self.resos[1][loc]
            
    #PLAY BACKGROUND loop for current faction
    def play_music(self, vol = 1.0):
        self._vol = vol
        if self.faction == 'enl':
            self.music = './sounds/sfx_ambient_alien_base.ogg'
            self._vol = 0.7
        elif self.faction == 'res':
            self.music = './sounds/sfx_ambient_human_base.ogg'
        else:
            self.music = './sounds/sfx_ambient_neutral_base.ogg'
        
        pygame.mixer.music.load(self.music)
        pygame.mixer.music.set_volume(self._vol)
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
            if self.faction == 'enl':
                self.fac = self.enl
            elif self.faction == 'res':
                self.fac = self.res
            else:
                self.fac = self.neu
            self.snd = random.choice(self.fac)
            #self.snd.set_volume(self.fx_vol)
            self.faded_len = int((self.snd.get_length()*1000)-35)
            self.snd.play(0,0,self.faded_len)
            time.sleep(self.snd.get_length())
            time.sleep(random.randrange(self.fxInterval[0],self.fxInterval[1]))
            
    def set_fx_volume(self, fxv):
        self.fx_vol = fxv
        return self.fx_vol
        
    def set_pixel_range(self,object_id):  #returns mapping for each lightup object in the form of [start_pixel,length,fadecandy board]
        #object ids: 0-7 are the links going clockwise from rear left link
        if object_id == 0: #chan 0 & 1 for long link 1, North link?, back left corner of tent
            self.link_len = 128
            self.start_channel = 0
            self.fadecandy = 0
        elif object_id == 1: # 2 & 3 for long link 2, back right corner
            self.link_len = 128
            self.start_channel = 2*64
            self.fadecandy = 0
        elif object_id == 2: #short links, single channel
            self.link_len = 64
            self.start_channel = 4*64
            self.fadecandy = 0
        elif object_id == 3:
            self.link_len = 64
            self.start_channel = 512
            self.fadecandy = 1
        elif object_id == 4: # 1 & 2 for long link reso 5, front right corner
            self.link_len = 92
            self.start_channel = 512+(1*64)
            self.fadecandy = 1
        elif object_id == 5:   #3 & 4 for long link reso 6, front left corner
            self.link_len = 92
            self.start_channel = 512+(3*64)
            self.fadecandy = 1
        elif object_id == 6: # chan 5 for forward left short link
            self.link_len = 64
            self.start_channel = 512+(5*64)
            self.fadecandy = 1
        elif object_id == 7:
            self.link_len = 64
            self.start_channel = 5*64
            self.fadecandy = 0
        elif object_id == 10:
            self.link_len = 24
            self.start_channel = 93
            self.fadecandy = 0
        elif object_id == 11:
            self.link_len = 24
            self.start_channel = (2*64)+93
            self.fadecandy = 0
        elif object_id == 12: #both mid short reso on chan6 FC1
            self.link_len = 8
            self.start_channel = 6*64
            self.fadecandy = 0
        elif object_id == 13: #both mid short reso on chan6 FC1
            self.link_len = 8
            self.start_channel = (6*64)+9
            self.fadecandy = 0
        elif object_id == 14: #front long reso on FC2 long link
            self.link_len = 8
            self.start_channel = (2*64)+93+512
            self.fadecandy = 1
        elif object_id == 15: #front long reso on FC2 long link
            self.link_len = 8
            self.start_channel = (4*64)+93+512
            self.fadecandy = 1
        elif object_id == 16:
            self.link_len = 8
            self.start_channel = 7*64
            self.fadecandy = 0
        elif object_id == 16:
            self.link_len = 8
            self.start_channel = (7*64)+9
            self.fadecandy = 0
        
                    
    def put_px_range(self, _start, _length, _color, _fc = 0, _delay = 0):   #set all pixels in range a color
        self.lightloop = threading.Thread(target=self.px_loop, args=(_start, _length, _color, _fc, _delay))
        self.lightloop.start()
        
    def px_loop(self, _start, _length, _color, _fc, _delay):   #set all pixels in range a color
        for i in range(_start, _start+_length):
            self.pixels[i] = _color
            if _delay > 0:
                self.client.put_pixels(self.pixels)
            #if _fc == 0:
            #    self.pixels[i] = _color
            #    if _delay > 0:
            #        self.client.put_pixels(self.pixels)
            #elif _fc == 1:
            #    self.pixels2[i] = _color
            #    if _delay > 0:
            #        self.client.put_pixels(self.pixels2)
            time.sleep(_delay)
        #if _fc == 0:
        #    self.client.put_pixels(self.pixels)
        #    self.client.put_pixels(self.pixels)
        #elif _fc == 1:
        #    self.client2.put_pixels(self.pixels2)
        #    self.client2.put_pixels(self.pixels2)
        self.client.put_pixels(self.pixels)
        self.client.put_pixels(self.pixels)
        
    
    #def set_brightness(self, resos=99): #set 0-100 brightness
    #    if resos == 99:
    #        for r in self.resos[1]:
    #            
    #            
    #    self.resos
    ### flash loop (not done)
    def flashing(self,ms=10,fshon=True):
        self._flshon = fshon
        self.fl = threading.Thread(target=self.flashloop, args=(ms))
        self.fl.start()
        
    def flashloop(self, ms):
        while self._flshon:    
            self.client.put_pixels(self.pixels)
            pygame.time.wait(ms/2.0)
            self.client.put_pixels(self.ledoff)
            pygame.time.wait(ms/2.0)
            self.client.put_pixels(self.pixels)
        self.fl.join(500)
        
    def epic_jarvis(self):
        self.jarvis1.play()
        pygame.mixer.music.fadeout(10000)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.load('./sounds/thorinair.mp3')
        pygame.mixer.music.play()
        time.sleep(19)
        self.srl.write('e9')
        for m in range(3):
            for i in range(64):
                self._rpxinrange = 1023
                for l in range(8):
                    #self.pixels[self._rpxinrange] = (0,130,30)
                    self.set_pixel_range(l)
                    self._rpxinrange = random.randrange(l+1) + self.start_channel
                    for j in [0,l*2]:
                            self.pixels[self._rpxinrange+j] = (255,255,255)
                            self.client.put_pixels(self.pixels)
                            self.link_len = i+1
                    if l >= random.randrange(l+1):
                        self.srl.write('e3')
                    self.put_px_range(self.start_channel, self.link_len, (58+l,255-(l*25),78-i),0)
                    self.set_pixel_range(11)
                    self.put_px_range(self.start_channel, self.link_len, (0,255-(l*18),32),0)
                    self.put_px_range(self.start_channel+(l*3), 3, (255,255,255),0)
                    #self._rpxinrange = random.randrange(self.link_len) + self.start_channel
                    #or j in [0,2,4]:
                    #    if self.pixels[self._rpxinrange+j] == (0,130,30):
                    #        self.pixels[self._rpxinrange+j] = (255,255,200)
                    time.sleep(0.1)
                    self.client.put_pixels(self.pixels)
                    self.srl.write('e9')
            for xl in range(24):
                for x in [1,3,7,9]:
                    self.put_px_range(x*64, xl, (58,255-(x*10),12),0,0.03)
                    self.set_pixel_range(10)
                    self._rpxinrange = random.randrange(self.link_len) + self.start_channel
                    if self.pixels[self._rpxinrange] == (0,130,30):
                        self.pixels[self._rpxinrange] = (255,255-(x*10),200)
                    time.sleep(0.02)
                    self.client.put_pixels(self.pixels)    
            #####nooooooo
            for i in range(64):
                self._rpxinrange = 1023
                for l in range(8):
                    #self.pixels[self._rpxinrange] = (0,130,30)
                    self.set_pixel_range(l)
                    self._rpxinrange = random.randrange(i+1) + self.start_channel
                    for j in [0,l*2]:
                            self.pixels[self._rpxinrange+j] = (255,255,255)
                            self.client.put_pixels(self.pixels)
                    self.link_len = i+1
                    self.put_px_range(self.start_channel, self.link_len, self.colors[l],78+i,0)
                    self.set_pixel_range(11)
                    self.put_px_range(self.start_channel, self.link_len, (0,255-(l*18),32),0)
                    self.put_px_range(self.start_channel+(l*3), 3, (255,255,255),0)
                    #self._rpxinrange = random.randrange(self.link_len) + self.start_channel
                    #or j in [0,2,4]:
                    #    if self.pixels[self._rpxinrange+j] == (0,130,30):
                    #        self.pixels[self._rpxinrange+j] = (255,255,200)
                    time.sleep(0.1)
                    self.client.put_pixels(self.pixels)
            for xl in range(24):
                for x in [1,3,7,9]:
                    self.put_px_range(x*64, xl, (58,255-(x*10),12),0,0.03)
                    self.set_pixel_range(10)
                    self._rpxinrange = random.randrange(self.link_len) + self.start_channel
                    if self.pixels[self._rpxinrange] == (0,130,30):
                        self.pixels[self._rpxinrange] = (255,255-(x*10),200)
                    time.sleep(0.02)
                    self.client.put_pixels(self.pixels)         
                    
                
        self.client.put_pixels(self.pixels)
        
        while pygame.mixer.music.get_busy():
            pygame.time.wait(500)
        self.client.put_pixels(self.pixels)
        self.play_music()
        self.pixels=[self.colors[7]]*1024
        self.client.put_pixels(self.pixels)
        self.client.put_pixels(self.pixels)
