# ST 2020
# utils for main GUI

import os, pandas
import config

currentDate = config.currentDate

def getInCorrectDirectory():
    path00 = '~\\Dropbox'
    path01 = '\\OlfactometerEngineeringGroup\\Control\\software\\github repo'
    PATH = path00 + path01
    x = os.path.expanduser(PATH)
    os.chdir(x)

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



'''
def convToList(numVals, listToConv):
    inString = listToConv[1:len(listToConv)-1]
    result = [x.strip() for x in inString.split(',')]
    for x in range(numVals):
        result[x] = result[x].replace('\'','')
    return result
'''

