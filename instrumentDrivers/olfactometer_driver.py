# ST 2020
# olfactometer_driver.py

import csv, os, time, pandas, numpy, random
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QTextEdit, QWidget, QSpinBox,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout)
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from serial.tools import list_ports
from instrumentDrivers import slave
import config, utils

olfFileLbl = config.olfFileLbl
dataFileType = config.dataFileType
delimChar = config.delimChar

currentDate = utils.currentDate
charsToRead = config.charsToRead
noPortMsg = config.noPortMsg
arduinoMasterConfigFile = config.arduinoMasterConfigFile
arduinoSlaveConfigFile = config.arduinoSlaveConfigFile
defSensors = config.defSensors
programTypes = config.programTypes
testingModes = config.testingModes

keysToGet = config.keysToGet

setpointVals = [10,20,30,40,50]
textEditWidth = 135
col2Width = 250

# for getting calibration tables 
filename = 'calibration_values.xlsx'
rowsb4header = 2
sccmRow = 0
ardRow = 2

# for exp01b
defDurOn = 5
defDurOff = 5
defNumRuns = 5

defManualCmd = 'A1_OV_5'
waitBtSpAndOV = 1

class worker(QObject):
    finished = pyqtSignal()
    w_sendNewParam = pyqtSignal(str,int,str,str)
    w_sendSetpoint = pyqtSignal()
    w_sendRandSetpoint = pyqtSignal()
    w_send2Setpoints = pyqtSignal()
    w_sendOVnow = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.dur_ON = 0
        self.dur_OFF = 0
        self.numRuns = 0
        self.threadON = False
    
    
    @pyqtSlot()
    def exp01a(self):
        for i in range(self.numRuns):
            if self.threadON == True:
                self.w_sendSetpoint.emit()
                time.sleep(waitBtSpAndOV)
                self.w_sendOVnow.emit()
                time.sleep(self.dur_ON)
                time.sleep(self.dur_OFF-waitBtSpAndOV)
            else:
                break
        self.finished.emit()
        self.threadON = False

    
    @pyqtSlot()
    def exp01b(self):
        for i in range(self.numRuns):
            if self.threadON == True:
                self.w_sendRandSetpoint.emit()
                time.sleep(waitBtSpAndOV)
                self.w_sendOVnow.emit()
                time.sleep(self.dur_ON)
                time.sleep(self.dur_OFF-waitBtSpAndOV)
            else:
                break
        self.finished.emit()
        self.threadON = False

    @pyqtSlot()
    def exp02(self):
        for i in range(self.numRuns):
            if self.threadON == True:
                self.w_send2Setpoints.emit()
                time.sleep(waitBtSpAndOV)
                self.w_sendOVnow.emit()
                time.sleep(self.dur_ON)
                time.sleep(self.dur_OFF-waitBtSpAndOV)
            else:
                break
        self.finished.emit()
        self.threadON = False


    @pyqtSlot()
    def exp03(self):
        for i in range(self.numRuns):
            self.sendRandSetpoint.emit()
            time.sleep(waitBtSpAndOV)
            if self.threadOn == True:
                self.sendOVnow.emit()
                time.sleep(self.dur_ON)
                time.sleep(self.dur_OFF)


class olfactometer(QGroupBox):

    def __init__(self, name, port=""):
        super().__init__()
        self.name = name
        self.port = port

        self.record = False
        
        self.className = type(self).__name__
        loggerName = self.className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)
        self.logger.debug('Creating %s', loggerName)

        self.getSlaveInfo()
        self.setUpThreads()
        
        # COLUMN 1
        self.createConnectBox()
        #self.connectBox.setFixedWidth(325)
        
        # COLUMN 2
        self.column2Layout = QVBoxLayout()
        self.createMasterBox()
        self.createFlowSettingsBox()
        self.createVialProgrammingBox()
        self.createDataFileBox()
        self.column2Layout.addWidget(self.masterBox)
        #self.column2Layout.addWidget(self.flowSettingsBox)
        self.column2Layout.addWidget(self.vialProgrammingBox)
        #self.column2Layout.addWidget(self.dataFileBox)
        #self.masterBox.setFixedWidth(col2Width)
        #self.vialProgrammingBox.setFixedWidth(col2Width)
        #self.dataFileBox.setFixedWidth(col2Width)
        
        # COLUMN 3
        self.createSlaveGroupBox()

        self.mainLayout = QHBoxLayout()
        self.mainLayout.addWidget(self.connectBox)
        self.mainLayout.addLayout(self.column2Layout)
        self.mainLayout.addWidget(self.slaveGroupBox)
        self.setLayout(self.mainLayout)
        self.setTitle(self.name)

        self.connectButton.setChecked(False)
        self.refreshButton.setEnabled(True)
        self.portWidget.setEnabled(True)
        self.masterBox.setEnabled(False)
        self.programStartButton.setEnabled(False)
        self.slaveGroupBox.setEnabled(False)
        self.dataFileBox.setEnabled(False)
    
    def getSlaveInfo(self):
        curDir = os.getcwd()
        olfaConfigDir = utils.findOlfaConfigFolder()
        self.logger.debug('getting config files from %s', olfaConfigDir)
        os.chdir(olfaConfigDir)

        # VARIABLES FROM MASTER CONFIG FILE
        self.ardConfig_m = utils.getArduinoConfigFile(arduinoMasterConfigFile)
        self.baudrate = int(self.ardConfig_m.get('baudrate'))
        self.numSlaves = int(self.ardConfig_m.get('numSlaves'))
        self.slaveNames = self.ardConfig_m.get('slaveNames[numSlaves]')
        self.vPSlave = self.ardConfig_m.get('vialsPerSlave[numSlaves]')
        self.defTimebt = self.ardConfig_m.get('timeBetweenRequests')
        
        # VARIABLES FROM SLAVE CONFIG FILE
        self.keysToGet = config.keysToGet
        self.ardConfig_s = utils.getArduinoConfigFile(arduinoSlaveConfigFile)
        for key in keysToGet:
            keyStr = 'self.' + key
            if key in self.ardConfig_s.keys():
                exec(keyStr + '=self.ardConfig_s.get(key)')
            else:
                exec(keyStr + '="0.000"')
        
        # CALIBRATION TABLES        
        self.sccm2Ard_dicts = {}
        self.ard2Sccm_dicts = {}
        x = pandas.ExcelFile(filename)
        self.cal_sheets = x.sheet_names
        for s in self.cal_sheets:
            sccm2Ard = {}
            ard2Sccm = {}
            data = x.parse(sheet_name=s, header=rowsb4header)
            numVals= len(data.values)
            for i in range(numVals):
                flowVal = data.iloc[i,sccmRow]
                ardVal = data.iloc[i,ardRow]
                if numpy.isnan(ardVal) == False:
                    if numpy.isnan(flowVal) == False:
                        sccm2Ard[flowVal] = ardVal
                        ard2Sccm[ardVal] = flowVal
            self.sccm2Ard_dicts[s] = sccm2Ard
            self.ard2Sccm_dicts[s] = ard2Sccm
        os.chdir(curDir)
    
    
    # CONNECT TO DEVICE
    def createConnectBox(self):
        self.connectBox = QGroupBox("Connect")

        self.portLbl = QLabel(text="Port/Device:")
        self.portWidget = QComboBox(currentIndexChanged=self.portChanged)
        self.connectButton = QPushButton(checkable=True,toggled=self.toggled_connect)
        self.refreshButton = QPushButton(text="Refresh",clicked=self.getPorts)
        self.getPorts()

        readLbl = QLabel(text="raw data from serial port:")
        self.rawReadDisplay = QTextEdit(readOnly=True)
        self.rawReadSpace = QWidget()
        readLayout = QVBoxLayout()
        readLayout.addWidget(readLbl)
        readLayout.addWidget(self.rawReadDisplay)
        self.rawReadSpace.setLayout(readLayout)

        writeLbl = QLabel(text="wrote to serial port:")
        self.rawWriteDisplay = QTextEdit(readOnly=True)
        self.rawWriteSpace = QWidget()
        writeLayout = QVBoxLayout()
        writeLayout.addWidget(writeLbl)
        writeLayout.addWidget(self.rawWriteDisplay)
        self.rawWriteSpace.setLayout(writeLayout)
        
        self.connectBoxLayout = QFormLayout()
        self.connectBoxLayout.addRow(self.portLbl,self.portWidget)
        self.connectBoxLayout.addRow(self.refreshButton,self.connectButton)
        self.connectBoxLayout.addRow(self.rawReadSpace,self.rawWriteSpace)
        self.connectBox.setLayout(self.connectBoxLayout)

    def getPorts(self):
        self.portWidget.clear()
        ports = list_ports.comports()
        if ports:
            for ser in ports:
                port_device = ser[0]
                port_description = ser[1]
                if port_device in port_description:
                    idx1 = port_description.find(port_device)
                    port_description = port_description[:idx1-2]
                ser_str = ('{}: {}').format(port_device,port_description)
                self.portWidget.addItem(ser_str)
        else:
            self.portWidget.addItem(noPortMsg)
    
    def portChanged(self):
        if self.portWidget.count() != 0:
            self.port = self.portWidget.currentText()
            if self.port == noPortMsg:
                self.connectButton.setEnabled(False)
                self.connectButton.setText(noPortMsg)
            else:
                self.portStr = self.port[:self.port.index(':')]
                self.connectButton.setEnabled(True)
                self.connectButton.setText("Connect to  " + self.portStr)
    
    def toggled_connect(self, checked):
        if checked:
            i = self.port.index(':')
            self.comPort = self.port[:i]
            self.serial = QtSerialPort.QSerialPort(self.comPort,baudRate=self.baudrate,readyRead=self.receive)
            self.logger.debug('Created serial object at %s',self.comPort)
            if not self.serial.isOpen():
                if self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.logger.info('Connected to %s',self.comPort)
                    self.setConnected(True)
                else:
                    self.logger.warning('could not open port at %s', self.comPort)
                    self.setConnected(False)
            else:
                self.setConnected(True)
        else:
            try:
                self.serial.close()
                self.logger.info('Closed serial port at %s',self.comPort)
                self.setConnected(False)
            except AttributeError:
                self.logger.debug('Cannot close port; serial object does not exist')
    
    def setConnected(self, connected):
        if connected == True:
            self.connectButton.setText('Stop communication w/ ' + self.portStr)
            self.refreshButton.setEnabled(False)
            self.portWidget.setEnabled(False)
            self.masterBox.setEnabled(True)
            self.programStartButton.setEnabled(True)
            self.slaveGroupBox.setEnabled(True)
            self.dataFileBox.setEnabled(True)
        else:
            self.connectButton.setText('Connect to ' + self.portStr)
            self.connectButton.setChecked(False)
            self.refreshButton.setEnabled(True)
            self.portWidget.setEnabled(True)
            self.masterBox.setEnabled(False)
            self.programStartButton.setEnabled(False)
            self.slaveGroupBox.setEnabled(False)
            self.dataFileBox.setEnabled(False)


    # OLFACTOMETER-SPECIFIC FUNCTIONS
    def setUpThreads(self):
        self.obj = worker()
        self.thread1 = QThread()
        self.obj.moveToThread(self.thread1)
        self.obj.w_sendNewParam.connect(self.sendParameter)
        self.obj.w_sendSetpoint.connect(self.sendSetpoint)
        self.obj.w_sendRandSetpoint.connect(self.sendRandomSetpoint)
        self.obj.w_send2Setpoints.connect(self.send2Setpoints)
        self.obj.w_sendOVnow.connect(self.sendOpenValve)
        self.obj.finished.connect(self.threadIsFinished)
    
    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        timeBtReqLbl = QLabel(text="Time b/t requests for slave data (ms):")
        timeBtReqBox = QLineEdit(text=self.defTimebt,returnPressed=lambda:self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        
        manualCmdLbl = QLabel(text="Send manual command:")
        self.manualCmdBox = QLineEdit(text=defManualCmd,returnPressed=self.sendManualParameter)
        manualCmdBtn = QPushButton(text="Send",clicked=self.sendManualParameter)

        layout = QFormLayout()
        layout.addRow(timeBtReqLbl)
        layout.addRow(timeBtReqBox,timeBtButton)
        layout.addRow(manualCmdLbl)
        layout.addRow(self.manualCmdBox,manualCmdBtn)
        self.masterBox.setLayout(layout)        

    def createFlowSettingsBox(self):
        self.flowSettingsBox = QGroupBox("Flow Control Mode")

        modeLabel = QLabel("Flow control:")
        self.modeCb = QComboBox()
        self.modeCb.addItems(testingModes)
        self.modeUpdate = QPushButton(text="Update",clicked=self.updateMode)

        layout = QHBoxLayout()
        layout.addWidget(modeLabel)
        layout.addWidget(self.modeCb)
        layout.addWidget(self.modeUpdate)

        self.flowSettingsBox.setLayout(layout)

    def createVialProgrammingBox(self):
        self.vialProgrammingBox = QGroupBox("Vial Programming")

        programLbl = QLabel("Program:")
        self.programSelectCb = QComboBox()
        self.programSelectCb.addItems(programTypes)
        self.programSelectCb.currentTextChanged.connect(self.changeProgramSelected)
        self.programStartButton = QPushButton(text="Start",checkable=True,clicked=self.programStartClicked,toolTip="must be in auto mode to start a program")
        self.programStartButton.setEnabled(False)
        
        self.progSettingsBox = QWidget()
        self.progSettingsLayout = QFormLayout()
        self.p_vial1_sbox = QComboBox()
        self.p_vial1_sbox.addItems(['A1','A2','B1','B2'])
        self.p_vial2_sbox = QComboBox()
        self.p_vial2_sbox.addItems(['A1','A2','B1','B2'])
        self.p_spt_edit = QSpinBox(value=50)
        self.p_durON_sbox = QSpinBox(value=defDurOn)
        self.p_durOFF_sbox = QSpinBox(value=defDurOff)
        self.p_numTimes_sbox = QSpinBox(value=defNumRuns)
        self.progSettingsLayout.addRow(QLabel("Vial 1:"),self.p_vial1_sbox)
        self.progSettingsLayout.addRow(QLabel("Vial 2:"),self.p_vial2_sbox)
        self.progSettingsLayout.addRow(QLabel("Setpoint:"),self.p_spt_edit)
        self.progSettingsLayout.addRow(QLabel("Dur. open (s)"),self.p_durON_sbox)
        self.progSettingsLayout.addRow(QLabel("Dur.closed (s)"),self.p_durOFF_sbox)
        self.progSettingsLayout.addRow(QLabel("# of runs"),self.p_numTimes_sbox)
        self.progSettingsBox.setLayout(self.progSettingsLayout)
        self.progSelected = self.programSelectCb.currentText()
        self.changeProgramSelected()

        layout = QFormLayout()
        layout.addRow(programLbl,self.programSelectCb)
        layout.addRow(self.progSettingsBox)
        layout.addRow(self.programStartButton)
        self.vialProgrammingBox.setLayout(layout)
    
    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("Olfactometer Data File (" + dataFileType + ")")
        
        files = os.listdir()
        dataFiles = [s for s in files if olfFileLbl in s]
        if not dataFiles:
            self.lastExpNum = 0
        else:
            lastFile = dataFiles[len(dataFiles)-1]
            i_fExt = lastFile.rfind('.')
            lastFile = lastFile[:i_fExt]
            i_us = lastFile.rfind('_')
            self.lastExpNum = int(lastFile[i_us+1:])
        
        defFileName = utils.makeNewFileName(olfFileLbl, self.lastExpNum)
        self.enterFileName = QLineEdit(text=defFileName)
        
        self.recordButton = QPushButton(text="Create && Start Recording",checkable=True,toggled=self.toggled_record)
        hint = self.recordButton.sizeHint()
        self.recordButton.setFixedSize(hint)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)
        '''
        if self.connectButton.isChecked():
            self.recordButton.setEnabled(True)
            self.endRecordButton.setEnabled(True)
        else:
            self.recordButton.setEnabled(False)
            self.endRecordButton.setEnabled(False)
        '''
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
    
    def createSlaveGroupBox(self):
        self.slaveGroupBox = QGroupBox("Slave Settings")
        
        self.slaves = []
        for i in range(self.numSlaves):
            s_slaveName = self.slaveNames[i]
            s_vPSlave = int(self.vPSlave[i])
            s_sensor = defSensors[i]
            s_slave = slave.Slave(self,s_slaveName,s_vPSlave,s_sensor)
            self.slaves.append(s_slave)
        
        allSlaves_layout = QVBoxLayout()
        for s in self.slaves:
            s.resize(s.sizeHint())
            allSlaves_layout.addWidget(s)
        
        self.allSlavesWid = QWidget()
        self.allSlavesWid.setLayout(allSlaves_layout)

        self.slaveScrollArea = QScrollArea()
        self.slaveScrollArea.setWidget(self.allSlavesWid)

        self.slaveBox_layout = QHBoxLayout()
        self.slaveBox_layout.addWidget(self.slaveScrollArea)
        self.slaveGroupBox.setLayout(self.slaveBox_layout)

    def sendManualParameter(self):
        toSend = self.manualCmdBox.text()
        str_send = toSend
        bArr_send = str_send.encode()

        try:
            if self.serial.isOpen():
                self.serial.write(bArr_send)
                self.logger.info("sent to %s: %s", self.port, str_send)
                self.rawWriteDisplay.append(str_send)
                self.window().receiveDataFromChannels(self.name,'',str_send)
            else:
                self.logger.warning('Serial port not open, cannot send parameter: %s', str_send)
        except AttributeError as err:
            self.logger.warning('Serial port not open, cannot send parameter: %s', str_send)


    # INTERFACE FUNCTIONS
    def changeProgramSelected(self):
        newProgSelected = self.programSelectCb.currentText()
        if self.progSelected != newProgSelected:
            self.progSelected = newProgSelected

            if self.progSelected == programTypes[0]:    # exp01a
                self.p_vial2_sbox.setEnabled(False)
                self.p_spt_edit.setEnabled(True)
                
            if self.progSelected == programTypes[1]:    # exp01b
                self.p_vial2_sbox.setEnabled(False)
                self.p_spt_edit.setEnabled(False)

            if self.progSelected == programTypes[2]:    # exp02
                self.p_vial2_sbox.setEnabled(True)
                self.p_spt_edit.setEnabled(True)
            
            if self.progSelected == programTypes[3]:    # exp03
                self.p_vial2_sbox.setEnabled(False)
                self.p_spt_edit.setEnabled(True)
    
    
    def programStartClicked(self, checked):
        if checked:
            if self.window().recordButton.isChecked() == False:
                self.logger.debug('main window record button is not checked, checking')
                self.window().recordButton.setChecked(True)
                self.window().clicked_record()
            else:
                self.logger.debug('main window record button is already checked')
            self.programStartButton.setText('Stop')
            program2run = self.programSelectCb.currentText()
            
            self.vialToRun1 = self.p_vial1_sbox.currentText() # get everything from the GUI
            self.vialToRun2 = self.p_vial2_sbox.currentText()
            self.constSpt = self.p_spt_edit.value()
            self.dur_ON = self.p_durON_sbox.value()
            self.dur_OFF = self.p_durOFF_sbox.value()
            self.numRuns = self.p_numTimes_sbox.value()
            
            self.p_slave1 = self.vialToRun1[0]
            self.p_vial1 = int(self.vialToRun1[1])
            self.p_slave2 = self.vialToRun2[0]
            self.p_vial2 = int(self.vialToRun2[1])
            
            self.obj.dur_ON = self.dur_ON   # give worker all the values
            self.obj.dur_OFF = self.dur_OFF
            self.obj.numRuns = self.numRuns

            for i in range(self.numSlaves):
                if self.slaves[i].slaveName == self.p_slave1: s_index1 = i
            v_index1 = int(self.p_vial1)-1
            sensDictName1 = self.slaves[s_index1].vials[v_index1].sensDict
            self.dictToUse1 = self.sccm2Ard_dicts.get(sensDictName1)
            for i in range(self.numSlaves):
                if self.slaves[i].slaveName == self.p_slave2: s_index2 = i
            v_index2 = int(self.p_vial1)-1
            sensDictName2 = self.slaves[s_index2].vials[v_index2].sensDict
            self.dictToUse2 = self.sccm2Ard_dicts.get(sensDictName2)

            if program2run == programTypes[0]:  # exp01a
                self.slotToConnectTo = self.obj.exp01a

            if program2run == programTypes[1]:  # exp01b
                self.slotToConnectTo = self.obj.exp01b

            if program2run == programTypes[2]:  # exp02
                self.slotToConnectTo = self.obj.exp02
            
            if program2run == programTypes[2]:  # exp03
                self.slotToConnectTo = self.obj.exp03
            
            self.thread1.started.connect(self.slotToConnectTo)  # connect thread started to worker slot
            #self.obj.finished.connect(self.threadIsFinished)
            self.thread1.start()
            self.obj.threadON = True

            self.logger.info('Starting program: %s',program2run)
            
        else:
            self.window().clicked_endRecord()
            self.threadIsFinished()
    
    
    def toggled_record(self, checked):
        if checked:
            self.record = True
            self.enteredFileName = self.enterFileName.text() + dataFileType
            if not os.path.exists(self.enteredFileName):
                self.logger.info('Creating new olfa datafile: %s',self.enteredFileName)
                File = self.enteredFileName, ' '
                Time = "File Created:", str(currentDate + ' ' + utils.getTimeNow())
                DataHead = "Time","Vial/Line","Item","Value","Ctrl (prop.valve)"
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f, delimiter=delimChar)
                    writer.writerow(File)
                    writer.writerow("")
                    writer.writerow(Time)
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
        newFileName = utils.makeNewFileName(olfFileLbl, self.lastExpNum)
        
        self.enterFileName.setText(newFileName)
        self.recordButton.setText("Create File && Start Recording")
        self.logFileOutputBox.clear()
    
    def updateMode(self):
        self.mode = self.modeCb.currentText()

        for s in self.slaves:
            for v in s.vials:
                if self.mode == 'auto': 
                    v.changeMode('auto')
                if self.mode == 'manual':
                    v.changeMode('manual')
            s.resize(s.sizeHint())
        self.allSlavesWid.resize(self.allSlavesWid.sizeHint())
        self.slaveScrollArea.resize(self.slaveScrollArea.sizeHint())
        #self.slaveGroupBox.resize(self.slaveGroupBox.sizeHint())
        #self.resize(self.sizeHint())
        #widget_width = self.slaves[0].width()
        #widget_height = self.slaves[0].height() + self.slaves[1].height()

    
    
    # ACTUAL FUNCTIONS THE THING NEEDS
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            if len(text) == charsToRead:
                try:
                    text = text.decode("utf-8")
                    text = text.rstrip('\r\n')
                    self.rawReadDisplay.append(text)
                    vialInfo = text[0:2]        # 'A1'
                    dataValue = text[2:]        # '020502550000'
                    if dataValue.isnumeric():
                        for i in range(self.numSlaves):
                            if self.slaves[i].slaveName == vialInfo[0]: s_index = i
                        v_index = int(vialInfo[1])-1
                        try:
                            self.slaves[s_index].vials[v_index].appendNew(dataValue)
                            recordOn =  self.slaves[s_index].vials[v_index].recBox.isChecked()
                            flowVal = dataValue[0:4]
                            ctrlVal = dataValue[5:8]
                            if self.window().recordButton.isChecked():  # if main window recording is on
                                if recordOn:    # if recording to this vial is on
                                    instrument = self.name + ' ' + str(vialInfo)
                                    unit = 'FL'
                                    value = flowVal
                                    self.window().receiveDataFromChannels(instrument,unit,value)

                            if self.record:     # if recording to olfa file is on
                                if recordOn:
                                    toWrite = utils.writeToFile(vialInfo,'FL',flowVal,ctrlVal)
                                    with open(self.enteredFileName,'a',newline='') as f:
                                        writer = csv.writer(f,delimiter=delimChar)
                                        writer.writerow(toWrite)
                                    self.logFileOutputBox.append(str(toWrite))
                        
                        except IndexError as err:
                            self.logger.error('arduino master config file does not include vial %s', vialInfo)
                except UnicodeDecodeError as err:
                    self.logger.error('Serial read error: %s\t%s',err,text)
            else:
                self.logger.debug('warning - text from Arduino was %s bytes: %s', len(text), text)
    
    def sendParameter(self, slave: str, vial:int, parameter: str, value=""):
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
            if self.serial.isOpen():
                self.serial.write(bArr_send)
                self.logger.info("sent to %s: %s", self.port, str_send)
                self.rawWriteDisplay.append(str_send)
                for s in self.slaves:
                    if s.slaveName == slave:
                        for v in s.vials:
                            if v.vialNum == vial:
                                recordThisVial = v.recBox.isChecked()   # if this vial record is on, send to mainGUI
                                if v.recBox.isChecked():
                                    instrument = self.name + ' ' + str(slave) + str(vial)
                                    unit = parameter
                                    value = value
                                    self.window().receiveDataFromChannels(instrument,unit,value)
            else:
                self.logger.warning('Serial port not open, cannot send parameter: %s', str_send)
        except AttributeError as err:
            self.logger.warning('Serial port not open, cannot send parameter: %s', str_send)

    
    def sendSetpoint(self):
        sccmVal = self.constSpt
        ardVal = utils.convertToInt(float(sccmVal),self.dictToUse1)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal))
    
    def sendRandomSetpoint(self):
        sccmVal = random.randint(1,100)
        ardVal = utils.convertToInt(float(sccmVal),self.dictToUse1)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal))
    
    def sendOpenValve(self):
        dur = self.dur_ON
        self.sendParameter(self.p_slave1,self.p_vial1,'OV',str(dur))

    def send2Setpoints(self):
        sccmVal1 = random.randint(1,100)
        sccmVal2 = 100 - sccmVal1
        ardVal1 = utils.convertToInt(float(sccmVal1),self.dictToUse1)
        ardVal2 = utils.convertToInt(float(sccmVal2),self.dictToUse2)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal1))
        self.sendParameter(self.p_slave2,self.p_vial2,'Sp',str(ardVal2))
        self.sendOpenValve()
        self.sendOpenValve()

    
    def threadIsFinished(self):
        self.obj.threadON = False
        self.thread1.quit()
        self.programStartButton.setChecked(False)
        self.programStartButton.setText('Start')
        self.logger.info('Finished program, quit thread')
        #self.thread1.started.disconnect(self.slotToConnectTo)

    
    def updatePort(self, newPort):
        self.port = newPort
        self.logger.info('port changed to %s', self.port)
    
    def updateName(self, newName):
        if not self.name == newName:
            self.name = newName
            self.logger.info('name changed to %s', self.name)
            self.setTitle(self.name)
    
