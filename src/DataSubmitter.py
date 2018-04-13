#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* DataSubmitter
* version: 20180413b
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

import sys, math, json, os.path, time
import pandas as pd
global MongoDBhost

def main():
    if len(sys.argv)<3 or os.path.isfile(sys.argv[2]) == False:
        print(__doc__)
        print(' Usage:\n  python3 DataSubmitter.py <lab-identifier> <mongoFile>\n')
        return
    
    lab = sys.argv[1]
    mongoFile = sys.argv[2]
    
    #************************************
    ''' Read from T/RH sensor '''
    #************************************
    dc = DataCollector(lab, lab, lab)
    data = dc.getData()
    dc.printUI()
    jsonData = dc.makeJson()
    
    #************************************
    ''' Push to MongoDB '''
    #************************************
    conn = DataSubmitterMongoDB(jsonData,mongoFile)
    conn.pushToMongoDB()

#************************************
''' Class DataCollector '''
#************************************
class DataCollector:
    def __init__(self, institution, lab, equipment):
        self.institution = institution
        self.lab = lab
        self.equipment = equipment
        self.date = time.strftime("%Y%m%d")
        self.time = time.strftime("%H:%M:%S")
        self.ip = getIP()
        self.data = []
        self.header = ["header0", "header1"]
        self.type = 1 #data format for MongoDB

    #************************************
    ''' Collect Data '''
    #************************************
    def getData(self):
        self.data.extend([self.institution, self.lab, self.equipment, self.ip, self.date, self.time])
        try:
            self.data.extend([[1,2],[3,4]])
        except:
            self.data.extend([[0.0,0.0][0.0,0.0]])
        return self.data
        
    def formatData(self, type):
        jsonData = {}
        for i in range(len(self.header)):
            jsonData.update({self.header[i] : self.data[6+i]})
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
        for i in range(len(self.header)):
            print(" {0} = {1} ".format(self.header[i], self.data[6+i]))
        print("")

#************************************
''' Class Database '''
#************************************
class DataSubmitterMongoDB:
    def __init__(self, jsonData, file):
        self.jsonData = jsonData
        with open(file, 'r') as f:
            f.readline()
            self.hostname = f.readline().rstrip('\n')
            f.readline()
            self.port_num = f.readline().rstrip('\n')
            f.readline()
            self.dbname = f.readline().rstrip('\n')
            f.readline()
            self.username = f.readline().rstrip('\n')
            f.readline()
            self.password = f.readline().rstrip('\n')

    def connectDB(self):
        from pymongo import MongoClient
        client = MongoClient(self.hostname, int(self.port_num))
        auth_status = client[self.dbname].authenticate(self.username, self.password, mechanism='SCRAM-SHA-1')
        print("\n Pushing to MongoDB: Authentication status = {0}".format(auth_status))
        return client

    def printAuthInfo(self):
        print(self.hostname)
        print(self.port_num)
        print(self.dbname)
        print(self.username)
        print(self.password)
    
    def pushToMongoDB(self):
        client = self.connectDB()
        db = client[self.dbname]
        try:
            db_entry = db.EnvTrack.insert_one(json.loads(self.jsonData))
            print(" Data entry successful (id:",db_entry.inserted_id,")\n")
        except:
            print(" Data entry failed.\n")

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
