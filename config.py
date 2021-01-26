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
'''
programTypes = ['exp01 (1 vial, all setpoints)',
                'exp01a (1 vial, 1 setpoint)',
                'exp01b (1 vial, random spts 0-100)',
                'exp01c (const spt, 2 vials back and forth)',
                'exp01d (const spt, random vials)',
                'exp02 (2 vials, random spts: total=x)',
                'exp03 (reproduce)',
                'exp04 (4 vials, random spts)']
'''
programTypes = ['exp01 (1 vial, all setpoints)',
                'exp01a (1 vial, 1 setpoint)',
                'exp01b (1 vial, random spts 0-100)',
                'exp02 (2 vials, random spts: total=100)',
                'exp04 (4 vials, all setpoints, open sequentially)',
                'exp04a (4 vials, 1 setpoint, open randomly)',
                'exp04b (4 vials, random spts, open randomly)',]
defVlval = 5
sensorTypes = ["Honeywell 3100V", "Honeywell 3300V", "Honeywell 5101V"]



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