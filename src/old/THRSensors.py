#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* THRSensors Class

* version: 20180413a
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

import sys, math, json, os.path, time
from Adafruit_BME280 import *
import RPi.GPIO as GPIO

#************************************
''' Class T/RH Sensor '''
#************************************
class TRHSensor:
    def __init__(self, lab):
        self.lab = lab
        self.date = time.strftime("%Y%m%d")
        self.time = time.strftime("%H:%M:%S")
        self.sensData = []
        self.ip = getIP()

    #************************************
    ''' Read Sensors '''
    #************************************
    def readSensors(self):
        self.sensData.extend([self.lab, self.ip, self.date, self.time])
        try:
            sensor = BME280(t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)
            self.sensData.extend([sensor.read_temperature(),
                                  sensor.read_pressure() / 100,
                                  sensor.read_humidity()])
        except:
            print("\n SENSOR NOT CONNECTED ")
            self.sensData.extend([0.0,0.0,0.0])
        return self.sensData

    #************************************
    ''' Print Values on screen '''
    #************************************
    def printUI(self):
        print("\n Lab: ", self.lab)
        print(" IP: ", self.ip)
        print(" Date: ", self.date)
        print(" Time: ", self.time)
        print(" Temperature = {0:0.1f} deg C".format(self.sensData[4]))
        print(" Pressure = {0:0.1f} hPa".format(self.sensData[5]))
        print(" Humidity = {0:0.1f} %".format(self.sensData[6]),"\n")

#************************************
''' Main initialization routine '''
#************************************
if __name__ == "__main__":
    
    lab = "lab1"
    
    #************************************
    ''' Read from T/RH sensor '''
    #************************************
    trhSensor = TRHSensor(lab)
    sensData = trhSensor.readSensors()
    trhSensor.printUI()
    sys.exit(main())
