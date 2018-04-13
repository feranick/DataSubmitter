# DataSubmitter
## Plugin for data submission into MongoDB
To be completed

## Usage
### Regular version:
    python3 DataSubmitter.py <lab-identifier> <mongodb-auth-file>

### Launcher    
The software will be automated through a script (DataSubmitter_launcher.sh). Since the RPi is 
connected online via WiFi-DHCP, the IP may change. Through this script, the IP is collected
on boot and saved on a dedicated server. This is achieved by adding the following to /etc/rc.local:

    su pi -c 'home/pi/DataSubmitter/EnvMonitor_launcher.sh'

The same script will eventually run the software itself at periodic intervals. 

## Contact
Nicola Ferralis <feranick@hotmail.com>
    

