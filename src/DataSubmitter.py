#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* DataSubmitter
* version: 20180423b
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

import configparser, logging, sys, math, json, os.path, time
import pandas as pd
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEvent, FileCreatedEvent, FileSystemEventHandler
global MongoDBhost

def main():
    conf = Configuration()
    if os.path.isfile(conf.configFile) is False:
        print("Configuration file does not exist: Creating one.")
        conf.createConfig()
        return
    conf.readConfig(conf.configFile)

    #************************************
    ''' Launch observer'''
    #************************************
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

#************************************************
''' Submission method, once data is detected '''
#************************************************
def sumbmitData(file):
    #************************************
    ''' Manage data'''
    #************************************
    dc = DataCollector(file)
    data = dc.getData()
    dc.printUI()
    jsonData = dc.makeJson()
    
    #************************************
    ''' Push to MongoDB '''
    #************************************
    conn = DataSubmitterMongoDB(jsonData)
    conn.pushToMongoDB()

#************************************
''' Class NewFileHandler '''
#************************************
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(event.src_path[2:])
        sumbmitData(event.src_path[2:])

#************************************
''' Class DataCollector '''
#************************************
class DataCollector:
    def __init__(self, file):
        config = Configuration()
        config.readConfig(config.configFile)
        self.institution = config.institution
        self.lab = config.lab
        self.equipment = config.equipment
        self.file = file
        self.date = time.strftime("%Y%m%d")
        self.time = time.strftime("%H:%M:%S")
        self.ip = getIP()
        self.data = []
        self.header = config.headers
        self.type = config.dataType

    #************************************
    ''' Collect Data '''
    #************************************
    def getData(self):
        self.data.extend([self.institution, self.lab, self.equipment, self.ip, self.date, self.time, self.file])
        try:
            self.data.extend([[1,2],[3,4]])
        except:
            self.data.extend([[0.0,0.0][0.0,0.0]])
        return self.data
        
    def formatData(self, type):
        jsonData = {}
        for i in range(len(self.header)):
            jsonData.update({self.header[i] : self.data[7+i]})
        if type == 0:
            listData = jsonData
        else:
            import pandas as pd
            dfData = pd.DataFrame(jsonData)
            dfData = dfData[[self.header[0], self.header[1]]]
            listData = dict(dfData.to_dict(orient='split'))
            listData['columnlabel'] = listData.pop('columns')
            listData['output'] = listData.pop('data')
            del listData['index']
        return listData
        
    def makeJson(self):
        jsonData = {
            'institution' : self.data[0],
            'lab' : self.data[1],
            'equipment' : self.data[2],
            'IP' : self.data[3],
            'date' : self.data[4],
            'time' : self.data[5],
            'file' : self.data[6],
            }
        jsonData.update(self.formatData(self.type))
        print(" JSON Data:\n",jsonData)
        return json.dumps(jsonData)

    #************************************
    ''' Print Values on screen '''
    #************************************
    def printUI(self):
        print("\n Institution: ", self.institution)
        print(" Lab: ", self.lab)
        print(" Equipment: ", self.equipment)
        print(" IP: ", self.ip)
        print(" Date: ", self.date)
        print(" Time: ", self.time)
        print(" File: ", self.file)
        for i in range(len(self.header)):
            print(" {0} = {1} ".format(self.header[i], self.data[7+i]))
        print("")

#************************************
''' Class Database '''
#************************************
class DataSubmitterMongoDB:
    def __init__(self, jsonData):
        self.config = Configuration()
        self.config.readConfig(self.config.configFile)
        self.jsonData = jsonData

    def connectDB(self):
        from pymongo import MongoClient
        client = MongoClient(self.config.DbHostname, int(self.config.DbPortNumber))
        auth_status = client[self.config.DbName].authenticate(self.config.DbUsername,
            self.config.DbPassword, mechanism='SCRAM-SHA-1')
        print("\n Pushing to MongoDB: Authentication status = {0}".format(auth_status))
        return client

    def printAuthInfo(self):
        print(self.config.DbHostname)
        print(self.config.DbPortNumber)
        print(self.config.DbName)
        print(self.config.DbUsername)
        print(self.config.DbPassword)
    
    def pushToMongoDB(self):
        client = self.connectDB()
        db = client[self.config.DbName]
        try:
            db_entry = db.EnvTrack.insert_one(json.loads(self.jsonData))
            print(" Data entry successful (id:",db_entry.inserted_id,")\n")
        except:
            print(" Data entry failed.\n")

####################################################################
# Configuration
####################################################################
class Configuration():
    def __init__(self):
        self.home = str(Path.home())+"/"
        self.configFile = self.home+"DataSubmitter.ini"
        self.generalFolder = self.home+"DataSubmitter/"
        Path(self.generalFolder).mkdir(parents=True, exist_ok=True)
        self.logFile = self.generalFolder+"DataSubmitter.log"
        #self.dataFolder = self.generalFolder + 'data/'
        #Path(self.dataFolder).mkdir(parents=True, exist_ok=True)
        #self.customConfigFolder = self.generalFolder+'saved_configurations'
        #Path(self.customConfigFolder).mkdir(parents=True, exist_ok=True)
        self.conf = configparser.ConfigParser()
        self.conf.optionxform = str
    
    # Create configuration file
    def createConfig(self):
        try:
            self.defineSystem()
            self.defineInstrumentation()
            self.defineData()
            self.defineConfDM()
            with open(self.configFile, 'w') as configfile:
                self.conf.write(configfile)
        except:
            print("Error in creating configuration file")

    # Hadrcoded default definitions for the confoguration file
    def defineSystem(self):
        self.conf['System'] = {
            'appVersion' : 0,
            'loggingLevel' : logging.INFO,
            'loggingFilename' : self.logFile,
            }
    def defineInstrumentation(self):
        self.conf['Instrumentation'] = {
            'institution' : 'institution1',
            'lab' : 'lab1',
            'equipment' : 'equipment1',
            }
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['header0','header1'],
            'dataType' : 0,
            }
    def defineConfDM(self):
        self.conf['DM'] = {
            'DbHostname' : "localhost",
            'DbPortNumber' : "7101",
            'DbName' : "Tata",
            'DbUsername' : "user1",
            'DbPassword' : "user1",
            }

    # Read configuration file into usable variables
    def readConfig(self, configFile):
        self.conf.read(configFile)
        self.sysConfig = self.conf['System']
        self.appVersion = self.sysConfig['appVersion']
        try:
            self.instrumentationConfig = self.conf['Instrumentation']
            self.dataConfig = self.conf['Data']
            self.dmConfig = self.conf['DM']

            self.loggingLevel = self.sysConfig['loggingLevel']
            self.loggingFilename = self.sysConfig['loggingFilename']

            self.institution = self.instrumentationConfig['institution']
            self.lab = self.instrumentationConfig['lab']
            self.equipment = self.instrumentationConfig['equipment']

            self.headers = eval(self.dataConfig['headers'])
            self.dataType = self.dataConfig['dataType']
            
            self.DbHostname = self.dmConfig['DbHostname']
            self.DbPortNumber = self.conf.getint('DM','DbPortNumber')
            self.DbName = self.dmConfig['DbName']
            self.DbUsername = self.dmConfig['DbUsername']
            self.DbPassword = self.dmConfig['DbPassword']
        
        except:
            print("Configuration file is for an earlier version of the software")
            oldConfigFile = str(os.path.splitext(configFile)[0] + "_" +\
                    str(datetime.now().strftime('%Y%m%d-%H%M%S'))+".ini")
            print("Old config file backup: ",oldConfigFile)
            os.rename(configFile, oldConfigFile )
            print("Creating a new config file.")
            self.createConfig()
            self.readConfig(configFile)

    # Save current parameters in configuration file
    def saveConfig(self, configFile):
        try:
            with open(configFile, 'w') as configfile:
                self.conf.write(configfile)
        except:
            print("Error in saving parameters")

#************************************
''' Get system IP '''
#************************************
def getIP():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

#************************************
''' Main initialization routine '''
#************************************
if __name__ == "__main__":
    sys.exit(main())
