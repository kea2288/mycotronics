#! /usr/bin/python3

import os
import time
import logging
import serial
import pyrebase
from picamera import PiCamera
import config

# <--- Device settings --->
conn = False
token = ''
dataDict = {'CO2': '', 'Temperature': '', 'Humidity': ''}
id = config.DEVICE_ID
delayTime = 0
tempHumiPin = 4
grblMSG = ''
gcode = 'G1 X1.6 F20'
camera = ''
# Serial initialization
ser0 = serial.Serial(config.PORT_0, config.BAUDRATE_0)
ser1 = serial.Serial(config.PORT_1, config.BAUDRATE_1)
# Device log initialization
logger = logging.getLogger('mycotronics: ' + id)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('/home/pi/mycotronics/logs/data1.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)
picsDir = '/home/pi/mycotronics/pictures'

# <--- Firebase settings --->
db_config = {
    "apiKey": "AIzaSyBNM8ll5KyDln9H5z7NCBPT71DgbLHuMi4",
    "authDomain": "stanford-boxes.firebaseapp.com",
    "databaseURL": "https://stanford-boxes.firebaseio.com",
    "storageBucket": "stanford-boxes.appspot.com",
    "serviceAccount": "/home/pi/mycotronics/cloud/stanford-boxes-firebase-adminsdk-3urx2-a4dafa174c.json"
}


def check_internet():
    hostname = "google.com" #example
    response = os.system("ping -c 1 " + hostname)

    # and then check the response...
    if response == 0:
        logger.info('Google pinged successfully.')
        return(True)
    logger.warning('Google pinged unsuccessfully!')
    return(False)


def check_sensors():
    read_sensors()
    if dataDict['CO2'] == 'Fail':
        logger.warning('CO2 sensor disconnected!')
    else:
        logger.info('CO2 sensor connected.')
    if dataDict['Temperature'] == 'Fail' or dataDict['Humidity'] == 'Fail':
        logger.warning('Temperature/Humidity sensor disconnected!')
    else:
        logger.info('Temperature/Humidity sensor connected.')


def check_grbl():
    ser1.write(b'\r\n\r\n')
    time.sleep(2)   # Wait for grbl to initialize
    ser1.flushInput() # Flush startup text in serial input
    status = grbl_command('G0', 'check')
    if status == 'ok':
        logger.info('GRBL connection succeed.')
    else:
        logger.warning('GRBL connection fail!')


def check_camera():
    try:
        startCAM = OpenCamera()
        logger.info('Camera initialized successfully.')
        startCAM.close()
    except:
        logger.warning('Camera initialized unsuccessfully!')


def push_to_db(id, device, value):
    data = {"timestamp": {".sv": "timestamp"}, "value": value}

    # Write to DB CO2 value
    results = db.child("data/{0}/{1}.json?print=silent".format(id, device)).push(data)


def read_sensors():
    sensorDATA = ['0', '1']
    done = 0
    while done < 3:
        readSerial = ser0.readline().decode('utf-8', 'ignore')[:-2]
        sensorDATA = readSerial.split(': ')
        if len(sensorDATA) == 2:
            if (sensorDATA[0] == 'CO2' or sensorDATA[0] == 'Temperature' or
                sensorDATA[0] == 'Humidity'):
                dataDict[sensorDATA[0]] = sensorDATA[1]
                done += 1


def grbl_command(command, flag):
    ser1.write(str.encode(command + '\n')) # Send g-code block to grbl
    grblFedback = ser1.readline().decode('utf-8') # Wait for grbl response with carriage return
    if flag == 'run':
        if len(grblFedback.split(',')) > 2:
            grblMSG = grblFedback.split(',')[1]
            return(grblMSG)
    elif flag == 'check':
        status = grblFedback[:-2]
        return(status)


class OpenCamera:
    def __init__(self):
        self.camera = PiCamera()
        self.picNAME = ''

    def set_resolution(self, width, height):
        self.camera.resolution = (width, height)

    def take_pic(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.picNAME = 'pic_{0}.jpg'.format(timestamp)
        self.camera.capture('/home/pi/mycotronics/pictures/' + self.picNAME)

    def close(self):
        self.camera.close()


while True:
    logger.info('Program started.')
    check_sensors()
    check_grbl()
    check_camera()
    check_internet()
    try:
        firebase = pyrebase.initialize_app(db_config)
        auth = firebase.auth() # Authentication
        token = auth.create_custom_token("rpi1-2017")
        user = auth.sign_in_with_custom_token(token)
        # Database connection
        db = firebase.database()
        storage = firebase.storage()
        logger.info('Firebase connected successfully.')
        conn = True
    except:
        logger.warning('Firebase connection fail!')

    while conn:
        # Read config from DB
        results = db.child('configs/{0}'.format(id)).get().val()

        # Setting config
        delayTime = results['sleep']
        picSIZE =  results['pic_size'].split(', ')
        w = int(picSIZE[0])
        h = int(picSIZE[1])

        # Read from sensors and push to DB
        ser0.flushInput()
        read_sensors()
        if dataDict['Temperature'] == 'Fail' or dataDict['Humidity'] == 'Fail':
            logger.warning('Temperature/Humidity sensor disconnected!')
        else:
            push_to_db(id, 'Temp', dataDict['Temperature'])
            push_to_db(id, 'Humi', dataDict['Humidity'])
        if dataDict['CO2'] == 'Fail':
            logger.warning('CO2 sensor disconnected!')
        else:
            push_to_db(id, 'CO2', dataDict['CO2'])

        # Initialize communication with GRBL
        ser1.write(b'\r\n\r\n')
        time.sleep(2)   # Wait for grbl to initialize
        ser1.flushInput() # Flush startup text in serial input

        # Initialize camera
        startCAM = OpenCamera()
        startCAM.set_resolution(w, h)
        grblMSG = ''
        grblMSG = grbl_command(gcode, 'check') #

        while grblMSG != 'MPos:1.600': # MPos is position of X server motor
            grblMSG = grbl_command('?', 'run')

            # Picture shoot
            startCAM.take_pic()
            
            # Push picture data to DB
            storage.child("pics/{0}".format(startCAM.picNAME)).put('/home/pi/mycotronics/pictures/' + startCAM.picNAME)
            link = 'http://storage.googleapis.com/stanford-boxes.appspot.com/{0}/{1}'.format('pics', startCAM.picNAME)
            picURL = {"timestamp": {".sv": "timestamp"}, "original": link}
            db.child("data/{0}/{1}.json?print=silent".format(id, 'Camera')).push(picURL)

        # Close camera
        startCAM.close()
        # Delete pictures
        filelist = [ f for f in os.listdir(picsDir) if f.endswith(".jpg") ]
        for f in filelist:
            os.remove(os.path.join(picsDir, f))
        # Rotate motor back and go to sleep mode
        ser1.write(b'G1 X0 F50\n')
        time.sleep(delayTime)
