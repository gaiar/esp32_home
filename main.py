#!/usr/bin/env python
from umqtt.robust import MQTTClient
import time
import machine
import dht

RESETPIN = 0
LEDPIN = 16
DHTPIN = 22
SOILPIN = 32
LIGHTPIN = 34


# timeout for mqtt
def settimeout(duration):
    pass


# Function for taking average of 100 analog readings
def smooth_reading():
    avg = 0
    _AVG_NUM = 100
    for _ in range(_AVG_NUM):
        avg += soil_sensor.read()
    avg /= _AVG_NUM
    return(avg)


# MQTT setup
client = MQTTClient("higrow", "192.168.1.148", port=1883, user="mqttuser", password="mqttpassword")
client.settimeout = settimeout
client.connect()
mqtt_topic = "dht11"


# DHT11
sensor = dht.DHT11(machine.Pin(DHTPIN))

# Moisture sensor
def soil_moisture_sensor(PIN):
    from machine import ADC, Pin
    adc = ADC(Pin(32)) 
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)
    return adc

soil_sensor = soil_moisture_sensor(SOILPIN)

print("Polling:")
try:
    while True:
        sensor.measure()
        # d.measure()
        # d.temperature()
        # d.humidity()
        output = "{} C, {} RH".format(
            sensor.temperature(),
            sensor.humidity()
        )
        print(output)
        client.publish(mqtt_topic, output)

        # Publish on individual topics for consistency
        client.publish('home/higrow/humidity', str(sensor.humidity()))
        client.publish('home/higrow/temperature', str(sensor.temperature()))

        # Read the analogue soil moisture sensor
        # _THRESHOLD = 3000
        soil_moisture = smooth_reading()
        client.publish('home/higrow/soil-moisture', str(soil_moisture))
        print(soil_moisture)

        # if analog_val < _THRESHOLD:
        #     print("Water_detected!")
        #     client.publish('bme680-water', "ON")
        # else:
        #     client.publish('bme680-water', "OFF")
        time.sleep(3)

except Exception as e:
    print("Exception happened:", e)
