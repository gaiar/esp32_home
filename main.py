#!/usr/bin/env python
from umqtt.robust import MQTTClient
import time
import machine
import dht

import bme680
from bme680.i2c import I2CAdapter
import gc

RESETPIN = 0
SCLPIN = 22
SDAPIN=21


LEDPIN = 16
DHTPIN = 22
SOILPIN = 32
LIGHTPIN = 34


#Setup BME680

i2c_dev = I2CAdapter(scl=machine.Pin(SCLPIN), sda=machine.Pin(SDAPIN))
sensor = bme680.BME680(i2c_device=i2c_dev, i2c_addr=bme680.I2C_ADDR_SECONDARY)

# These oversampling settings can be tweaked to 
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# start_time and curr_time ensure that the 
# burn_in_time (in seconds) is kept track of.


burn_in_time = 300


def sensor_burnin(burn_in_time = burn_in_time):
    # Collect gas resistance burn-in values, then use the average
    # of the last 50 values to set the upper limit for calculating
    # gas_baseline.
    print("Collecting gas resistance burn-in data for {0} mins\n".format(burn_in_time/60))
    start_time = time.time()
    curr_time = time.time()
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            with open('burn_in_data.txt', 'ab') as burn_in_data:
                burn_in_data.write("{}\n".format(str(gas)))
            print("Gas: {0} Ohms".format(gas))
            time.sleep(1)
            gc.collect()
            print ("Memory available {0} bytes".format(gc.mem_free()))
    del start_time, curr_time

def calculate_gas_baseline():
    #TODO: Add file existanse check   
    with open('burn_in_data.txt', 'r') as burn_in_data:
        print ("Reading gas data file")
        gas_baseline = 0.0
        for item in burn_in_data.readlines()[-50:]:
            gas_baseline+=float(item)
            print ("Memory available {0} bytes".format(gc.mem_free()))
        gc.collect()
        gas_baseline = gas_baseline / 50.0
    print ("Memory available {0} bytes after gas resistance calculation".format(gc.mem_free()))
    return gas_baseline

gas_baseline = calculate_gas_baseline()

# Set the humidity baseline to 40%, an optimal indoor humidity.
hum_baseline = 40.0

# This sets the balance between humidity and gas reading in the 
# calculation of air_quality_score (25:75, humidity:gas)
hum_weighting = 0.25

print("Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n".format(gas_baseline, hum_baseline))






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
mqtt_topic = "bme680"


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
