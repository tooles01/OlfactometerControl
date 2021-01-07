# ST 2020
# utils for main GUI

import os, logging, glob, math
from datetime import datetime
import config

currentDate = config.currentDate
logFileName = config.logFileName
fileHandlerLogLevel = config.fileHandlerLogLevel
consoleHandlerLogLevel = config.consoleHandlerLogLevel


def findOlfEngGroup():
    # find Dropbox\OlfactometerEngineeringGroup
    dropboxPath = os.path.expanduser('~\\Dropbox')
    oeg_list = glob.glob(dropboxPath + '/**/*OlfactometerEngineeringGroup*',recursive=True)
    if not oeg_list:
        dropboxPath = os.path.expanduser('~\\Dropbox (NYU Langone Health)')
        oeg_list = glob.glob(dropboxPath + '/**/*OlfactometerEngineeringGroup*',recursive=True)
    oeg = oeg_list[0]

    oegDirectory = oeg

    return oegDirectory

def findLogFolder():
    oeg = findOlfEngGroup()

    logfiles_list = glob.glob(oeg + '/**/*logfiles',recursive=True)
    logFileDirectory = logfiles_list[0]     # assuming there is only 1 logfiles folder there

    return logFileDirectory

def findOlfaConfigFolder():
    oeg = findOlfEngGroup()

    olfControl_list = glob.glob(oeg + '/**/*OlfactometerControl',recursive=True)
    olfaConfigDirectory = olfControl_list[0]
    olfactometerFolder = olfaConfigDirectory + '\olfactometer'

    return olfactometerFolder


def createLogger(name):
    # if today folder doesn't exist, make it
    logDir = findLogFolder()
    today_logDir = logDir + '\\' + currentDate
    if not os.path.exists(today_logDir):
        os.mkdir(today_logDir)

    # if it's coming from my computer
    if 'shann' in logDir:
        logFileName = 'logfile_delete.txt'
    
    # create logger
    os.chdir(today_logDir) # move into directory before creating logger (you can also move just before creating the filehandler, but I'd rather do it here)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # formatters
    file_formatter = logging.Formatter('%(asctime)s.%(msecs)03d : %(name)-14s :%(levelname)-8s: %(message)s',datefmt='%H:%M:%S')
    console_formatter = logging.Formatter('%(name)-14s: %(levelname)-8s: %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(logFileName,mode='a')
    file_handler.setLevel(fileHandlerLogLevel)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(consoleHandlerLogLevel)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # first file entry
    anythingInIt = os.stat(logFileName).st_size
    if anythingInIt == 0:   # if logfile is empty
        logger.info('~~ Log File for %s ~~', currentDate)
        logger.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    
    return logger

def getArduinoConfigFile(fileName):
    '''
    open file
    -> line by line: if it doesn't start with '//' and has an '='
        -> key = last word before '='
        -> val = everything after '=' and before ';'
            -> remove spaces to the left
            -> if it's a list: remove '{}', convert to list by splitting at the commas
        -> add key and val to newDict
    '''
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
                        val_0 = val[1:len(val)-1]           # remove {}
                        newList = val_0.split(',')          # convert to list (split at commas)
                        val = [p.strip() for p in newList]  # remove spaces
                    newDict[key] = val

    except OSError or FileNotFoundError as err:
        print("could not read file:", err)
    
    return newDict



def makeNewFileName(fileType, lastExpNum):
    newExpNum = lastExpNum + 1
    newExpNum = str(newExpNum).zfill(2)
    newFileName = currentDate + '_' + fileType + '_' + str(newExpNum)
    return newFileName


def convertToSCCM(ardVal, dictionary):
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

def convertToInt(SCCMval, dictionary):
    if SCCMval in dictionary:   ardVal = dictionary.get(SCCMval)
    else:
        minVal = min(dictionary)
        maxVal = max(dictionary)
        if SCCMval < minVal:    ardVal = dictionary.get(minVal)
        elif SCCMval > maxVal:  ardVal = dictionary.get(maxVal)
        else:
            if SCCMval.is_integer() == False:
                val1 = math.floor(SCCMval)
            else:
                val1 = SCCMval-1
            flow1 = dictionary.get(val1)
            while flow1 is None:
                val1 = val1-1
                flow1 = dictionary.get(val1)
            if SCCMval.is_integer() == False:
                val2 = math.ceil(SCCMval)
            else:
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
    return int(ardVal)


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