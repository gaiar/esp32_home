from time import sleep
import network
import gc
from ntptime import settime


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('HomeTech_1', 'r0k0r0kmxbr')
        while not sta_if.isconnected():	
            print(".", end="")
			time.sleep(1)
    print('network config:', sta_if.ifconfig())
 
do_connect()
settime()
gc.collect()

