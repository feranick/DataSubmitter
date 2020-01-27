# DataSubmitter
## Plugin for data submission into MongoDB
Automated data submission/retrieval for ASCII and images into mongoDB. DataSubmitter provides an automated data submission and conversion (customizable for both text/ASCII and binary/images). Binary data is converted into text using base64 encoding. DataGet can be used to retrieve and restore data (both text and binary) from mongodb. 

## Usage
### From local file version.
    python3 DataSubmitter.py
### Installation with pip. 
Create a wheel package (wheel module required):

    python3 setup bdist_wheel
    
Install directly:

    sudo pip3 install dist/DataSubmitter_...

Launch from the terminal in the folder with data:

    DataSubmitter
    DataGet
    
### MongoDB: Quick installation
While this is far from being a comprehensive guide, this will get you going. Install the required packages according to your OS. Then edit the config file:

    sudo nano /etc/mongodb.conf
    
to make sure the correct IP and port are selected. Keep the authentication flag `auth = true` commented. 
Restart the ```mongodb``` service. Then run:

    mongo

Set administration rights and authentication:

    use admin
    db.createUser({user:'admin',pwd:'pwd',roles:[{role:"userAdminAnyDatabase", db:'admin'}]})
    use DataSubmitter
    db.createUser({user:'user1',pwd:'user1',roles:[{role:"readWrite", db:'DataSubmitter'}]})
    quit()
    
Enable authentication in  ```mongodb.conf```, by uncommenting:

    auth = true
    
Restart ```mongodb``` service. 

    sudo systemctl restart mongodb.service

Use EnvMonitor.

### Launcher (Obsolete, no longer supported)
The software will be automated through a script (DataSubmitter_launcher.sh). Since the RPi is 
connected online via WiFi-DHCP, the IP may change. Through this script, the IP is collected
on boot and saved on a dedicated server. This is achieved by adding the following to /etc/rc.local:

    su pi -c 'home/pi/DataSubmitter/DataSubmitter_launcher.sh'

The same script will eventually run the software itself at periodic intervals. 

## Contact
Nicola Ferralis <feranick@hotmail.com>
    

