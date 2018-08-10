#!/usr/bin/env python
#
# Simple example color correction UI.
# Talks to an fcserver running on localhost.
#
# Micah Elizabeth Scott
# This example code is released into the public domain.
#

import Tkinter as tk
import socket
import json
import struct

s = socket.socket()
s.connect(('localhost', 7890))
print "Connected to OPC server"

def setGlobalColorCorrection(**obj):
    msg = json.dumps(obj)
    s.send(struct.pack(">BBHHH", 0, 0xFF, len(msg) + 4, 0x0001, 0x0001) + msg)

def update(_):
    setGlobalColorCorrection(
        gamma = gamma.get(),
        whitepoint = [
            red.get(),
            green.get(),
            blue.get(),
        ])

def slider(name, from_, to, setpoint):
    s = tk.Scale(root, label=name, from_=from_, to=to, resolution=0.01,
        showvalue='yes', orient='horizontal', length=400, command=update)
    s.set(setpoint)
    s.pack()
    return s

config = json.load(open('./fcserver/temple_new.json'))

root = tk.Tk()
root.title("Fadecandy Color Correction Example")

gamma = slider("Gamma", 0.2, 3.0, config["color"]["gamma"])
red = slider("Red", 0.0, 1.5, config["color"]["whitepoint"][0])
green = slider("Green", 0.0, 1.5, config["color"]["whitepoint"][1])
blue = slider("Blue", 0.0, 1.5, config["color"]["whitepoint"][2])

root.mainloop()
