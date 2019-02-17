#!/usr/bin/env python
from mqtt import MQTTClient
import time
import machine
import utime
import dht


# timeout for mqtt
def settimeout(duration):
    pass


# Function for taking average of 100 analog readings
def smooth_reading():
    avg = 0
    _AVG_NUM = 100
    for _ in range(_AVG_NUM):
        avg += apin()
    avg /= _AVG_NUM
    return(avg)


# MQTT setup
client = MQTTClient("wipy", "192.168.1.148", port=1883)
client.settimeout = settimeout
client.connect()
mqtt_topic = "dht11"


# DHT11
sensor=dht.DHT11(machine.Pin(22))
# Moisture sensor
adc = machine.ADC()
apin = adc.channel(pin='P16', attn=3)

print("Polling:")
try:
    while True:
        if sensor.measure():
            #d.measure()
            #d.temperature()
            #>>> d.humidity()
            output = "{} C, {} RH".format(
                sensor.temperature(),
                sensor.humidity()
                )
            print(output)
            client.publish(mqtt_topic, output)
            # Publish on individual topics for consistency with rpi repo.
            client.publish('dht11-humidity', str(sensor.humidity()))
            client.publish('dht11-temperature', str(sensor.temperature()))
           
            # Read the analogue water sensor
            _THRESHOLD = 3000
            analog_val = smooth_reading()
            print(analog_val)
            if analog_val < _THRESHOLD:
                print("Water_detected!")
                client.publish('bme680-water', "ON")
            else:
                client.publish('bme680-water', "OFF")
            time.sleep(2)

except KeyboardInterrupt:
    pass
