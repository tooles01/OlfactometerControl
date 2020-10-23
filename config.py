# ST 2020
# config.py

from datetime import datetime

currentDate = str(datetime.date(datetime.now()))

logFileName = 'logFile.txt'
noPortMsg = ' ~ No COM ports detected ~'



arduinoMasterConfigFile = 'config_master.h'

# mainGUI.py
users = ['Shannon','Ophir','Other']


# channel_stuff.py
defnumChannels = 3
instTypes = ['olfactometer','oscilloscope','flow sensor','NI-DAQ']


noPortMsg = ' ~ No COM ports detected ~'

##### Olfactometer
defConfig = 'C:\\Users\\shann\\Dropbox\\OlfactometerEngineeringGroup\\Control\\software\\OlfactometerControl'
testingModes = ['auto','manual']
charsToRead = 16
programTypes = ['A1 50cc-5s (10x)','A1 testing','A1 & A2 testing ']


defSpval = 100
defVlval = 5

fileLbl = "olfadata"
#defFileLbl = "datafile"
defFileType = ".csv"
delimChar = ','

# Sensor Things
slaveASensors = {
    1: 'Honeywell 3100V',
    2: 'Honeywell 3100V',
    3: 'Honeywell 3100V',
    4: 'Honeywell 3100V'
}
slaveBSensors = {
    1: 'Honeywell 3100V',
    2: 'Honeywell 3100V',
    3: 'Honeywell 3100V',
    4: 'Honeywell 3100V'
}
sensors = [slaveASensors, slaveBSensors]
sensorTypes = ["Honeywell 3100V", "Honeywell 3300V", "Honeywell 5101V"]
# Flow Sensor Dictionaries
Honeywell3100_SCCMToArd = {
    200: 1024,
    175: 983,
    150: 922,
    125: 854,
    100: 768,
    75: 670,
    50: 547,
    20: 389,
    15: 332,
    10: 295,
    5: 257,
    0: 204
}
Honeywell3100_ArdToSCCM = {
    1024: 200,
    983: 175,
    922: 150,
    854: 125,
    768: 100,
    670: 75,
    547: 50,
    389: 20,
    332: 15,
    295: 10,
    257: 5,
    204: 0
}
Honeywell3300_SCCMToArd = {
    1000: 1024,
    900: 1004,
    800: 983,
    700: 954,
    600: 905,
    500: 856,
    400: 782,
    300: 698,
    200: 606,
    100: 471,
    0: 205
}
Honeywell3300_ArdToSCCM = {
    1024: 1000,
    1004: 900,
    983: 800,
    954: 700,
    905: 600,
    856: 500,
    782: 400,
    698: 300,
    606: 200,
    471: 100,
    205: 0
}
Honeywell5101_SCCMtoArd = {
    1000: 1024,
    4000: 850,
    3000: 686,
    2000: 532,
    1000: 369,
    0: 205
}
Honeywell5101_ArdToSCCM = {
    1024: 1000,
    850: 4000,
    686: 3000,
    532: 2000,
    395: 1100,
    379: 1000,
    365: 900,
    240: 0
}

sccmToArd = {
    'Honeywell 3100V': Honeywell3100_SCCMToArd,
    'Honeywell 3300V': Honeywell3300_SCCMToArd,
    'Honeywell 5101V': Honeywell5101_SCCMtoArd
}
ardToSCCM = {
    'Honeywell 3100V': Honeywell3100_ArdToSCCM,
    'Honeywell 3300V': Honeywell3300_ArdToSCCM,
    'Honeywell 5101V': Honeywell5101_ArdToSCCM
}


'''
Honeywell3300_SCCMToArd = {
    1000: 1024,
    900: 4
    800: 4.80,
    700: 4.66,
    600: 4.42,
    500: 4.18,
    400: 3.82,
    300: 3.41,
    200: 2.96,
    100: 2.30,
    0: 0
}
'''