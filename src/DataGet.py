#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* DataGet
* version: 20180530a
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

#***************************************************
''' This is needed for installation through pip '''
#***************************************************
def DataGet():
    main()
#***************************************************

import configparser, logging, sys, math, json, os.path, time, base64
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from libDataSub import *

#************************************
''' Main '''
#************************************
def main():
    conf = Configuration()
    if os.path.isfile(conf.configFile) is False:
        print("Configuration file does not exist: Creating one.")
        conf.createConfig()
    conf.readConfig(conf.configFile)

    #************************************
    ''' Launch observer'''
    #************************************
    path = conf.dataFolder
    #path = sys.argv[1] if len(sys.argv) > 1 else '.'

    #************************************
    ''' Push to MongoDB '''
    #************************************
    try:
        jsonData={}
        conn = DataSubmitterMongoDB(jsonData)
        #conn.getById(sys.argv[1])
        conn.getByFile(sys.argv[1])
    except:
        print("\n Getting entry from database failed!\n")

#************************************
''' Main initialization routine '''
#************************************
if __name__ == "__main__":
    sys.exit(main())
