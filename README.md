# jarvis-portal
Tecthulu project for SEA-ENL #MagnusReawakens. Requires pygame, opc (included in folder), and Fadecandy fcserver. Should still run without fcserver running, but will print warning messages.

----------------------------------------------------------------


Portal Module
##############################

PORTAL
------------------
portal.Portal(faction = 'neutral', level = 1, start_fc-client = True, start_serial = True):

- Creates the portal and initializes portal data and settings, Pygame sound effects module, and interfaces to external hardware.
	- Portal is initialized by default to unclaimed (neural, L1, no resos). Faction & level can be set on initialization if needed.
	- For convenience initializing the portal will also start client connection to the Fadecandy, and the serial connection to the Arduino, using default settings. However, set these to false to manually start them.


portal.init_fcclient(ADDRESS_1 = 'localhost:7890', ADDRESS_2='localhost:7981')

- Manually start Fadecandy client connection. Adresses/ports for Fadecandy boards 1 & 2 can be changed. If only one board is connected, set ADDRESS_2=''


portl.init_serial(port = '/dev/ttyUSB0')
- Start serial connection to Arduino board. Use make sure the port is correctly set to the connected Arduino.

FACTION
------------------
portal.set_faction(faction)
- Set faction to 'neu', 'enl', or 'res'. Triggers faction-specific  lighting and sound. Returns portal.faction if successful, returns 0 if invalid argument or argument matches current faction. Faction should be set using set_faction, instead of setting portal.faction directly, because set_faction also sets the correct factiosn sounds and lighting.

portal.get_faction()
- Returns current faction. Also can be accessed via portal.faction

portal.flip()
- Flips portal to opposite faction and [TODO] triggers flip animation. Returns new portal.faction if successful, returns 0 if portal is neutral.

RESOS & PORTAL LEVEL
---------------------
Resos are stored as the 2d array: portal.resos[reso_level[8],reso_health[8]]
- Array position corresponds to reso slot, starting with resos[0] as the North slot (red dot in scanner), proceeding clockwise to resos[7]. reso_level of 0 means undeployed. reso_health is health percentage of 1 - 100. portal.resos can be accessed to see current status of resos, but setting portal.resos directly will not trigger FX. Unless you are trying to avoid triggering FX, resos should be set via deploy_reso, set_reso_health, and destroy_reso.

get_level()
- recalculates the overall portal level from deployed resos, and returns level as int. Sets portal.level as current level based on resos. Changing portal.resos directly will not immediately update level, you must call get_level() to do this.

deploy_reso(reso_slot,reso_level)
- adds a reso at full health & triggers deploy FX. Raises warnings on invalid reso level.

destroy_reso(reso_slot)
- Sets reso in reso slot to 0 level and 0 health. Plays destroy FX.

set_reso_health(reso_slot, health)
- Sets health of reso in reso_slot. If health set to <= 0, calls destroy_reso. Returns level and health for reso_slot.

get_resos()
- Returns portal.resos


MUSIC & SOUND FX
---------------------

play.music(vol = 1.0)
- Plays faction-specific background sound loop. Set volume from 0.0 to 1.0.

get_music_volume()
- Return current music volume

set_music_volume(volume)
- Sets music volume. Valid values are 0.0 to 1.0

play_fx()
- Starts playing faction-specific sound effects

stop_fx(fade = True)
- Stops music and sound fx playback. If fade=false, playback stops immediately, otherwise fades out over (portal.fadeTime) ms

set_fx_volume(fx_volume)
- Sets sound fx volume, valid values 0.0 to 1.0. Returns fx_volume.





