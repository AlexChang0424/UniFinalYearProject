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
    #elif (water_level_channel.voltage > 0.1 and water_level_channel.voltage <= 2.0):
        #return "On Level"     # Partially submerged
    #elif (water_level_channel.voltage > 2.0):
        #return "Above Level"  # Fully submerged

def read_ph_sensor():
    # Read the voltage on the analog input channel
    pH_voltage = ph_sensor_channel.voltage
    # Convert the voltage to a pH value using the manufacturer's conversion formula
    pH_Value = (pH_voltage * 3.5) - 3.0
    #pH_Value = ((pH_voltage / 3.3) * 14) / 2
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

# Read and display data from sensors
while True:
   
    # Data from DHT11 Sensor
    humidity, temperature = Adafruit_DHT.read_retry(11, DHT11_SENSOR_PIN)
    print("Air Temperature:", temperature, "℃")
    print("Air Humidity:", humidity, "%")
    
    # Data from TDS Sensor
    tds_concentration = read_tds_sensor()
    print('TDS concentration: {:.1f} ppm'.format(tds_concentration))
    
    # Data from Water Level Sensor
    #WaterLevel = read_waterlvl_sensor()
    #print("Water Level:",WaterLevel)
    
    # Data from PH Sensor
    pH_Value = read_ph_sensor()
    print("ph Value: {:.1f}".format(pH_Value))
    
    # Data from DS18B20 Sensor
    temp_c, temp_f = read_temp()
    print("Water Temperature: {:.1f} ℃".format(temp_c))
    #print("Temperature:", temp_f, "F")
    
    time.sleep(1)
  
