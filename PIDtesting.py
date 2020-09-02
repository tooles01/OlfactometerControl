# ST 2020
# PIDtesting.py

import serial, time, sys, csv, os
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import (QWidget, QGroupBox, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QLabel, QFormLayout,
                            QRadioButton, QSpinBox, QScrollArea, QApplication, QComboBox, QCheckBox, QPushButton)
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import sip, threading, logging
from datetime import datetime
from serial.tools import list_ports
import utils, config, slave, vial

'''
    #dict_3100V = utils.getCalibrationDict('calibration_values.xlsx','Honeywell 3100V',1,[0,2])

    #flow2Ard = {}
    #ard2Flow = {}
    #for s in config.sensorTypes:
    #    print(s)
    #    Fl, Ar = utils.getCalibrationDict('calibration_values.xlsx',s,1,[0,2])

    #dict_3300V = utils.getCalibrationDict('calibration_values.xlsx','Honeywell 3300V',2,[0,2])
'''
currentDate = utils.currentDate
charsToRead = config.charsToRead
programTypes = ['2 vial testing ']

vials = [1,2]
setpointVals = [10,20,30,40,50]

class worker(QObject):
    finished = pyqtSignal()
    setpointReady = pyqtSignal(str,int,str,str)
    
    @pyqtSlot()
    def setpointFunction(self): # a slot takes no params
        for A1 in setpointVals:
            self.setpointReady.emit('A',1,'Sp',str(A1))
            for A2 in setpointVals:
                self.setpointReady.emit('A',2,'Sp',str(A2))
                time.sleep(1)
        self.finished.emit()
    
    '''
    @pyqtSlot()
    def setpointFunction(self):
        for i in range(1,10):
            time.sleep(5)
            self.setpointReady.emit(i)
        self.finished.emit()
    '''


class GUIMain(QWidget):
    defFilePrefix = config.defFileLbl
    defFileType = config.defFileType
    delimChar = config.delimChar
    defUser = 'Shannon'

    def __init__(self, configDir, todayDir, numSlaves, slaveNames, slaveVials):
        super().__init__()
        self.configDir = configDir
        self.todayDir = todayDir
        self.numSlaves = numSlaves
        self.slaveNames = slaveNames
        self.vPSlave = slaveVials
        self.user = self.defUser

        self.setWindowTitle("GUIMain")
        self.record = False
        
        # Create logger
        self.logger = utils.createCustomLogger(__name__)
        self.logger.debug('Created logger for %s', __name__)
        self.logger.debug('Current directory: %s', os.getcwd())
        
        # Get config.master things
        os.chdir(self.configDir)
        self.ardConfig = utils.getArduinoConfigFile('config_master.h')
        os.chdir(self.todayDir)
        
        self.setUpThreads()
        
        # COLUMN 1
        column1Layout = QVBoxLayout()
        self.createMainSettingsBox()
        self.createArduinoConnectBox()
        self.createMasterBox()
        self.createProgramSelectBox()
        column1Layout.addWidget(self.MainSettingsBox)
        column1Layout.addWidget(self.arduinoConnectBox)
        column1Layout.addWidget(self.masterBox)
        column1Layout.addWidget(self.programSelectBox)

        # COLUMN 2
        column2Layout = QVBoxLayout()
        self.createSlaveBox()
        column2Layout.addWidget(self.slaveBox)
        ''' scroll bar for when there's lots of slaves
                scroll = QScrollArea()
                scroll.setWidget(slaveBox)
                column2Layout.addWidget(scroll)
        '''

        # COLUMN 3
        column3Layout = QVBoxLayout()
        self.createDataFileBox()
        column3Layout.addWidget(self.dataFileBox)
        
        mainLayout = QHBoxLayout()
        mainLayout.addLayout(column1Layout)
        mainLayout.addLayout(column2Layout)
        mainLayout.addLayout(column3Layout)
        self.setLayout(mainLayout)

    
    def setUpThreads(self):
        self.obj = worker()
        self.thread1 = QThread()
        self.obj.setpointReady.connect(self.sendParameter)
        self.obj.moveToThread(self.thread1)
        self.obj.finished.connect(self.thread1.quit)
        self.thread1.started.connect(self.obj.setpointFunction)
    
    # FUNCTIONS TO CREATE GUI
    def createMainSettingsBox(self):
        self.MainSettingsBox = QGroupBox("Main Settings")
        
        locationLayout = QHBoxLayout()

        userLayout = QHBoxLayout()
        userSelectCb = QComboBox()
        userSelectCb.addItems(config.users)
        userChangeBtn = QPushButton(text="Update", clicked=lambda: self.userUpdate(userSelectCb.currentText()))
        userLayout.addWidget(QLabel("User:"))
        userLayout.addWidget(userSelectCb)
        userLayout.addWidget(userChangeBtn)

        slaveEditBtn = QPushButton(text="Edit # Slaves / # Vials",clicked=self.editSlaveStuff)
        
        layout = QVBoxLayout()
        layout.addLayout(userLayout)
        layout.addWidget(slaveEditBtn)
        self.MainSettingsBox.setLayout(layout)

    def createArduinoConnectBox(self):
        self.arduinoConnectBox = QGroupBox("Connect to master Arduino:")

        self.COMportSelect = QComboBox()
        self.refreshButton = QPushButton(text="Refresh port list",clicked=self.refreshPorts)
        self.connectButton = QPushButton(text="Connect",checkable=True,toggled=self.toggled_connect)
        self.arduinoReadBox = QTextEdit(readOnly=True)
        
        self.refreshPorts()

        layout = QFormLayout()
        layout.addRow(self.COMportSelect)
        layout.addRow(self.refreshButton,self.connectButton)
        layout.addRow(QLabel("reading from serial port:"))
        layout.addRow(self.arduinoReadBox)
        self.arduinoConnectBox.setLayout(layout)  

    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        defTimebt = self.ardConfig.get('timeBetweenRequests')
        timeBtReqLbl = QLabel(text="Time b/t requests for slave data (ms):")
        timeBtReqBox = QLineEdit(text=defTimebt,returnPressed=lambda:self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        

        timeBtReqBox.setFixedWidth(60)
        timeupdateLayout = QFormLayout()
        timeupdateLayout.addRow(timeBtReqLbl)
        timeupdateLayout.addRow(timeBtReqBox,timeBtButton)
        self.masterBox.setLayout(timeupdateLayout)

    def createProgramSelectBox(self):
        self.programSelectBox = QGroupBox("Select Program to run:")

        self.programSelectCb = QComboBox()
        self.programSelectCb.addItems(programTypes)
        self.programStartButton = QPushButton(text="Start",checkable=True,toggled=self.programButtonClicked)

        layout = QHBoxLayout()
        layout.addWidget(self.programSelectCb)
        layout.addWidget(self.programStartButton)
        self.programSelectBox.setLayout(layout)
    
    ## ideally this will refresh when edit slaves/vials is changed
    def createSlaveBox(self):
        self.slaveBox = QGroupBox("Slave Settings")

        layout = QVBoxLayout()
        self.slaves = []
        lenSensorList = len(config.sensors)
        for i in range(self.numSlaves):
            # deal w/ error checking later
            '''
            if not self.slaveNames[i]: slaveName = 'x'
            else: slaveName = self.slaveNames[i]
            if not self.vPSlave[i]: vPSlave = 2
            else: vPSlave = int(self.vPSlave[i])
            if not config.sensors[i]: sensor = config.sensors[0]
            else: sensor = config.sensors[i]
            '''
            slaveName = self.slaveNames[i]
            vPSlave = int(self.vPSlave[i])
            sensor = config.sensors[i]

            s_slave = slave.Slave(self,slaveName,vPSlave,sensor)
            #if i < lenSensorList:
            #    s_slave = slave.Slave(self,self.slaveNames[i],int(self.vPSlave[i]),config.sensors[i])
            #else:
            #    s_slave = slave.Slave(self,int(self.vPSlave[i]),config.sensors[0])
            self.slaves.append(s_slave)
        
        # keeping these separate as a reminder about slave objects
        for s in self.slaves:
            layout.addWidget(s)
        
        self.slaveBox.setLayout(layout)
    
    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("Data File (" + self.defFileType + ")")
        
        files = os.listdir()
        dataFiles = [s for s in files if self.defFilePrefix in s]
        
        if not dataFiles:
            self.lastExpNum = 0
        else:
            lastFile = dataFiles[len(dataFiles)-1]
            i_fExt = lastFile.rfind('.')
            lastFile = lastFile[:i_fExt]
            i_us = lastFile.rfind('_')
            self.lastExpNum = int(lastFile[i_us+1:])
        defFileName = utils.makeNewFileName(self.lastExpNum)

        self.logDirLabel = QLineEdit(text=self.todayDir,readOnly=True)
        self.enterFileName = QLineEdit(text=defFileName)

        self.cbA1 = QCheckBox(text='A1',checkable=True,checked=True)
        self.cbA2 = QCheckBox(text='A2',checkable=True,checked=True)
        self.cbB1 = QCheckBox(text='B1',checkable=True,checked=True)
        self.cbB2 = QCheckBox(text='B2',checkable=True,checked=True)
        cbLayout = QHBoxLayout()
        cbLayout.addWidget(self.cbA1); cbLayout.addWidget(self.cbA2)
        cbLayout.addWidget(self.cbB1); cbLayout.addWidget(self.cbB2)
        
        self.recordButton = QPushButton(text="Create File && Start Recording",checkable=True,toggled=self.toggled_record)
        hint = self.recordButton.sizeHint()
        self.recordButton.setFixedSize(hint)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)

        self.logFileOutputBox = QTextEdit(readOnly=True)
        
        layout = QFormLayout()
        layout.addRow(QLabel("Directory:"),self.logDirLabel)
        layout.addRow(QLabel("File Name:"),self.enterFileName)
        #layout.addRow(QLabel("Lines to Record:"),cbLayout)
        layout.addRow(self.recordButton,self.endRecordButton)
        layout.addRow(self.logFileOutputBox)

        self.dataFileBox.setLayout(layout)
    

    # ACTUAL FUNCTIONS THE THING NEEDS
    def refreshPorts(self):
        self.logger.info('Refreshing COM port list')

        self.COMportSelect.clear()
        ports = list_ports.comports()
        if ports:
            self.connectButton.setEnabled(True)
            for ser in ports:
                port_device = ser[0]
                port_description = ser[1]
                ser_str = ('{}: {}').format(port_device,port_description)
                self.COMportSelect.addItem(ser_str)
        else:
            self.logger.debug('\t~No COM ports detected~')
            self.COMportSelect.addItem('~~ No COM ports detected ~~')
            self.connectButton.setEnabled(False)
    
    def toggled_connect(self, checked):
        if checked:
            port_str = self.COMportSelect.currentText()
            i = port_str.index(':')
            comPort = port_str[:i]
            baudrate = int(self.ardConfig.get('baudrate'))
            self.serial = QtSerialPort.QSerialPort(comPort,baudRate=baudrate,readyRead=self.receive)
            self.logger.info('Created serial object at %s',comPort)
            if not self.serial.isOpen():
                self.serial.open(QtCore.QIODevice.ReadWrite)
                self.logger.debug('Opened serial port & set mode to ReadWrite')
                self.connectButton.setText('Stop comm. w/ ' + comPort)
                if not self.serial.isOpen():
                    self.logger.error('Cannot open serial port :/')
                    self.connectButton.setChecked(False)
        else:
            try:
                self.serial.close()
                self.logger.info('Closed serial port')
                self.connectButton.setText("Connect")
            except AttributeError as err:
                self.logger.debug('Cannot close port, serial object does not exist')
        
        if self.connectButton.isChecked():
            self.refreshButton.setEnabled(False)
        else:
            self.refreshButton.setEnabled(True)
    
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            if len(text) == charsToRead:
                try:
                    text = text.decode("utf-8")
                    text = text.rstrip('\r\n')
                    self.arduinoReadBox.append(text)
                    vialInfo = text[0:2]    # 'A1'
                    value = text[2:]        # '020502550000'
                    if value.isnumeric():
                        for i in range(self.numSlaves):
                            if self.slaves[i].slaveName == vialInfo[0]: s_index = i
                        v_index = int(vialInfo[1])-1
                        try:
                            self.slaves[s_index].vials[v_index].appendNew(value)
                            recordOn =  self.slaves[s_index].vials[v_index].recBox.isChecked()
                            if self.record and recordOn:
                                flowVal = value[0:4]
                                ctrlVal = value[5:8]
                                toWrite = utils.writeToFile(vialInfo,'FL',flowVal,ctrlVal)
                                with open(self.enteredFileName,'a',newline='') as f:
                                    writer = csv.writer(f,delimiter=self.delimChar)
                                    writer.writerow(toWrite)
                                self.logFileOutputBox.append(str(toWrite))
                        except IndexError as err:
                            self.logger.error('current config file does not include %s', vialInfo)
                except UnicodeDecodeError as err:
                    self.logger.error('Serial read error: %s',err)
            else:
                self.logger.debug('error - text from Arduino was %s bytes: %s', len(text), text)

    def toggled_record(self, checked):
        if checked:
            self.record = True            
            self.enteredFileName = self.enterFileName.text() + self.defFileType
            if not os.path.exists(self.enteredFileName):
                self.logger.info('Creating new data file: %s',self.enteredFileName)
                File = self.enteredFileName, ' '
                User = "User:", self.user
                Time = "File Created:", str(currentDate + ' ' + utils.getTimeNow())
                DataHead = "Time","Vial/Line","Item","Value","Ctrl (prop.valve)"
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f, delimiter=self.delimChar)
                    writer.writerow(File)
                    writer.writerow("")
                    writer.writerow(Time)
                    writer.writerow(User)
                    writer.writerow("")
                    writer.writerow(DataHead)
            else:
                self.logger.info('Resuming recording to %s', self.enteredFileName)
            self.recordButton.setText("Pause Recording")

        else:
            self.record = False
            self.recordButton.setText("Resume Recording")
            self.logger.info('Paused recording to %s', self.enteredFileName)
    
    def clicked_endRecord(self,checked):
        self.logger.info('End recording')
        if self.recordButton.isChecked() == True:
            self.recordButton.toggle()
        self.record = False

        self.lastExpNum = self.lastExpNum + 1
        newFileName = utils.makeNewFileName(self.lastExpNum)
        
        self.enterFileName.setText(newFileName)
        self.recordButton.setText("Create File && Start Recording")
    
    def sendParameter(self, slave, vial, parameter, value=""):
        if parameter[0] == 'K' and parameter != 'Kx':
            str_param = 'Kx'
            nextChar = parameter[1].capitalize()
            valToSend = nextChar + value
        else:
            str_param = parameter
            valToSend = value
        str_send = slave + str(vial) + '_' + str_param + '_' + valToSend
        bArr_send = str_send.encode()
        try:
            self.serial.write(bArr_send)
            self.logger.info("sent to master: %s", str_send)
            if self.record == True:
                toWrite = utils.getTimeNow(),slave+str(vial),parameter,valToSend
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=self.delimChar)
                    writer.writerow(toWrite)
                self.logFileOutputBox.append(str(toWrite))
        except AttributeError as err:
            self.logger.warning('Serial port not open, cannot send parameter: %s', str_send)

    def programButtonClicked(self, checked):
        if checked:
            self.programStartButton.setText('Stop')
            program2run = self.programSelectCb.currentText()
            if program2run == programTypes[0]:
                self.thread1.start()
                self.logger.info('Starting program: %s', programTypes[0])
                self.logger.info('\ttest setpoints %s for vials A%s and A%s with 1s rest between each change', setpointVals,vials[0],vials[1])
        else:
            self.programStartButton.setText('Start')
            self.thread1.terminate()
            self.logger.info('Stop button pressed: program ended')

    def userUpdate(self, newUser):
        self.user = newUser
        self.logger.info('User: %s', newUser)
        
    def editSlaveStuff(self):
        self.logger.error('edit slave info: this function is not set up yet')
        #self.logger.debug('edit slave properties was clicked: opening slaveSetupWindow')
        
        # create a window and open it
        '''
        slaveEditWindow = QWidget()
        slaveEditWindow.setWindowTitle("Slave Setup Window")
        
        mainLayout = QVBoxLayout()
        numSlavesBox = QGroupBox("1) Enter Number of Slaves")
        numSlavesSb = QSpinBox(value=self.numSlaves)
        numSlavesBtn = QPushButton(text="Update",clicked=self.updateNumSlaves)
        layout1 = QHBoxLayout()
        layout1.addWidget(numSlavesSb)
        layout1.addWidget(numSlavesBtn)
        numSlavesBox.setLayout(layout1)
        mainLayout.addWidget(numSlavesBox)
        slaveEditWindow.setLayout(mainLayout)

        slaveEditWindow.show()
        '''
        # when done, delete slave groupbox and re-add to main layout
        
        
        #self.slaveEditWindow = slaveSetupWindow(self.configDir,self.todayDir,self.numSlaves,self.slaveNames,self.vPSlave)
        #self.slaveEditWindow.show()
        #if self.slaveEditWindow.isVisible() == False:
        #    print('closed it')
        #self.logger.debug('closing this window')
        #self.close()
    
    '''
    def createModeBox(self):
        self.modeBox = QGroupBox("Mode")

        manualRb = QRadioButton(text="Manual", checked=True, toggled=self.changeMode)
        autoRb = QRadioButton(text="Auto")
        
        modeLayout = QHBoxLayout()
        modeLayout.addWidget(manualRb)
        modeLayout.addWidget(autoRb)

        self.modeBox.setLayout(modeLayout)
    '''
        
    '''
    def run2vialProg(self):
        vials = ['A1','A2']
        A1nums = [10,20]
        A2nums = [10,20,30,40,50]

        self.sendParameter('A',1,'ON')
        self.sendParameter('A',2,'ON')
        
        for i in A1nums:
            self.sendParameter('A',1,'Sp',str(i))
            for m in A2nums:
                self.sendParameter('A',2,'Sp',str(m))
        
        self.sendParameter('A',1,'OF')
        self.sendParameter('A',2,'OF')
    '''
    '''
    def changeMode(self, checked):
        if checked:
            self.logger.debug('manual is checked')
        else:
            self.logger.debug('auto is checked')
    '''
    '''
    def sendMasterParameter(self, slave, parameter, value=""):
        str_send = 'M' + slave + '_' + parameter + '_' + value
        bArr_send = str_send.encode()
        try:
            self.serial.write(bArr_send)
        except AttributeError:
            self.logger('Serial port not open, cannot send: %s', str_send)
        #if parameter == 'debug_':   self.numBytesIwant = 10
        #if parameter == 'normal':   self.numBytesIwant = 6
    '''
    '''
    def updateNumSlaves(self):
        self.logger.debug('Update numslaves')
    '''

'''
class slaveEnterBox(QHBoxLayout):

    def __init__(self, defSlaveName, defNumVials):
        super().__init__()

        self.slaveNameBox = QLineEdit(text=defSlaveName)
        self.numVialsBox = QSpinBox(value=defNumVials)

        self.addWidget(self.slaveNameBox)
        self.addWidget(self.numVialsBox)

class slaveSetupWindow(QWidget):
    
    def __init__(self, configDir, todayDir, numSlaves, slaveNames, slaveVials):
        super().__init__() # so it inherits QWidget type
        self.setWindowTitle("Slave Edit Window")
        self.numSlaves = numSlaves
        self.defSlaveNames = slaveNames
        self.defvPSlave = slaveVials
        self.todayDir = todayDir
        
        # create logger for slaveSetupWindow
        className = type(self).__name__
        self.logger = utils.createCustomLogger(className)
        self.logger.debug('Created logger for %s', className)
        self.logger.debug('Current directory: %s', os.getcwd())
        self.logger.warning('this will only change the user interface, not the actual slave properties. (to change this for the whole system you need to edit config files and reupload the slave codes)')

        # Number of Slaves
        numSlavesBox = QGroupBox("1) Enter Number of Slaves")
        self.box = QSpinBox(value=self.numSlaves)
        layout = QHBoxLayout()
        layout.addWidget(self.box)
        layout.addWidget(QPushButton(text="Update",clicked=self.updateNumSlaves))
        numSlavesBox.setLayout(layout)
        
        # Slave Properties
        self.makeSlaveEnterBoxes(self.numSlaves,self.defSlaveNames,self.defvPSlave)
        
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(numSlavesBox)
        self.mainLayout.addWidget(self.slaveEnterSpace)
        self.setLayout(self.mainLayout)
    
    def makeSlaveEnterBoxes(self, numSlaves, slaveNames, vpSlave):
        self.slaveEnterSpace = QGroupBox("2) Enter Properties of Each Slave")
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Name"))
        layout.addWidget(QLabel("# of Vials"))

        self.slaveEnterLayout = QVBoxLayout()
        self.slaveEnterLayout.addLayout(layout)
        
        self.slaveEnterObjs = [None]*numSlaves
        for i in range(numSlaves):
            numDefaultShit = len(slaveNames)
            if i < numDefaultShit:
                s_slaveEnter = slaveEnterBox(slaveNames[i],int(vpSlave[i]))
            else: s_slaveEnter = slaveEnterBox('','')
            self.slaveEnterObjs[i] = s_slaveEnter
            self.slaveEnterLayout.addLayout(s_slaveEnter)
        self.doneButton = QPushButton(text="Click when done",clicked=self.allDone)
        self.slaveEnterLayout.addWidget(self.doneButton)

        self.slaveEnterSpace.setLayout(self.slaveEnterLayout)
    
    def updateNumSlaves(self):
        self.numSlaves = self.box.value()
        self.logger.debug('updating # of slaves: %s', self.numSlaves)

        self.mainLayout.removeWidget(self.slaveEnterSpace)
        sip.delete(self.slaveEnterSpace)
        self.makeSlaveEnterBoxes(self.numSlaves,self.defSlaveNames,self.defvPSlave)
        self.mainLayout.addWidget(self.slaveEnterSpace)

    def allDone(self):
        slaveNames = [None]*self.numSlaves
        slaveVials = [None]*self.numSlaves
        self.logger.debug('done editing slave details:')
        
        for i in range(self.numSlaves):
            slaveNames[i] = self.slaveEnterObjs[i].slaveNameBox.text()
            slaveVials[i] = self.slaveEnterObjs[i].numVialsBox.value()
            self.logger.debug('slave %s, %s vial(s)', slaveNames[i],slaveVials[i])
        self.logger.debug('reopening GUIMain')
        self.mainWindow = GUIMain(os.getcwd(),self.todayDir,self.numSlaves,slaveNames,slaveVials)
        self.mainWindow.show()
        self.logger.debug('closing this window')
        self.close()
'''