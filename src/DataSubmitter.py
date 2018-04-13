#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* DataSubmitter
* version: 20180413a
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

import sys, math, json, os.path, time
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
    data = DataCollector(lab)
    collectedData = data.readSensors()
    data.printUI()
    
    #************************************
    ''' Make JSON and push to MongoDB '''
    #************************************
    conn = DSmongoDB(data.typeData,collectedData,mongoFile)
    print("\n JSON:\n",conn.makeJSON(),"\n")
    print(" Pushing to MongoDB:")
    conn.pushToMongoDB()

#************************************
''' Class T/RH Sensor '''
#************************************
class DataCollector:
    def __init__(self, lab):
        self.lab = lab
        self.date = time.strftime("%Y%m%d")
        self.time = time.strftime("%H:%M:%S")
        self.ip = getIP()
        self.collectedData = []
        self.typeData = ["test1", "test2"]

    #************************************
    ''' Read Sensors '''
    #************************************
    def readSensors(self):
        self.collectedData.extend([self.lab, self.ip, self.date, self.time])
        try:
            self.collectedData.extend([1,2])
        except:
            self.collectedData.extend([0.0,0.0])
        return self.collectedData

    #************************************
    ''' Print Values on screen '''
    #************************************
    def printUI(self):
        print("\n Lab: ", self.lab)
        print(" IP: ", self.ip)
        print(" Date: ", self.date)
        print(" Time: ", self.time)
        
        print(" {0} = {1:0.1f} ".format(self.typeData[0], self.collectedData[4]))
        print(" {0} = {1:0.1f} ".format(self.typeData[1], self.collectedData[5]),"\n")

#************************************
''' Class Database '''
#************************************
class DSmongoDB:
    def __init__(self, type, data, file):
        self.data = data
        self.type = type
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
        print(' Authentication status = {0} \n'.format(auth_status))
        return client

    def printAuthInfo(self):
        print(self.hostname)
        print(self.port_num)
        print(self.dbname)
        print(self.username)
        print(self.password)

    def makeJSON(self):
        dataj = {
            'lab' : self.data[0],
            'IP' : self.data[1],
            'date' : self.data[2],
            'time' : self.data[3],
            '{0}'.format(self.type[0]) : '{0:0.1f}'.format(self.data[4]),
            '{0}'.format(self.type[1]) : '{0:0.1f}'.format(self.data[5]),
            }
        return json.dumps(dataj)
    
    def pushToMongoDB(self):
        jsonData = self.makeJSON()
        client = self.connectDB()
        db = client[self.dbname]
        try:
            db_entry = db.EnvTrack.insert_one(json.loads(jsonData))
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
