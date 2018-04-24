#!/bin/bash

#####################################
#
# DataSubmitter IP and launcher
#
# v. 20180413a
#
# Nicola Ferralis <ferralis@mit.edu>
#
#####################################

lab="Lab1"

remote="pi@server.com:/home/pi/DataSubmitter-logs"
file="/home/pi/DataSubmitter/DataSubmitter_$lab.txt"

sleep 60
IP=$(hostname -I)

echo "DataSubmitter lab: "$lab > $file
echo "IP: "$IP >> $file
echo $(date) >> $file
scp $file $remote

# Start pigpiod
#sudo pigpiod

# Eventually, the actual Software for running the DataSubmitter could be launched from here
