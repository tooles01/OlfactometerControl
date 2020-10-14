# ST 2020
# instrument_drivers.py

import csv, os, time, serial, sip
from datetime import datetime
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QTextEdit,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout)
import slave, vial, config, utils

currentDate = utils.currentDate
charsToRead = config.charsToRead
programTypes = ['A1 testing','A1 & A2 testing ']

vials = [1,2]
setpointVals = [10,20,30,40,50]

flowSens_baud = 9600

defConfig = 'C:\\Users\\shann\\Dropbox\\OlfactometerEngineeringGroup\\Control\\software\\OlfactometerControl'

class olfactometer(QGroupBox):
    defFileType = config.defFileType
    delimChar = config.delimChar

    def __init__(self, name, port):
        super().__init__()
        self.name = name
        self.port = port
        self.configDir = defConfig  # gotta edit
        
        self.record = False
        
        className = type(self).__name__
        loggerName = className + ' (' + self.name + ')'
        self.logger = utils.createCustomLogger(loggerName)
        self.logger.debug('Created logger')
        
        # get default slave information
        curDir = os.getcwd()
        os.chdir(self.configDir)
        self.ardConfig_m = utils.getArduinoConfigFile('config_master.h')
        self.numSlaves = int(self.ardConfig_m.get('numSlaves'))
        self.slaveNames = self.ardConfig_m.get('slaveNames[numSlaves]')
        self.vPSlave = self.ardConfig_m.get('vialsPerSlave[numSlaves]')
        self.defTimebt = self.ardConfig_m.get('timeBetweenRequests')
        os.chdir(curDir)
        
        # COLUMN 1
        self.column1Layout = QVBoxLayout()
        self.createArduinoConnectBox()
        self.column1Layout.addWidget(self.arduinoConnectBox)
        
        # COLUMN 2
        self.column2Layout = QVBoxLayout()
        self.createMasterBox()
        self.createVialProgrammingBox()
        self.createDataFileBox()
        self.column2Layout.addWidget(self.masterBox)
        self.column2Layout.addWidget(self.vialProgrammingBox)
        self.column2Layout.addWidget(self.dataFileBox)
        
        # COLUMN 3
        self.column3Layout = QVBoxLayout()
        self.createSlaveGroupBox()
        self.column3Layout.addWidget(self.slaveGroupBox)

        self.mainLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.column1Layout)
        self.mainLayout.addLayout(self.column2Layout)
        self.mainLayout.addLayout(self.column3Layout)
        self.setLayout(self.mainLayout)

        col3Size = self.slaveGroupBox.size()
        self.arduinoConnectBox.resize(125,col3Size.height())
        col1Size = self.arduinoConnectBox.size()
        col2Size = self.masterBox.size()
        self.mainW = col1Size.width() + col2Size.width() + col3Size.width()
        self.mainH = self.slaveGroupBox.height()
        self.resize(self.mainW,self.mainH)

        self.setTitle(loggerName)
    
    # FUNCTIONS TO CREATE GUI
    def createArduinoConnectBox(self):
        self.arduinoConnectBox = QGroupBox()

        self.connectButton = QPushButton(checkable=True,toggled=self.toggled_connect)
        if not self.port:
            self.connectButton.setEnabled(False)
            self.connectButton.setText("Connect")
        else:
            self.connectButton.setEnabled(True)
            self.connectButton.setText("Connect to " + str(self.port))
        self.arduinoReadBox = QTextEdit(readOnly=True)

        layout = QFormLayout()
        layout.addRow(self.connectButton)
        layout.addRow(QLabel("reading from serial port:"))
        layout.addRow(self.arduinoReadBox)
        self.arduinoConnectBox.setLayout(layout)

    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        timeBtReqLbl = QLabel(text="Time b/t requests for slave data (ms):")
        timeBtReqBox = QLineEdit(text=self.defTimebt,returnPressed=lambda:self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendParameter('M','M','timebt',timeBtReqBox.text()))

        timeBtReqBox.setFixedWidth(60)
        timeupdateLayout = QFormLayout()
        timeupdateLayout.addRow(timeBtReqLbl)
        timeupdateLayout.addRow(timeBtReqBox,timeBtButton)
        self.masterBox.setLayout(timeupdateLayout)

    def createVialProgrammingBox(self):
        self.vialProgrammingBox = QGroupBox("Vial Programming")

        modeLabel = QLabel("Testing mode:")
        self.modeCb = QComboBox()
        self.modeCb.addItems(config.testingModes)
        self.modeUpdate = QPushButton(text="Update",clicked=self.updateMode)
        row1 = QHBoxLayout()
        row1.addWidget(modeLabel)
        row1.addWidget(self.modeCb)
        row1.addWidget(self.modeUpdate)
        
        self.programSelectCb = QComboBox()
        self.programSelectCb.addItems(programTypes)
        self.programStartButton = QPushButton(text="Start",checkable=True,toggled=self.programButtonToggled,toolTip="must be in auto mode to start a program")
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Select program:"))
        row2.addWidget(self.programSelectCb)
        row2.addWidget(self.programStartButton)

        layout = QVBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.vialProgrammingBox.setLayout(layout)
    
    def createSlaveGroupBox(self):
        self.slaveGroupBox = QGroupBox("Slave Settings")
        
        self.slaves = []
        for i in range(self.numSlaves):
            slaveName = self.slaveNames[i]
            vPSlave = int(self.vPSlave[i])
            sensor = config.sensors[i]
            s_slave = slave.Slave(self,slaveName,vPSlave,sensor)
            self.slaves.append(s_slave)
        
        allSlaves_layout = QVBoxLayout()
        for s in self.slaves:
            allSlaves_layout.addWidget(s)
        
        allSlavesGb = QGroupBox()
        allSlavesGb.setLayout(allSlaves_layout)

        self.slaveScrollArea = QScrollArea()
        self.slaveScrollArea.setWidget(allSlavesGb)
        allSlavesGb_size = allSlavesGb.sizeHint()

        self.slaveBox_layout = QHBoxLayout()
        self.slaveBox_layout.addWidget(self.slaveScrollArea)
        self.slaveGroupBox.setLayout(self.slaveBox_layout)
        self.slaveGroupBox.setMinimumWidth(allSlavesGb_size.width()+50)

    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("Data File (" + self.defFileType + ")")
        
        files = os.listdir()
        dataFiles = [s for s in files if config.defFileLbl in s]
        if not dataFiles:
            self.lastExpNum = 0
        else:
            lastFile = dataFiles[len(dataFiles)-1]
            i_fExt = lastFile.rfind('.')
            lastFile = lastFile[:i_fExt]
            i_us = lastFile.rfind('_')
            self.lastExpNum = int(lastFile[i_us+1:])
        
        defFileName = utils.makeNewFileName(self.lastExpNum)
        self.enterFileName = QLineEdit(text=defFileName)
        
        self.recordButton = QPushButton(text="Create && Start Recording",checkable=True,toggled=self.toggled_record)
        hint = self.recordButton.sizeHint()
        self.recordButton.setFixedSize(hint)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)

        self.logFileOutputBox = QTextEdit(readOnly=True)
        
        fileNameLayout = QHBoxLayout()
        fileNameLayout.addWidget(QLabel("File Name:"))
        fileNameLayout.addWidget(self.enterFileName)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.recordButton)
        buttonLayout.addWidget(self.endRecordButton)
        layout = QVBoxLayout()
        layout.addLayout(fileNameLayout)
        layout.addLayout(buttonLayout)
        layout.addWidget(self.logFileOutputBox)

        self.dataFileBox.setLayout(layout)
    
    # ACTUAL FUNCTIONS THE THING NEEDS
    def toggled_connect(self, checked):
        if checked:
            port_str = self.port
            i = port_str.index(':')
            comPort = port_str[:i]
            baudrate = int(self.ardConfig_m.get('baudrate'))
            self.serial = QtSerialPort.QSerialPort(comPort,baudRate=baudrate,readyRead=self.receive)
            self.logger.info('Created serial object at %s',comPort)
            if not self.serial.isOpen():
                x = self.serial.open(QtCore.QIODevice.ReadWrite)
                if x == True:
                    self.logger.info('successfully opened port (& set mode to ReadWrite')
                    self.connectButton.setText('Stop communication w/ ' + comPort)
                else:
                    self.logger.warning('could not successfully open port')
                    self.connectButton.setChecked(False)
        else:
            try:
                if self.serial.isOpen():
                    self.serial.close()
                    self.logger.info('Closed serial port')
                self.connectButton.setText("Connect to " + str(self.port))
            except AttributeError as err:
                self.logger.debug('Cannot close port, serial object does not exist')
    
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
                self.logger.debug('warning - text from Arduino was %s bytes: %s', len(text), text)

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

    def programButtonToggled(self, checked):
        if checked:
            self.programStartButton.setText('Stop')
            program2run = self.programSelectCb.currentText()
            self.logger.info('Starting program: %s',program2run)
            if program2run == programTypes[0]:
                self.slotToConnectTo = self.obj.singleLineSetpointChange
            elif program2run == programTypes[1]:
                self.slotToConnectTo = self.obj.setpointFunction
            
            self.thread1.started.connect(self.slotToConnectTo)  # connect thread started to worker slot
            self.thread1.start()
        else:
            self.logger.info('Program ended')
            self.programStartButton.setText('Start')
    
    def updateMode(self):
        self.mode = self.modeCb.currentText()
        if self.mode == 'auto':
            self.programStartButton.setEnabled(True)
            for s in self.slaves:
                for v in s.vials:
                    v.updateMode('auto')
                s.resize(s.sizeHint())
        else:
            self.programStartButton.setEnabled(False)
            for s in self.slaves:
                for v in s.vials:
                    v.updateMode('manual')
                s.resize(s.sizeHint())
        
        allSlaves_layout = QVBoxLayout()
        for s in self.slaves:
            allSlaves_layout.addWidget(s)
        allSlavesGb = QGroupBox()
        allSlavesGb.setLayout(allSlaves_layout)

        self.slaveScrollArea.takeWidget()
        self.slaveScrollArea.setWidget(allSlavesGb)
        allSlavesGb_size = allSlavesGb.sizeHint()

        self.slaveBox_layout.addWidget(self.slaveScrollArea)
        self.slaveGroupBox.setMinimumWidth(allSlavesGb_size.width()+50)

    def portChanged(self, newPort):
        self.port = newPort
        self.logger.debug('port changed to %s', newPort)
        port_text = str(self.port)
        if port_text == ' ~ No COM ports detected ~':
            self.connectButton.setEnabled(False)
            self.connectButton.setText('Connect')
        else:
            self.connectButton.setEnabled(True)
            self.connectButton.setText('Connect to ' + port_text)


class flowSensor(QGroupBox):
    def __init__(self, name, port):
        super().__init__()
        self.name = name
        self.port = port

        className = type(self).__name__
        loggerName = className + ' (' + self.name + ')'
        self.logger = utils.createCustomLogger(loggerName)
        self.logger.debug('Created logger')

        mainLayout = QHBoxLayout()
        self.createArduinoConnectBox()
        mainLayout.addWidget(self.arduinoConnectBox)
        self.setLayout(mainLayout)
        self.setTitle(loggerName)

    def createArduinoConnectBox(self):
        self.arduinoConnectBox = QGroupBox()
        
        self.connectButton = QPushButton(checkable=True,toggled=self.toggled_connect)
        if not self.port:
            self.connectButton.setEnabled(False)
            self.connectButton.setText("Connect")
        else:
            self.connectButton.setEnabled(True)
            self.connectButton.setText("Connect to " + str(self.port))
        self.arduinoReadBox = QTextEdit(readOnly=True)

        layout = QFormLayout()
        layout.addRow(self.connectButton)
        layout.addRow(QLabel("reading from serial port:"))
        layout.addRow(self.arduinoReadBox)
        self.arduinoConnectBox.setLayout(layout)
    
    def toggled_connect(self, checked):
        if checked:
            port_str = self.port 
            i = self.port.index(':')
            comPort = port_str[:i]
            baudrate = int(flowSens_baud)
            self.serial = QtSerialPort.QSerialPort(comPort,baudRate=baudrate,readyRead=self.receive)
            self.logger.info('Created serial object at %s', comPort)
            if not self.serial.isOpen():
                self.serial.open(QtCore.QIODevice.ReadWrite)
                self.logger.debug('Opened serial port & set mode to ReadWrite')
                self.connectButton.setText('Stop communication w/ ' + comPort)
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


    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            try:
                text = text.decode("utf-8")
                text = text.rstrip('\r\n')
                self.arduinoReadBox.append(text)
            except UnicodeDecodeError as err:
                self.logger.error('Serial read error: %s', err)

    def portChanged(self, newPort):
        self.port = newPort
        self.logger.debug('port changed to %s', newPort)
        port_text = str(self.port)
        if port_text == ' ~ No COM ports detected ~':
            self.connectButton.setEnabled(False)
            self.connectButton.setText('Connect')
        else:
            self.connectButton.setEnabled(True)
            self.connectButton.setText('Connect to ' + port_text)