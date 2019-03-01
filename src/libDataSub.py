#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* libDataSub
* version: 20190228c
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

import configparser, logging, sys, math, json, os.path, time, base64, csv
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEvent, FileCreatedEvent, FileSystemEventHandler

#************************************************
''' RoutineFileHandler method'''
#************************************************
def RoutineFileHandler(file):
    #************************************
    ''' Manage data'''
    #************************************
    dc = DataCollector(file)
    data, validFile = dc.getData()
    if validFile:
        dc.printUI()
        jsonData, sub = dc.makeJson()
    
        #************************************
        ''' Push to MongoDB '''
        #************************************
        try:
            conn = DataSubmitterMongoDB(jsonData)
            conn.checkCreateLotDM(sub)
            conn.pushToMongoDB()
        except:
            print("\n Submission to database failed!\n")
    else:
        print(" Invalid file\n")
        
#************************************************
''' Class NewFileHandler '''
''' Submission method, once data is detected '''
#************************************************
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        RoutineFileHandler(event.src_path[:])

#************************************************
''' Class ManualFileHandler '''
''' Submission method, manual '''
#************************************************
class ManualFileHandler:
    def __init__(self, file):
        self.file = file
    def run(self):
        RoutineFileHandler(self.file)

#************************************
''' Class DataCollector '''
#************************************
class DataCollector:
    def __init__(self, file):
        config = Configuration()
        config.readConfig(config.configFile)
        self.file = file
        self.extension = config.extension
        self.equipment = config.equipment
        self.substrate = os.path.relpath(file, config.dataFolder)[:10]
        self.name = config.name
        self.architecture = config.architecture
        self.measType = config.measType
        self.itemId = config.itemId
        self.date = [time.strftime("%Y-%m-%d")]
        self.time = [time.strftime("%H-%M-%S")]
        self.data = []
        self.header = config.headers
        self.encoding = config.encoding
        self.type = config.dataType
        self.ncols = config.ncols
        if self.type == 0:
            print(" Processing images/binary")
        else:
            print(" Processing text/ASCII")
    
    #************************************
    ''' Collect Data '''
    #************************************
    def getData(self):
        self.data.extend([self.equipment, self.substrate,self.name,
        self.measType, self.itemId, self.date, self.time, self.file, self.encoding, self.type])
        self.lenData = len(self.data)+1
        
        if os.path.splitext(self.file)[-1][1:] != self.extension:
            return None, False
        
        try:
            if self.type == 0:
                with open(self.file, "rb") as f:
                    lines = [base64.b64encode(f.read())] # uncomment for images/binary
            elif self.type == 1:
                with open(self.file, "rb") as f:
                    lines = np.loadtxt(f, unpack=True) # uncomment for text/ASCII
            elif self.type == 2:
                df = pd.read_csv(self.file, usecols=self.ncols)
                lines = df.iloc[:,0:len(self.ncols)].T.values
            print(lines)
            self.data.extend(["True"])
            self.data.extend(lines)
        except:
            self.data.extend(["False"])
            if self.type == 0:
                self.data.extend([[0.0, 0.0]])
            else:
                self.data.extend([[0.0, 0.0], [0.0, 0.0]])
        #print(self.data)
        return self.data, True
        
    def formatData(self):
        if self.type == 0:  # for images/binary
            jsonData = None
        else:
            jsonData = {}
        for i in range(len(self.header)):
            jsonData.update({self.header[i] : self.data[self.lenData+i]})
        if self.type == 0:  # for images/binary
            listData = jsonData
        else:  # for text/ASCII
            dfData = pd.DataFrame(jsonData)
            dfData = dfData[[self.header[0], self.header[1]]]
            listData = dict(dfData.to_dict(orient='split'))
            listData['columnlabel'] = listData.pop('columns')
            listData['output'] = listData.pop('data')
            del listData['index']
        return listData
        
    def makeJson(self):
        jsonData = {
            'equipment' : self.data[0],
            'substrate' : self.data[1],
            'name' : self.data[2],
            'measType' : self.data[3],
            'itemId' : self.data[4],
            'date' : self.data[5],
            'time' : self.data[6],
            'file' : self.data[7],
            #'encoding' : self.data[10],
            #'type' : self.data[11],
            #'success' : self.data[12],
            }
        jsonData.update(self.formatData())
        print(" JSON Data:\n",jsonData)
        if self.type == 0:
            return (jsonData), self.substrate
        else:
            return json.dumps(jsonData), self.substrate

    #************************************
    ''' Print Values on screen '''
    #************************************
    def printUI(self):
        print("\n Equipment: ", self.equipment)
        print(" Substrate: ", self.substrate)
        print(" Name: ", self.name)
        #print(" Architecture: ", self.architecture)
        print(" measType: ", self.measType)
        print(" itemId: ", self.itemId)
        print(" Date: ", self.date)
        print(" Time: ", self.time)
        print(" File: ", self.file)
        print(" ItemID: ", self.itemId)
        print(" Encoding: ", self.encoding)
        print(" Type: ", self.type)
        #print(" Success: ", self.data[11])
        for i in range(len(self.header)):
            print(" {0} = {1} ".format(self.header[i], self.data[self.lenData+i]))
        print("")

    def archSubstrate(self, ind):
        if ind == 0:
            name = "0_blank"
            return name, {'substrates': {'isCollapsed': False, 'label': 'deviceID', 'material': '', 'flex': False, 'area': '', 'layers': [], 'attachments': [], 'devices': [{'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}]}}

#************************************
''' Class Database '''
#************************************
class DataSubmitterMongoDB:
    def __init__(self, jsonData):
        self.config = Configuration()
        self.config.readConfig(self.config.configFile)
        if self.config.dataType == 0:
            self.jsonData = jsonData
        else:
            self.jsonData = json.loads(jsonData)

    def connectDB(self):
        from pymongo import MongoClient
        client = MongoClient(self.config.DbHostname, int(self.config.DbPortNumber))
        auth_status = client[self.config.DbName].authenticate(self.config.DbUsername,self.config.DbPassword)
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
            db_entry = db.Measurement.insert_one(self.jsonData)
            print(" Data entry successful (id:",db_entry.inserted_id,")\n")
        except:
            print(" Data entry failed.\n")

    # View entry in DM page for substrate/device
    def checkCreateLotDM(self, deviceID):
        client = self.connectDB()
        db = client[self.config.DbName]
        #try:
        entry = db.Lot.find_one({'label':deviceID[:8]})
        if entry:
            #db.Lot.update_one({ '_id': entry['_id'] },{"$push": self.getArchConfig(deviceID, row, col)}, upsert=False)
            msg = " Data entry for this batch found in DM. Created substrate: "+deviceID
        else:
            print(" No data entry for this substrate found in DM. Creating new one...")
            jsonData = {'label' : deviceID[:8], 'date' : deviceID[2:8], 'description': '', 'notes': '', 'tags': [], 'substrates': [{'isCollapsed': False, 'label': deviceID, 'material': '', 'flex': False, 'area': '', 'layers': [], 'attachments': [], 'devices': [{'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}, {'size': '', 'measurements': []}]}]}
            db_entry = db.Lot.insert_one(json.loads(json.dumps(jsonData)))
                #db.Lot.update_one({ '_id': db_entry.inserted_id },{"$push": self.getArchConfig(deviceID,row,col)}, upsert=False)
            msg = " Created batch: " + deviceID[:8] + " and device: "+deviceID
        print(msg)
        
        
        #except:
        #    print(" Connection with DM via Mongo cannot be established.")

    def getById(self, id):
        from bson.objectid import ObjectId
        client = self.connectDB()
        db = client[self.config.DbName]
        db_entry = db.dataSubmitter.find_one({"_id": ObjectId(id)})
        print("\n Restoring file: :",db_entry['file'][2:])
        with open(db_entry['file'][2:], "wb") as fh:
            fh.write(base64.b64decode(db_entry[self.config.headers[0]]))

    def getByFile(self, file):
        client = self.connectDB()
        db = client[self.config.DbName]
        db_entry = db.dataSubmitter.find_one({"file": "./"+file})
        print("\n Restoring file: :",db_entry['file'][2:])
        with open(db_entry['file'][2:], "wb") as fh:
            fh.write(base64.b64decode(db_entry[self.config.headers[0]]))

####################################################################
# Configuration
####################################################################
class Configuration():
    def __init__(self):
        self.home = str(Path.home())+"/"
        #self.home = str(Path.cwd())+"/"
        self.configFile = self.home+"DataSubmitter.ini"
        self.generalFolder = self.home+"DataSubmitter/"
        #Path(self.generalFolder).mkdir(parents=True, exist_ok=True)
        self.logFile = self.generalFolder+"DataSubmitter.log"
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
            'dataFolder' : ".",
            }
    def defineInstrumentation(self):
        self.conf['Instrumentation'] = {
            'measType' : 'test',
            'equipment' : 'test',
            'name' : 'test',
            'architecture' : '',
            'itemId' : '1'
            }
    '''
    # for images/binary
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['image'],
            'encoding' : 'base64.b64encode',
            'dataType' : 0,
            'ncols': [0,1],
            }
    
    # for text/ASCII
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['header0','header1'],
            'encoding' : 'text/ASCII',
            'dataType' : 1,
            'ncols': [0,1],
            }
    '''
    # for text/csv
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['X','Y'],
            'encoding' : 'text/CSV',
            'dataType' : 1,
            'ncols': [0,1],
            'extension' : 'txt',
            }
    
    def defineConfDM(self):
        self.conf['DM'] = {
            'DbHostname' : "my.site.com",
            'DbPortNumber' : "27017",
            'DbName' : "test",
            'DbUsername' : "user",
            'DbPassword' : "pwd",
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
            self.dataFolder = self.sysConfig['dataFolder']

            self.equipment = self.instrumentationConfig['equipment']
            self.name = self.instrumentationConfig['name']
            self.measType = self.instrumentationConfig['measType']
            self.architecture = self.instrumentationConfig['architecture']
            self.itemId = self.instrumentationConfig['itemId']

            self.headers = eval(self.dataConfig['headers'])
            self.dataType = eval(self.dataConfig['dataType'])
            self.encoding = self.dataConfig['encoding']
            self.ncols = eval(self.dataConfig['ncols'])
            self.extension = self.dataConfig['extension']
            
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

