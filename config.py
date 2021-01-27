# ST 2020
# config.py

from datetime import datetime
import logging


currentDate = str(datetime.date(datetime.now()))
logFileName = 'logFile.txt'


# LOGGING
fileHandlerLogLevel = logging.INFO
consoleHandlerLogLevel = logging.DEBUG


# run.py
################################
#delimChar = ','
noPortMsg = ' ~ No COM ports detected ~'



# Olfactometer
################################

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