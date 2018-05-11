#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* libDataSub
* version: 20180511a
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
''' Class NewFileHandler '''
''' Submission method, once data is detected '''
#************************************************
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        #************************************
        ''' Manage data'''
        #************************************
        dc = DataCollector(event.src_path[:])
        data = dc.getData()
        dc.printUI()
        jsonData = dc.makeJson()
    
        #************************************
        ''' Push to MongoDB '''
        #************************************
        try:
            conn = DataSubmitterMongoDB(jsonData)
            conn.pushToMongoDB()
        except:
            print("\n Submission to database failed!\n")

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
        self.file = file[2:]
        self.tag = self.file[:11]
        self.itemId = self.tag[-1]
        self.sample = self.tag[:-1]
        self.date = time.strftime("%Y%m%d")
        self.time = time.strftime("%H:%M:%S")
        self.ip = getIP()
        self.data = []
        self.header = config.headers
        self.encoding = config.encoding
        self.type = config.dataType
        if self.type == 0:
            print(" Processing images/binary")
        else:
            print(" Processing text/ASCII")
    
    #************************************
    ''' Collect Data '''
    #************************************
    def getData(self):
        self.data.extend([self.institution, self.lab, self.equipment, self.ip, self.date,
            self.time, self.file, self.sample, self.itemId, self.encoding, self.type])
        try:
            if self.type == 0:
                with open(self.file, "rb") as f:
                    lines = [base64.b64encode(f.read())] # uncomment for images/binary
            elif self.type == 1:
                with open(self.file, "rb") as f:
                    lines = np.loadtxt(f, unpack=True) # uncomment for text/ASCII
            elif self.type == 2:
                df = pd.read_csv(self.file, usecols=[11,12])
                lines = [df.iloc[:,0:1].values.tolist(),df.iloc[:,1:2].values.tolist()]
            print(lines)
            self.data.extend(["True"])
            self.data.extend(lines)
        except:
            self.data.extend(["False"])
            if self.type == 0:
                self.data.extend([[0.0, 0.0]])
            else:
                self.data.extend([[0.0, 0.0], [0.0, 0.0]])
        print(self.data)
        return self.data
        
    def formatData(self):
        if self.type == 0:  # for images/binary
            jsonData = None
        else:
            jsonData = {}
        for i in range(len(self.header)):
            jsonData.update({self.header[i] : self.data[12+i]})
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
            'institution' : self.data[0],
            'lab' : self.data[1],
            'equipment' : self.data[2],
            'IP' : self.data[3],
            'date' : self.data[4],
            'time' : self.data[5],
            'file' : self.data[6],
            'substrate': self.data[7],
            'itemId' : self.data[8],
            'encoding' : self.data[9],
            'type' : self.data[10],
            'success' : self.data[11],
            }
        jsonData.update(self.formatData())
        print(" JSON Data:\n",jsonData)
        if self.type == 0:
            return (jsonData)
        else:
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
        print(" ItemID: ", self.itemId)
        print(" Sample: ", self.sample)
        print(" Encoding: ", self.encoding)
        print(" Type: ", self.type)
        print(" Success: ", self.data[11])
        for i in range(len(self.header)):
            print(" {0} = {1} ".format(self.header[i], self.data[12+i]))
        print("")

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
            db_entry = db.dataSubmitter.insert_one(self.jsonData)
            print(" Data entry successful (id:",db_entry.inserted_id,")\n")
        except:
            print(" Data entry failed.\n")

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
        #self.home = str(Path.home())+"/"
        self.home = str(Path.cwd())+"/"
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
            'institution' : 'institution1',
            'lab' : 'lab1',
            'equipment' : 'equipment1',
            }
    '''
    # for images/binary
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['image'],
            'encoding' : 'base64.b64encode',
            'dataType' : 0,
            }
    
    # for text/ASCII
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['header0','header1'],
            'encoding' : 'text/ASCII',
            'dataType' : 1,
            }
    '''
    # for text/csv
    def defineData(self):
        self.conf['Data'] = {
            'headers' : ['header0','header1'],
            'encoding' : 'text/CSV',
            'dataType' : 2,
            }
    
    def defineConfDM(self):
        self.conf['DM'] = {
            'DbHostname' : "localhost",
            'DbPortNumber' : "27017",
            'DbName' : "DataSubmitter",
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
            self.dataFolder = self.sysConfig['dataFolder']

            self.institution = self.instrumentationConfig['institution']
            self.lab = self.instrumentationConfig['lab']
            self.equipment = self.instrumentationConfig['equipment']

            self.headers = eval(self.dataConfig['headers'])
            self.dataType = eval(self.dataConfig['dataType'])
            self.encoding = self.dataConfig['encoding']
            
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

