# ST 2020
# config.py

from datetime import datetime
import logging


currentDate = str(datetime.date(datetime.now()))
logFileName = 'logFile.txt'


# LOGGING
fileHandlerLogLevel = logging.INFO
consoleHandlerLogLevel = logging.DEBUG


# mainGUI.py
################################
users = ['Shannon','Ophir','Other']
datafileLbl = 'exp01'
dataFileType = ".csv"
delimChar = ','


# channel_stuff.py
################################
instTypes = ['olfactometer','flow sensor','NI-DAQ']
noPortMsg = ' ~ No COM ports detected ~'


# Olfactometer
################################
olfFileLbl = "olfadata"
arduinoMasterConfigFile = 'config_master.h'
arduinoSlaveConfigFile = 'config_slave.h'
testingModes = ['auto','manual']
charsToRead = 16
programTypes = ['exp01a (1 vial, repeat setpoint)',
                'exp01b (1 vial, random setpoints 0-100)',
                'exp02 (2 vials, random setpoints: total flow=100)',
                'exp03 (reproduce)']
defVlval = 5
sensorTypes = ["Honeywell 3100V", "Honeywell 3300V", "Honeywell 5101V"]
keysToGet = ['defKp','defKi','defKd','defSp']


# Sensor Things
defSlaveASensors = {
    1: 'Honeywell 3100V',
    2: 'Honeywell 3100V',
    3: 'Honeywell 3100V',
    4: 'Honeywell 3100V'
}
defSlaveBSensors = {
    1: 'Honeywell 3100V',
    2: 'Honeywell 3100V',
    3: 'Honeywell 3100V',
    4: 'Honeywell 3100V'
}
defSensors = [defSlaveASensors, defSlaveBSensors]