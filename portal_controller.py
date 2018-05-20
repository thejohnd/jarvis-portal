import portal
global main_menu_functions
global macro_menu_functions
global levels

p = portal.Portal(start_serial=False)

def resoDeployer():
    reso = 0
    level = 0
    print("Enter selection, or -1 to return to main menu")
    while reso not in levels:
        reso = input("Deploy to which resonator slot? ")
        if reso == '-1' : break
        if not (1 <= reso <= 8):
            print("Invalid selection")
            reso = 0
    while level not in levels:
        level = input("Enter resonator level to deploy: ")
        if level == '-1' : break
        if not (1 <= level <= 8):
            print("Invalid level")
            level = 0
 
    p.deploy_reso(reso, level, 'enl')
    o = ("Level {} reso deployed to slot {}").format(level, reso)
    print(o)

def resoDestroyer():
    print("Enter selection, or leave -1 to return to main menu")
    loc = 0
    while (loc <= 0):
        loc = input("Destroy which resonator? ")
        if loc == '-1' : break
        if not (1 <= loc <= 8):
            print("Invalid selection")
            loc = -1
    if loc == '-1' : pass
    else:
        p.destroy_reso(loc)

def macroCaller():
    global macro_menu_functions
    print("""
		==============
		Macro Menu
		==============
		1 - Deploy all L8E
		2 - Reso Rainbow! (Level by location)
		3 - Destroy all resos
		4 - Return to Main Menu
		""")
    m = 0
    while m not in macro_menu_functions:
        m = input("Enter Selection: ")
    macro_menu_functions[m].__call__()
        
        
def allL8E():
    for i in range(8):
        p.deploy_reso(i,8,'enl')
        
def resoRainbow():
    for i in range(8):
        p.deploy_reso(i,i+1,'enl')
        
def destroyAll():
    for i in range(8):
        p.destroy_reso(i)
        
def printResos():
    reso_msg = """
      ::Resonator Status::
    =========================
    Reso 1: {0}  |  Reso 2: {1}
    Reso 3: {2}  |  Reso 4: {3}
    Reso 5: {4}  |  Reso 6: {5}
    Reso 7: {6}  |  Reso 8: {7}
    """
    reso_array = p.get_resos()[0]
    print(reso_msg.format(reso_array[0],
					reso_array[1],
					reso_array[2],
                    reso_array[3],
                    reso_array[4],
                    reso_array[5], 
                    reso_array[6],
                    reso_array[7]
                    )
         )

def portalShutdown():
    p.stop_fx()
    p.put_px_range(0, 1023, p.blk, 0)
    exit()

def null():
	pass

def main():
    global main_menu_functions
    global macro_menu_functions
    global levels
    
    main_menu_functions = {
        1 : resoDeployer,
        2 : resoDestroyer,
        3 : macroCaller,
        4 : printResos,
        5 : portalShutdown
        }

    macro_menu_functions = {
        1 : allL8E,
        2 : resoRainbow,
        3 : destroyAll,
        9 : p.epic_jarvis,
        4 : null
        }
    levels = [ 1,2,3,4,5,6,7,8 ]
    while True:
        MMchoice = 0
        print("""
        ____________________________
        ||   Portal Control Menu  ||
        ============================
        1 - Deploy Reso
        2 - Destroy Reso
        3 - Macro Menu (Patterns)
        4 - Reso Status
        5 - Shutdown Portal
        """)
        while MMchoice not in main_menu_functions:
            MMchoice = input("Enter your selection: ")
            print(MMchoice)
        main_menu_functions[MMchoice].__call__()

if __name__ == "__main__":
    main()
