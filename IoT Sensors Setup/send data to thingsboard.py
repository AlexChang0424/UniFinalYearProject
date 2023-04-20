import RPi.GPIO as GPIO
import time
import os
import Adafruit_DHT
import glob
import time
import Adafruit_ADS1x15
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import paho.mqtt.client as mqtt
import json

THINGSBOARD_HOST = 'thingsboard.cloud'
ACCESS_TOKEN = 'Oi4mExCcvgLAjrQOQnNL'

# Data capture and upload interval in seconds. Less interval will eventually hang the sensors.
INTERVAL=6

# Set up the DHT11 sensor
DHT11_SENSOR_PIN = 26

# Create an I2C object
i2c = busio.I2C(board.SCL, board.SDA)

# Create an ADS1115 ADC object
ads = ADS.ADS1115(i2c, address=0x48)

# Create AnalogIn objects for the input pins on the ADS1115 that are connected to the water level and TDS sensors
tds_channel = AnalogIn(ads, ADS.P0)         # channnel 0
#water_level_channel = AnalogIn(ads, ADS.P1) # channel 1
ph_sensor_channel = AnalogIn(ads, ADS.P2)    # channel 2

# Coversion factor
#water_level_cf = 1
tds_cf = 2000
# Reference voltage (in volts)
vref = 3.3

def read_tds_sensor():
    # Read the analog voltage from the TDS sensor
    tds_voltage = tds_channel.voltage
    # Calculate TDS Value using vref and cf base on tds voltage 
    tds_concentration = tds_voltage / vref * tds_cf # range 0 - 1000ppm
    return tds_concentration

#def read_waterlvl_sensor():
    # Determine Water level 
    #if (water_level_channel.voltage <= 0):
        #return "Bellow Level" # Not submerged
    #elif (water_level_channel.voltage > 0):
        #return "On Level"     # Partially submerged

def read_ph_sensor():
    # Read the voltage on the analog input channel
    pH_voltage = ph_sensor_channel.voltage
    # Convert the voltage to a pH value using the manufacturer's conversion formula
    pH_Value = (pH_voltage * 3.5) - 3.0
    # pH_Value = ((pH_voltage / 3.3) * 14) / 2
    return pH_Value
    
# Set up the DS18B20 sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

sensor_data = {'Air Temperature': 0, 'Air Humidity': 0, 'TDS concentration': 0, 'pH Value': 0, 'Water Temperature': 0}

next_reading = time.time() 

client = mqtt.Client()

# Set access token
client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

# Read and display data from sensors
try:
    while True:
       
        # Data from DHT11 Sensor
        humidity, temperature = Adafruit_DHT.read_retry(11, DHT11_SENSOR_PIN)
        print("Air Temperature:", temperature, "℃")
        print("Air Humidity:", humidity, "%")
        sensor_data['Air Temperature'] = temperature
        sensor_data['Air Humidity'] = humidity
        
        # Data from TDS Sensor
        tds_concentration = read_tds_sensor()
        tds_concentration = round(tds_concentration, 1)
        print('TDS concentration:', tds_concentration, 'ppm')
        sensor_data['TDS concentration'] = tds_concentration
        
        # Data from Water Level Sensor
        #WaterLevel = read_waterlvl_sensor()
        #print("Water Level:",WaterLevel)
        #sensor_data['Water Level'] = WaterLevel
        
        # Data from PH Sensor
        pH_Value = read_ph_sensor()
        pH_Value = round(pH_Value, 1)
        print('ph Value:', pH_Value)
        sensor_data['ph Value'] = pH_Value
        
        # Data from DS18B20 Sensor
        temp_c, temp_f = read_temp()
        temp_c = round(temp_c, 1)
        print('Water Temperature:', temp_c)
        sensor_data['Water Temperature'] = temp_c
        
        # Sending humidity and temperature data to ThingsBoard
        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)       
except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()
  

