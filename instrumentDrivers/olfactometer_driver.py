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

currentDate = utils.currentDate

olfFileLbl = config.olfFileLbl
dataFileType = config.dataFileType
delimChar = config.delimChar

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
col1Width = 325
col2Width = 250

# for getting calibration tables 
filename = 'calibration_values.xlsx'
rowsb4header = 2
sccmRow = 0
ardRow = 2

# for exp01b
defDurOn = 2
defDurOff = 2
defNumRuns = 2

defManualCmd = 'A1_OV_5'
waitBtSpAndOV = .5
waitBtSps = 1

class worker(QObject):
    finished = pyqtSignal()
    w_sendThisSp = pyqtSignal(str,int,int)
    w_send_OpenValve = pyqtSignal(str,int)
    
    def __init__(self):
        super().__init__()
        self.slave1 = 'A';  self.vial1 = 1
        self.slave2 = 'A';  self.vial2 = 2
        self.slave3 = 'B';  self.vial3 = 1
        self.slave4 = 'B';  self.vial4 = 2
        self.setpoint = 0

        self.dur_ON = 0
        self.dur_OFF = 0
        self.numRuns = 0
        self.threadON = False
    
    @pyqtSlot()
    def exp01(self):
        maxsp = 100
        incr = 10
        sccmVal = 10
        for j in range(int((maxsp-sccmVal)/incr)):
            for i in range(self.numRuns):
                if self.threadON == True:
                    self.w_sendThisSp.emit(self.slave1,self.vial1,sccmVal)
                    time.sleep(waitBtSpAndOV)
                    self.w_send_OpenValve.emit(self.slave1,self.vial1)
                    time.sleep(self.dur_ON)
                    time.sleep(self.dur_OFF-waitBtSpAndOV)
                else:
                    break
            sccmVal=sccmVal+incr
        self.finished.emit()
        self.threadON = False

    @pyqtSlot()
    def exp01a(self):
        self.w_sendThisSp.emit(self.slave1,self.vial1,self.setpoint)
        time.sleep(waitBtSpAndOV)
        for i in range(self.numRuns):
            if self.threadON == True:
                self.w_send_OpenValve.emit(self.slave1,self.vial1)
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
                sccmVal = random.randint(1,100)
                self.w_sendThisSp.emit(self.slave1,self.vial1,sccmVal)
                time.sleep(waitBtSpAndOV)
                self.w_send_OpenValve.emit(self.slave1,self.vial1)
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
                sccmVal1 = random.randint(1,10)
                sccmVal2 = 10 - sccmVal1
                self.w_sendThisSp.emit(self.slave1,self.vial1,sccmVal1);     time.sleep(waitBtSps)
                self.w_sendThisSp.emit(self.slave2,self.vial2,sccmVal2);     time.sleep(waitBtSpAndOV)
                self.w_send_OpenValve.emit(self.slave1,self.vial1);         time.sleep(waitBtSpAndOV)
                self.w_send_OpenValve.emit(self.slave2,self.vial2);         time.sleep(self.dur_ON - waitBtSpAndOV) # now the ON time is over
                time.sleep(self.dur_OFF-waitBtSps-waitBtSpAndOV)
            else:
                break
        self.finished.emit()
        self.threadON = False


    @pyqtSlot()
    def exp04(self):
        maxsp = 200
        incr = 10
        sccmVal = 10
        for j in range(int((maxsp-sccmVal)/incr)):
            for i in range(self.numRuns):
                if self.threadON == True:
                    self.w_sendThisSp.emit(self.slave1,self.vial1,sccmVal); time.sleep(waitBtSpAndOV);  self.w_send_OpenValve.emit(self.slave1,self.vial1); time.sleep(self.dur_ON + self.dur_OFF)
                    self.w_sendThisSp.emit(self.slave2,self.vial2,sccmVal); time.sleep(waitBtSpAndOV);  self.w_send_OpenValve.emit(self.slave2,self.vial2); time.sleep(self.dur_ON + self.dur_OFF)
                    self.w_sendThisSp.emit(self.slave3,self.vial3,sccmVal); time.sleep(waitBtSpAndOV);  self.w_send_OpenValve.emit(self.slave3,self.vial3); time.sleep(self.dur_ON + self.dur_OFF)
                    self.w_sendThisSp.emit(self.slave4,self.vial4,sccmVal); time.sleep(waitBtSpAndOV);  self.w_send_OpenValve.emit(self.slave4,self.vial4); time.sleep(self.dur_ON + self.dur_OFF)
                else:
                    break
            sccmVal=sccmVal+incr
        self.finished.emit()
        self.threadON = False
    
    @pyqtSlot()
    def exp04a(self):
        self.w_sendThisSp.emit(self.slave1,self.vial1,self.setpoint);   time.sleep(.1)
        self.w_sendThisSp.emit(self.slave2,self.vial2,self.setpoint);   time.sleep(.1)
        self.w_sendThisSp.emit(self.slave3,self.vial3,self.setpoint);   time.sleep(.1)
        self.w_sendThisSp.emit(self.slave4,self.vial4,self.setpoint);   time.sleep(.1)
        time.sleep(waitBtSpAndOV)
        for i in range(self.numRuns):
            if self.threadON == True:
                thisSlave = random.randint(1,2)
                if thisSlave == 1: slave = 'A'
                if thisSlave == 2: slave = 'B'
                thisVial = random.randint(1,2)
                self.w_send_OpenValve.emit(slave,thisVial)
                time.sleep(self.dur_ON + self.dur_OFF)
            else:
                break
        self.finished.emit()
        self.threadON = False

    @pyqtSlot()
    def exp04b(self):
        for i in range(self.numRuns):
            if self.threadON == True:
                sccmVal = random.randint(1,100)
                thisSlave = random.randint(1,2)
                if thisSlave == 1: slave = 'A'
                if thisSlave == 2: slave = 'B'
                thisVial = random.randint(1,2)
                self.w_sendThisSp.emit(slave,thisVial,sccmVal); time.sleep(waitBtSpAndOV)
                self.w_send_OpenValve.emit(slave,thisVial);     time.sleep(self.dur_ON + self.dur_OFF)
            else:
                break
        self.finished.emit()
        self.threadON = False
    

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
        size = self.connectBox.sizeHint()
        cboxWidth = size.width()
        #boxWidth = size.width()/2 - 20
        #self.rawReadSpace.setFixedWidth(boxWidth)
        #self.rawWriteSpace.setFixedWidth(boxWidth)

        #self.rawReadSpace.setFixedWidth(size.width()/2)
        #size = self.rawReadSpace.sizeHint()
        #self.rawReadSpace.setFixedSize(size)
        #self.rawWriteSpace.setFixedSize(size)
        #self.rawReadSpace.size(self.rawReadSpace.sizeHint())
        #self.rawWriteSpace.size(self.rawReadSpace.sizeHint())
        self.connectBox.setFixedWidth(col1Width)
        
        # COLUMN 2
        self.column2Layout = QVBoxLayout()
        self.createMasterBox()
        self.createFlowSettingsBox()
        self.createVialProgrammingBox()
        self.column2Layout.addWidget(self.masterBox)
        #self.column2Layout.addWidget(self.flowSettingsBox)
        self.column2Layout.addWidget(self.vialProgrammingBox)
        
        self.masterBox.setFixedWidth(col2Width)
        self.vialProgrammingBox.setFixedWidth(col2Width)
        
        
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
            self.logger.debug('Creating serial object at %s',self.comPort)
            self.serial = QtSerialPort.QSerialPort(self.comPort,baudRate=self.baudrate,readyRead=self.receive)
            if not self.serial.isOpen():
                if self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.logger.info('Connected to %s',self.comPort)
                    self.setConnected(True)
                else:
                    self.logger.warning('could not open port at %s', self.comPort)
                    self.setConnected(False)
            else:
                self.logger.info('serial port already open')
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
        else:
            self.connectButton.setText('Connect to ' + self.portStr)
            self.connectButton.setChecked(False)
            self.refreshButton.setEnabled(True)
            self.portWidget.setEnabled(True)
            self.masterBox.setEnabled(False)
            self.programStartButton.setEnabled(False)
            self.slaveGroupBox.setEnabled(False)


    # OLFACTOMETER-SPECIFIC FUNCTIONS
    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        timeBtReqLbl = QLabel(text="Time b/t requests for slave data (ms):")
        timeBtReqBox = QLineEdit(text=self.defTimebt,returnPressed=lambda:self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        
        manualCmdLbl = QLabel(text="Manually send command:")
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
        self.slaveScrollArea.setWidgetResizable(True)

        self.slaveBox_layout = QHBoxLayout()
        self.slaveBox_layout.addWidget(self.slaveScrollArea)
        self.slaveGroupBox.setLayout(self.slaveBox_layout)


    
    # VIAL PROGRAMMING
    def setUpThreads(self):
        #self.logger.debug('create self.obj')
        self.obj = worker()

        #self.logger.debug('create self.thread1')
        self.thread1 = QThread()
        
        #self.logger.debug('move obj to thread')
        self.obj.moveToThread(self.thread1)
        
        #self.obj.w_sendNewParam.connect(self.sendParameter)
        self.obj.w_sendThisSp.connect(self.sendThisSetpoint)
        self.obj.w_send_OpenValve.connect(self.send_OpenValve)
        self.obj.finished.connect(self.threadIsFinished)
    
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
        self.p_vial1_sbox.setCurrentIndex(0)
        self.p_vial2_sbox = QComboBox()
        self.p_vial2_sbox.addItems(['A1','A2','B1','B2'])
        self.p_vial2_sbox.setCurrentIndex(1)
        self.p_spt_edit = QSpinBox(value=50,maximum=200)
        self.p_durON_sbox = QSpinBox(value=defDurOn)
        self.p_durOFF_sbox = QSpinBox(value=defDurOff)
        self.p_numTimes_sbox = QSpinBox(value=defNumRuns,maximum=500)
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
    
        
    def changeProgramSelected(self):
        newProgSelected = self.programSelectCb.currentText()
        self.progSelected = newProgSelected

        if self.progSelected == programTypes[0]:    # exp01
            self.p_vial1_sbox.setEnabled(True)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(False)
        if self.progSelected == programTypes[1]:    # exp01a
            self.p_vial1_sbox.setEnabled(True)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(True)
        if self.progSelected == programTypes[2]:    # exp01b
            self.p_vial1_sbox.setEnabled(True)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(False)
        
        if self.progSelected == programTypes[3]:    # exp02
            self.p_vial1_sbox.setEnabled(True)
            self.p_vial2_sbox.setEnabled(True)
            self.p_spt_edit.setEnabled(False)
        
        if self.progSelected == programTypes[4]:    # exp04
            self.p_vial1_sbox.setEnabled(False)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(False)
        if self.progSelected == programTypes[5]:    # exp04a
            self.p_vial1_sbox.setEnabled(False)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(True)
        if self.progSelected == programTypes[6]:    # exp04b
            self.p_vial1_sbox.setEnabled(False)
            self.p_vial2_sbox.setEnabled(False)
            self.p_spt_edit.setEnabled(False)


    def programStartClicked(self, checked):
        if checked:
            if self.window().recordButton.isChecked() == False:
                self.logger.warning('not recording to file')
            self.programStartButton.setText('Stop')
            self.progSettingsBox.setEnabled(False)
            self.program2run = self.programSelectCb.currentText()
            
            self.vialToRun1 = self.p_vial1_sbox.currentText() # get everything from the GUI
            self.vialToRun2 = self.p_vial2_sbox.currentText()
            self.constSpt = self.p_spt_edit.value()
            self.dur_ON = self.p_durON_sbox.value()
            
            self.obj.dur_ON = self.dur_ON   # give worker all the values
            self.obj.dur_OFF = self.p_durOFF_sbox.value()
            self.obj.numRuns = self.p_numTimes_sbox.value()
            self.obj.setpoint = self.constSpt


            if self.program2run == programTypes[0] or self.program2run == programTypes[1] or self.program2run == programTypes[2]:
                self.obj.slave1 = self.vialToRun1[0]
                self.obj.vial1 = int(self.vialToRun1[1])
            elif self.program2run == programTypes[3]:
                self.obj.slave1 = self.vialToRun1[0]
                self.obj.vial1 = int(self.vialToRun1[1])
                self.obj.slave2 = self.vialToRun2[0]
                self.obj.vial2 = int(self.vialToRun2[1])
            else:
                self.obj.slave1 = 'A'
                self.obj.vial1 = 1
                self.obj.slave2 = 'A'
                self.obj.vial2 = 2

            if self.program2run == programTypes[0]:     self.thread1.started.connect(self.obj.exp01)    # connect thread started to worker slot
            if self.program2run == programTypes[1]:     self.thread1.started.connect(self.obj.exp01a)   # 01a
            if self.program2run == programTypes[2]:     self.thread1.started.connect(self.obj.exp01b)   # 01b
            
            if self.program2run == programTypes[3]:     self.thread1.started.connect(self.obj.exp02)    # 02
            
            if self.program2run == programTypes[4]:     self.thread1.started.connect(self.obj.exp04)    # 04
            if self.program2run == programTypes[5]:     self.thread1.started.connect(self.obj.exp04a)   # 04a
            if self.program2run == programTypes[6]:     self.thread1.started.connect(self.obj.exp04b)   # 04b
            
            self.thread1.start()
            self.obj.threadON = True
            self.logger.info('Starting program: %s',self.program2run)
            
        else:
            self.progSettingsBox.setEnabled(True)
            self.logger.info('program stopped early by user')
            self.threadIsFinished()
    
    
    def sendThisSetpoint(self, slave:str, vial:int, sccmVal:int):
        # find dictionary to use
        for i in range(self.numSlaves):
            if self.slaves[i].slaveName == slave: s_index = i
        v_index = vial - 1
        sensDictName = self.slaves[s_index].vials[v_index].sensDict
        dictToUse = self.sccm2Ard_dicts.get(sensDictName)
        
        # convert to integer and send
        ardVal = utils.convertToInt(float(sccmVal),dictToUse)
        self.sendParameter(slave,vial,'Sp',str(ardVal))

    def send_OpenValve(self, slave:str, vial:int):
        dur = self.dur_ON
        self.sendParameter(slave,vial,'OV',str(dur))

    def threadIsFinished(self):
        self.obj.threadON = False
        self.thread1.quit()
        self.thread1.terminate()
        self.programStartButton.setChecked(False)
        self.programStartButton.setText('Start')
        self.progSettingsBox.setEnabled(True)
        self.logger.info('Finished program, quit thread')
        self.setUpThreads()

    


    '''
    def sendSetpoint_vial1(self):
        sccmVal = self.constSpt
        ardVal = utils.convertToInt(float(sccmVal),self.dictToUse1)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal))
    
    def sendRandomSetpoint_vial1(self):
        sccmVal = random.randint(1,100)
        ardVal = utils.convertToInt(float(sccmVal),self.dictToUse1)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal))
    
    def sendRandomSetpoint1(self):
        sccmVal1 = random.randint(1,10)
        sccmVal2 = 10 - sccmVal1
        ardVal1 = utils.convertToInt(float(sccmVal1*10),self.dictToUse1)
        self.ardVal2 = utils.convertToInt(float(sccmVal2*10),self.dictToUse2)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal1))
        
    def sendRandomSetpoint2(self):
        self.sendParameter(self.p_slave2,self.p_vial2,'Sp',str(self.ardVal2))
    
    def sendOpenValve_random(self):
        valve = random.randint(1,4)
        if valve == 1:  slave = 'A'; vial=1
        if valve == 2:  slave = 'A'; vial=2
        if valve == 3:  slave = 'B'; vial=1
        if valve == 4:  slave = 'B'; vial=2
        self.sendParameter(slave,vial,'OV',str(self.dur_ON))
    
    def sendSetpoint_random(self):
        sccmVal1 = random.randint(1,100)
        self.this_slave_idx = random.randint(1,2) - 1
        self.this_vial_idx = random.randint(1,2) - 1
        self.this_vial = self.this_vial_idx + 1
        if self.this_slave_idx == 0:    self.this_slave = 'A'
        if self.this_slave_idx == 1:    self.this_slave = 'B'
        self.dictToUse1 = self.sccm2Ard_dicts.get(self.slaves[self.this_slave_idx].vials[self.this_vial_idx].sensDict)
        ardVal1 = utils.convertToInt(float(sccmVal1),self.dictToUse1)
        self.sendParameter(self.this_slave,self.this_vial,'Sp',str(ardVal1))
    
    def send2Setpoints(self):
        sccmVal1 = random.randint(1,10)
        sccmVal2 = 10 - sccmVal1
        ardVal1 = utils.convertToInt(float(sccmVal1*10),self.dictToUse1)
        ardVal2 = utils.convertToInt(float(sccmVal2*10),self.dictToUse2)
        self.sendParameter(self.p_slave1,self.p_vial1,'Sp',str(ardVal1))
        self.sendParameter(self.p_slave2,self.p_vial2,'Sp',str(ardVal2))
    '''

    # INTERFACE FUNCTIONS
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

    
    
    def updatePort(self, newPort):
        self.port = newPort
        self.logger.info('port changed to %s', self.port)
    
    def updateName(self, newName):
        if not self.name == newName:
            self.name = newName
            self.logger.info('name changed to %s', self.name)
            self.setTitle(self.name)
    
