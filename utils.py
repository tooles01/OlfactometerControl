# ST 2020
# utils for main GUI

import os, pandas, logging
from datetime import datetime
import config

import glob

currentDate = config.currentDate

def createCustomLogger(name):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # or else nothing is set?
    
    # create formatters
    file_formatter = logging.Formatter('%(asctime)s.%(msecs)03d : %(name)-10s :%(levelname)-8s: %(message)s',datefmt='%H:%M:%S')
    console_formatter = logging.Formatter('%(name)-12s: %(levelname)-8s: %(message)s')

    # create file handler
    file_handler = logging.FileHandler('logFile.txt',mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)

    # add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def findLogFiles():
    # find dropbox folder
    try:
        x = os.path.expanduser('~\\Dropbox')
        os.chdir(os.path.expanduser(x))
    except FileNotFoundError:
        x = os.path.expanduser('~\\Dropbox (NYU Langone Health)')
        os.chdir(os.path.expanduser(x))
    # find OlfactometerEngineeringGroup folder
    oeg = glob.glob(x + '/**/*OlfactometerEngineeringGroup',recursive=True)
    o = oeg[0]
    # find logfiles folder
    f = glob.glob(o + '/**/*logfiles',recursive=True)
    if len(f) > 1: print("error: somehow more than 1 logfiles folder within OlfactometerEngineeringGroup")
    else: logFileLocation = f[0]

    return logFileLocation

'''
def setUpLogger(name, logFormat, log_file_name):
    formatter = logging.Formatter(logFormat)
    handler = logging.FileHandler(log_file_name,mode='a')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    return logger

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(name)s %(levelname)-8s %(message)s',
                                    datefmt='%H:%M:%S')
    handler = logging.FileHandler('log.txt',mode='a')
    handler.setFormatter(formatter)
    #file_handler = logging.StreamHandler()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger
'''
def getInCorrectDirectory():
    # we need this for the arduino config files
    path00 = '~\\Dropbox'
    path01 = '\\OlfactometerEngineeringGroup\\Control\\software\\github repo'
    PATH = path00 + path01
    x = os.path.expanduser(PATH)
    os.chdir(x)

def makeNewFileName(lastExpNum):
    newExpNum = lastExpNum + 1
    newExpNum = str(newExpNum).zfill(2)
    newFileName = currentDate + '_' + config.defFileLbl + '_' + str(newExpNum)
    return newFileName


def getArduinoConfigFile(fileName):
    newDict = {}
    try:
        with open(fileName,'r') as f:
            for line in f:
                if line[0:2] != '//' and '=' in line:
                    i_eq = line.find('=')

                    str1 = line[:i_eq]
                    x1 = str1.split()
                    key = x1[-1]
                    
                    str2 = line[i_eq+1:]
                    i_sc = str2.find(';')
                    val = str2[:i_sc]
                    val = val.lstrip()
                    val = val.replace('\'','')
                    val = val.replace('\"','')
                    if '{' in val:  # if it's a list, convert it to one
                        inString = val[1:len(val)-1]    # remove {}
                        newList = inString.split(',')   # split at commas
                        val = [p.strip() for p in newList]  # remove shitespace
                    newDict[key] = val

    except OSError or FileNotFoundError as err:
        print("could not read file:", err)
    
    return newDict

def convertToSCCM(ardVal, sensor):

    dictionary = config.ardToSCCM.get(sensor)
    if ardVal in dictionary:    val_SCCM = dictionary.get(ardVal)
    else:
        minVal = min(dictionary)
        maxVal = max(dictionary)
        if ardVal < minVal:     val_SCCM = dictionary.get(minVal)
        elif ardVal > maxVal:   val_SCCM = dictionary.get(maxVal)
        else:
            val1 = ardVal-1
            flow1 = dictionary.get(val1)
            while flow1 is None:
                val1 = val1-1
                flow1 = dictionary.get(val1)
            val2 = ardVal+1
            flow2 = dictionary.get(val2)
            while flow2 is None:
                val2 = val2+1
                flow2 = dictionary.get(val2)
            
            slope = (flow2-flow1)/(val2-val1)
            x1 = ardVal - val1
            addNum = x1*slope
            val_SCCM = flow1 + addNum
            val_SCCM = round(val_SCCM,1)

    return val_SCCM

def convertToInt(SCCMval, sensor):

    dictionary = config.sccmToArd.get(sensor)
    if SCCMval in dictionary:   ardVal = dictionary.get(SCCMval)
    else:
        minVal = min(dictionary)
        maxVal = max(dictionary)
        if SCCMval < minVal:    ardVal = dictionary.get(minVal)
        elif SCCMval > maxVal:  ardVal = dictionary.get(maxVal)
        else:
            val1 = SCCMval-1
            flow1 = dictionary.get(val1)
            while flow1 is None:
                val1 = val1-1
                flow1 = dictionary.get(val1)
            val2 = SCCMval+1
            flow2 = dictionary.get(val2)
            while flow2 is None:
                val2 = val2+1
                flow2 = dictionary.get(val2)

            slope = (flow2-flow1)/(val2-val1)
            x1 = SCCMval - val1
            addNum = x1*slope
            ardVal = flow1 + addNum
            ardVal = round(ardVal)

    return ardVal


def getCalibrationDict(fileName,sheet,rowsb4Header,columns):
    sccm2Ard = {}
    ard2Sccm = {}
    try:
        f = open(fileName,'rb')
        xls = pandas.read_excel(fileName,
                            sheet_name=sheet,
                            header=rowsb4Header-1,
                            usecols = columns)
        numVals = int(xls.size/2)
        for n in range(numVals):
            flowVal = xls.iloc[n,0]
            ardVal = xls.iloc[n,1]
            sccm2Ard[flowVal] = ardVal
            ard2Sccm[ardVal] = flowVal
    
    except OSError as err:
        print("cant find the file :/", err)
    
    return sccm2Ard, ard2Sccm

def getTimeNow():
    timeNow = datetime.time(datetime.now())         # type: 'datetime.time'
    timeNow_f = timeNow.strftime('%H:%M:%S.%f')     # type: 'str'
    timeNow_str = timeNow_f[:-3]                    # type: 'str' (get rid of last 3 ms)

    return timeNow_str


def writeToFile(vial, param, flow, ctrl):
    timeNow = getTimeNow()
    strToWrite = timeNow,vial,param,flow,ctrl
    
    return strToWrite

'''
def convToList(numVals, listToConv):
    inString = listToConv[1:len(listToConv)-1]
    result = [x.strip() for x in inString.split(',')]
    for x in range(numVals):
        result[x] = result[x].replace('\'','')
    return result
'''

