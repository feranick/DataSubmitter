#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
*
* DataSubmitter
* version: 20180731a
*
* By: Nicola Ferralis <feranick@hotmail.com>
*
***********************************************************
'''
#print(__doc__)

#***************************************************
''' This is needed for installation through pip '''
#***************************************************
def DataSubmitter():
    main()
#***************************************************

import configparser, logging, sys, math, json, os.path, time, base64
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEvent, FileCreatedEvent, FileSystemEventHandler
from libDataSub import *

#************************************
''' Main '''
#************************************
def main():
    file = sys.argv[1]

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
    
    print("start")
    handler = ManualFileHandler(file)
    handler.run()
    
    '''
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    '''

#************************************
''' Main initialization routine '''
#************************************
if __name__ == "__main__":
    sys.exit(main())
