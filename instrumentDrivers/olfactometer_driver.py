# ST 2020
# olfactometer_driver.py

import csv, os, time, pandas, numpy, random
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from serial.tools import list_ports
import config, utils



### VIAL
defVl = str(config.defVlval)
defMode = 'manual'
lineEditWidth = 45
defSensorCal = 'Honeywell 3100V'
keysToGet = ['defKp','defKi','defKd','defSp']
sensorTypes = ["Honeywell 3100V", "Honeywell 3300V", "Honeywell 5101V"]

### OLFACTOMETER
currentDate = utils.currentDate
charsToRead = 16

noPortMsg = config.noPortMsg
arduinoMasterConfigFile = 'config_master.h'
arduinoSlaveConfigFile = 'config_slave.h'
defSensors = config.defSensors
programTypes = config.programTypes

testingModes = ['auto','manual']

col2Width = 275

# for getting calibration tables 
filename = 'calibration_values.xlsx'
rowsb4header = 2
sccmRow = 0
ardRow = 2

defDurOn = 2
defDurOff = 2
defNumRuns = 5
defSp = 100
maxSp = 200
defVlval = config.defVlval

defManualCmd = 'A1_OV_5'
waitBtSpAndOV = .5
waitBtSps = 1

class Vial(QGroupBox):

    def __init__(self, parent, slave, vialNum, sensorType):
        super().__init__()
        self.parent = parent
        self.slave = slave
        self.vialNum = vialNum
        self.sensType = sensorType      ## ** sensor type doesn't matter - just the dictionary does
        self.mode = defMode

        # get the dictionary u want
        self.sensDict = defSensorCal
        #self.sensDict = self.parent.cal_sheets[0]
        self.program_button = QPushButton(text=slave+str(vialNum),checkable=True)

        className = type(self).__name__
        loggerName = className + ' (' + self.parent.name + ' ' + self.slave + str(self.vialNum) + ')'
        self.logger = utils.createLogger(loggerName)
        self.logger.debug('Creating %s', loggerName)

        self.getDefVals()

        title = "Vial " + slave + str(vialNum) + ": " + self.sensType
        self.setTitle(title)        

        if self.mode == 'auto':
            self.mainLayout = QHBoxLayout()
            self.setLayout(self.mainLayout)

            self.createVialSettingsBox()
            self.createRunSettingsBox()
            self.createDataReceiveBoxes()

            self.mainLayout.addWidget(self.vialSettingsBox)
            self.mainLayout.addWidget(self.runSettingsBox)
            self.mainLayout.addWidget(self.dataReceiveBox)
        
        if self.mode == 'manual':
            self.mainLayout = QHBoxLayout()
            self.setLayout(self.mainLayout)

            self.createVialSettingsBox()
            self.createFlowTuningBox()
            self.createDebugBox()
            self.createRunSettingsBox()
            self.createDataReceiveBoxes()

            self.mainLayout.addWidget(self.vialSettingsBox)
            self.mainLayout.addWidget(self.flowTuningBox)
            self.mainLayout.addWidget(self.debugBox)
            self.mainLayout.addWidget(self.runSettingsBox)
            self.mainLayout.addWidget(self.dataReceiveBox)
    
    def getDefVals(self):
        slaveVars = self.parent.ardConfig_s
        for key in keysToGet:
            keyStr = 'self.' + key
            exec(keyStr + '=slaveVars.get(key)')
    
    # CREATE BOXES
    def createVialSettingsBox(self):
        self.vialSettingsBox = QGroupBox("vial settings")

        self.recBox = QCheckBox(checkable=True,checked=True)

        self.sensTypeBox = QComboBox()
        self.sensTypeBox.addItems(sensorTypes)
        self.sensTypeBox.setCurrentText(self.sensType)
        self.sensTypeBox.setEnabled(False)
        self.sensTypeBtn = QPushButton(text="Edit",checkable=True)
        self.sensTypeBtn.clicked.connect(self.clicked_sensTypeEdit)

        self.sensDictBox = QComboBox()
        self.sensDictBox.addItems(self.parent.cal_sheets)
        self.sensDictBox.setCurrentText(self.sensDict)
        self.sensDictBox.setEnabled(False)
        self.sensDictBtn = QPushButton(text="Edit",checkable=True)
        self.sensDictBtn.clicked.connect(self.clicked_sensDictEdit)

        layout = QFormLayout()
        layout.addRow(QLabel(text="Record to file:"),self.recBox)
        layout.addRow(QLabel("Sensor Type:"))
        layout.addRow(self.sensTypeBox,self.sensTypeBtn)
        layout.addRow(QLabel("Sensor Calibration Table:"))
        layout.addRow(self.sensDictBox,self.sensDictBtn)
        self.vialSettingsBox.setLayout(layout)
            
    def createRunSettingsBox(self):
        self.runSettingsBox = QGroupBox("run settings")

        SpLabel = QLabel("Setpoint (SCCM):")
        SpEnter = QLineEdit(text=self.defSp, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('Sp',SpEnter.text()))
        SpSend = QPushButton(text="Update", clicked=lambda: self.sendP('Sp',SpEnter.text()))
        spLayout = QHBoxLayout()
        spLayout.addWidget(SpLabel)
        spLayout.addWidget(SpEnter)
        spLayout.addWidget(SpSend)

        VlLabel = QLabel("Open @ setpoint for x secs:")
        VlEnter = QLineEdit(text=defVl, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('OV',VlEnter.text()))
        VlButton = QPushButton(text="Go",clicked=lambda: self.sendP('OV',VlEnter.text()))
        vlLayout = QHBoxLayout()
        vlLayout.addWidget(VlLabel)
        vlLayout.addWidget(VlEnter)
        vlLayout.addWidget(VlButton)

        layout = QFormLayout()
        layout.addRow(SpLabel)
        layout.addRow(SpEnter,SpSend)
        layout.addRow(VlLabel)
        layout.addRow(VlEnter,VlButton)
        self.runSettingsBox.setLayout(layout)
    
    def createFlowTuningBox(self):
        self.flowTuningBox = QGroupBox("flow control tuning")

        KpLabel = QLabel('Kp:')
        KpEnter = QLineEdit(text=self.defKp, width=lineEditWidth, returnPressed=lambda: self.sendP('Kp',KpEnter.text()))
        KpSend = QPushButton(text="Send",clicked=lambda: self.sendP('Kp',KpEnter.text()))
        KpRow = QHBoxLayout()
        KpRow.addWidget(KpLabel)
        KpRow.addWidget(KpEnter)
        KpRow.addWidget(KpSend)
        KiLabel = QLabel('Ki:')
        KiEnter = QLineEdit(text=self.defKi, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('Ki',KiEnter.text()))
        KiSend = QPushButton(text="Send", clicked=lambda: self.sendP('Ki',KiEnter.text()))
        KiRow = QHBoxLayout()
        KiRow.addWidget(KiLabel)
        KiRow.addWidget(KiEnter)
        KiRow.addWidget(KiSend)
        KdLabel = QLabel('Kd:')
        KdEnter = QLineEdit(text=self.defKd, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('Kd',KdEnter.text()))
        KdSend = QPushButton(text="Send", clicked=lambda: self.sendP('Kd',KdEnter.text()))
        KdRow = QHBoxLayout()
        KdRow.addWidget(KdLabel)
        KdRow.addWidget(KdEnter)
        KdRow.addWidget(KdSend)
        
        SendAllButton = QPushButton(text="Send all K vals",clicked=lambda: self.sendP('Kx',KpEnter.text(),KiEnter.text(),KdEnter.text()))

        flowTuningBoxLayout = QFormLayout()
        flowTuningBoxLayout.addRow(KpRow)
        flowTuningBoxLayout.addRow(KiRow)
        flowTuningBoxLayout.addRow(KdRow)
        flowTuningBoxLayout.addRow(SendAllButton)
        self.flowTuningBox.setLayout(flowTuningBoxLayout)
    
    def createDebugBox(self):
        self.debugBox = QGroupBox("debugging")

        self.PIDToggle = QPushButton(text="Turn PID on",checkable=True,toggled=self.toggled_PID)
        self.CtrlToggle = QPushButton(text="Open prop valve",checkable=True,toggled=self.toggled_ctrlOpen)
        self.VlToggle = QPushButton(text="Open Iso Valve",checkable=True,toggled=self.toggled_valveOpen)

        layout = QVBoxLayout()
        layout.addWidget(self.PIDToggle)
        layout.addWidget(self.CtrlToggle)
        layout.addWidget(self.VlToggle)
        self.debugBox.setLayout(layout)
    
    def createDataReceiveBoxes(self):
        self.dataReceiveBox = QGroupBox("data received")

        self.receiveBox = QTextEdit(readOnly=True)
        receiveBoxLbl = QLabel(text="Flow val (int), Flow (SCCM), Ctrl val (int)")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        layout = QHBoxLayout()
        layout.addLayout(receiveBoxLayout)
        self.dataReceiveBox.setLayout(layout)
    
    
    # USER ACTION
    def clicked_sensTypeEdit(self, checked):
        if checked:
            self.sensTypeBtn.setText("Done")
            self.sensTypeBox.setEnabled(True)
        else:
            self.sensTypeBtn.setText("Edit")
            self.sensTypeBox.setEnabled(False)
            newSensType = self.sensTypeBox.currentText()
            if not self.sensType == newSensType:
                self.sensType = newSensType
                self.logger.info('sensor type changed to: %s', self.sensType)
                title = "Vial " + str(self.vialNum) + ": " + self.sensType
                self.setTitle(title)
    
    def clicked_sensDictEdit(self, checked):
        if checked:
            self.sensDictBtn.setText("Done")
            self.sensDictBox.setEnabled(True)
        else:
            self.sensDictBtn.setText("Edit")
            self.sensDictBox.setEnabled(False)
            newSensDict = self.sensDictBox.currentText()
            if not self.sensDict == newSensDict:
                self.sensDict = newSensDict
                self.logger.info('sensor calibration table changed to: %s', self.sensDict)        
    
    
    def toggled_PID(self, checked):
        if checked:
            self.sendP('ON')
            self.PIDToggle.setText('Turn PID Off')
        else:
            self.sendP('OF')
            self.PIDToggle.setText('Turn PID On')

    def toggled_ctrlOpen(self, checked):
        if checked:
            self.sendP('OC')
            self.CtrlToggle.setText('Close prop valve')
        else:
            self.sendP('CC')
            self.CtrlToggle.setText('Open prop valve')
    
    def toggled_valveOpen(self, checked, value=""):
        if checked:
            self.sendP('OV')
            self.VlToggle.setText('Close Iso Valve')
        else:
            self.sendP('CV')
            self.VlToggle.setText('Open Iso Valve')

    
    def sendP(self, parameter, val1="", val2="", val3=""):
        if parameter == 'Sp':
            s_dict = self.parent.sccm2Ard_dicts.get(self.sensDict)
            calculatedSp = utils.convertToInt(float(val1),s_dict)
            value = str(calculatedSp)
        elif parameter == 'Kx':
            if val1:    str_Kp = "_P" + val1
            else:       str_Kp = ""
            if val2:    str_Ki = "_I" + val2
            else:       str_Ki = ""
            if val3:    str_Kd = "_D" + val3
            else:       str_Kd = ""
            value = str_Kp + str_Ki + str_Kd
            value = value[1:]   # remove the extra underscore at front
        else:
            value = val1
        
        self.parent.sendParameter(self.slave,self.vialNum,parameter,value)

    
    # ACCESSED BY EXTERNAL THINGS
    def changeMode(self, newMode):
        if self.mode == newMode:
            self.logger.info('same mode as previous')
        
        else:
            # delete all current widgets            
            for i in reversed(range(self.mainLayout.count())):
                item = self.mainLayout.itemAt(i)
                w = self.mainLayout.itemAt(i).widget()
                self.mainLayout.removeWidget(w)
                sip.delete(w)

            self.mode = newMode
            if self.mode == 'auto':
                self.createVialSettingsBox()
                self.createRunSettingsBox()
                self.createDataReceiveBoxes()
                self.mainLayout.addWidget(self.vialSettingsBox,0,0)
                self.mainLayout.addWidget(self.runSettingsBox,1,0)
                self.mainLayout.addWidget(self.dataReceiveBox,0,1,2,1)
                
            if self.mode == 'manual':
                self.createVialSettingsBox()
                self.createRunSettingsBox()
                self.createFlowTuningBox()
                self.createDebugBox()
                self.createDataReceiveBoxes()

                self.mainLayout.addWidget(self.vialSettingsBox,0,0)
                self.mainLayout.addWidget(self.runSettingsBox,1,0)
                self.mainLayout.addWidget(self.flowTuningBox,0,1)
                self.mainLayout.addWidget(self.debugBox,1,1)
                self.mainLayout.addWidget(self.dataReceiveBox,0,2,2,1)
    
    def appendNew(self, value):
        flowValue = value[0:4]
        ctrlValue = value[5:8]        

        flowVal = int(flowValue)
        s_dict = self.parent.ard2Sccm_dicts.get(self.sensDict)
        val_SCCM = utils.convertToSCCM(flowVal,s_dict)
        
        dataStr = flowValue + '\t' + str(val_SCCM) + '\t' + ctrlValue
        self.receiveBox.append(dataStr)


class Slave(QGroupBox):

    def __init__(self, parent, slaveName, numVials, sensorTypes):
        super().__init__()
        self.slaveName = slaveName
        self.numVials = numVials
        self.sensorTypes = sensorTypes

        layout = QVBoxLayout()
        self.vials = []
        for x in range(numVials):
            vialNum = x+1
            try:
                v_sensorType = sensorTypes[vialNum]
            except IndexError:
                v_sensorType = sensorTypes[0]
            #v_vial = vial.Vial(parent,slaveName,vialNum,v_sensorType)
            v_vial = Vial(parent,slaveName,vialNum,v_sensorType)
            self.vials.append(v_vial)
            layout.addWidget(v_vial)
        
        self.setTitle("Slave " + self.slaveName)
        self.setLayout(layout)


class worker(QObject):
    finished = pyqtSignal()
    w_sendThisSp = pyqtSignal(str,int,int)
    w_send_OpenValve = pyqtSignal(str,int,int)
    w_incProgBar = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setpoint = 0
        self.lineToRun_1 = ' '
        self.lineToRun_2 = ' '

        self.dur_ON = 0
        self.dur_OFF = 0
        self.numRuns = 0
        self.threadON = False

        self.minSp = 0; self.maxSp = 0; self.incSp = 0
        self.spOrder = ' '
        self.expType = ' '
        self.spType = ' '

    @pyqtSlot()
    def exp(self):
        if self.expType == 'One vial':
            slaveToRun = self.lineToRun_1[0]
            vialToRun = int(self.lineToRun_1[1])
            
            if self.spType == 'Constant':
                self.w_sendThisSp.emit(slaveToRun,vialToRun,self.setpoint); time.sleep(waitBtSpAndOV)
                for i in range(self.numRuns):
                    if self.threadON == True:
                        self.w_send_OpenValve.emit(slaveToRun,vialToRun,self.dur_ON);   time.sleep(self.dur_ON + self.dur_OFF)
                        progBarVal = int(((i+1)/self.numRuns)*100)
                        self.w_incProgBar.emit(progBarVal)
                    if self.threadON == False:  break
                self.finished.emit()
                self.threadON = False
                
            if self.spType == 'Varied':
                values = []
                i = self.minSp
                while i < self.maxSp:
                    values.append(i)
                    i += self.incSp

                for i in range(self.numRuns):
                    if self.spOrder == 'Random':    random.shuffle(values)
                    for j in values:
                        sccmVal = j
                        if self.threadON == True:
                            self.w_sendThisSp.emit(slaveToRun,vialToRun,sccmVal);   time.sleep(waitBtSpAndOV)
                            self.w_send_OpenValve.emit(slaveToRun,vialToRun,self.dur_ON);       time.sleep(self.dur_ON)
                            time.sleep(self.dur_OFF-waitBtSpAndOV)
                            idx = values.index(j) + 1
                            progBarVal = int((idx / (len(values)*self.numRuns)) *100)
                            self.w_incProgBar.emit(progBarVal)
                        if self.threadON == False:  break
                    self.finished.emit()
                    self.threadON = False
        
        # this can only do for 2 additive vials i don't have the energy to figure out how to make it work for 3
        if self.expType == 'Additive vials':
            slaveToRun1 = self.lineToRun_1[0]
            slaveToRun2 = self.lineToRun_2[0]
            vialToRun1 = int(self.lineToRun_1[1])
            vialToRun2 = int(self.lineToRun_2[1])

            for i in range(self.numRuns):
                if self.threadON == True:
                    sccmVal1 = random.randint(1,self.setpoint)
                    sccmVal2 = self.setpoint - sccmVal1
                    self.w_sendThisSp.emit(slaveToRun1,vialToRun1,sccmVal1);    time.sleep(waitBtSps)
                    self.w_sendThisSp.emit(slaveToRun2,vialToRun2,sccmVal2);    time.sleep(waitBtSpAndOV)
                    self.w_send_OpenValve.emit(slaveToRun1,vialToRun1,self.dur_ON);         time.sleep(waitBtSpAndOV)
                    self.w_send_OpenValve.emit(slaveToRun2,vialToRun2,self.dur_ON);         time.sleep(self.dur_ON - waitBtSpAndOV)
                    time.sleep(self.dur_OFF-waitBtSps-waitBtSpAndOV)
                if self.threadON == False:  break
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
        self.obj = worker()
        self.thread1 = QThread()
        self.obj.moveToThread(self.thread1)
        self.setUpThreads()
        
        self.createConnectBox()
        #size = self.connectBox.sizeHint()
        #cboxWidth = size.width()
        self.createMasterBox()
        self.createSlaveGroupBox()  # need to make this before vial programming box
        self.createFlowSettingsBox()
        self.createVialProgrammingBox()
        
        self.column2Layout = QVBoxLayout()
        self.column2Layout.addWidget(self.masterBox)
        #self.column2Layout.addWidget(self.flowSettingsBox)
        self.column2Layout.addWidget(self.vialProgrammingBox)
        
        #self.masterBox.setFixedWidth(col2Width)
        #self.vialProgrammingBox.setFixedWidth(col2Width)

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
        self.ardConfig_s = utils.getArduinoConfigFile(arduinoSlaveConfigFile)
        
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
            #s_slave = slave.Slave(self,s_slaveName,s_vPSlave,s_sensor)
            s_slave = Slave(self,s_slaveName,s_vPSlave,s_sensor)
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
        self.obj.w_sendThisSp.connect(self.sendThisSetpoint)
        self.obj.w_send_OpenValve.connect(self.send_OpenValve)
        self.obj.w_incProgBar.connect(self.incProgBar)
        self.obj.finished.connect(self.threadIsFinished)
        self.thread1.started.connect(self.obj.exp)
    
    def createVialProgrammingBox(self):
        self.vialProgrammingBox = QGroupBox("Vial Programming")
        
        self.p_additiveSelect = QComboBox();  self.p_additiveSelect.addItems(['One vial','Additive vials'])
        
        self.p_vialSelect1 = QComboBox();   self.p_vialSelect2 = QComboBox()
        for s in self.slaves:
            for v in s.vials:
                vialName = s.slaveName + str(v.vialNum)
                self.p_vialSelect1.addItem(vialName)
                self.p_vialSelect2.addItem(vialName)
        self.p_vialSelect1.setCurrentIndex(0)
        self.p_vialSelect2.setCurrentIndex(1)
        
        p_vialBoxLayout = QFormLayout()
        p_vialBoxLayout.addRow(QLabel("Vial 1:"),self.p_vialSelect1)
        p_vialBoxLayout.addRow(QLabel("Vial 2:"),self.p_vialSelect2)
        self.p_vialBox = QGroupBox('Vial(s) to run:');  self.p_vialBox.setLayout(p_vialBoxLayout)        
        
        self.p_spType = QComboBox();    self.p_spType.addItems(['Constant','Varied'])
        self.p_spOrder = QComboBox();   self.p_spOrder.addItems(['Sequential','Random'])
        self.p_sp = QSpinBox(maximum=maxSp,value=defSp)
        self.p_spMin = QSpinBox(maximum=maxSp,value=1); 
        self.p_spMax = QSpinBox(maximum=maxSp,value=10)
        self.p_spInc = QSpinBox(maximum=maxSp/2,value=2)
        
        p_sp1_layout = QFormLayout()
        p_sp1_layout.addRow(QLabel("Constant or varied?:"),self.p_spType)
        p_sp1_layout.addRow(QLabel("(Total) Setpoint:"),self.p_sp)
        self.p_sp1 = QWidget(); self.p_sp1.setLayout(p_sp1_layout)
        p_spBox_rowLayout = QHBoxLayout()
        p_spBox_rowLayout.addWidget(QLabel("Min:"));    p_spBox_rowLayout.addWidget(self.p_spMin)
        p_spBox_rowLayout.addWidget(QLabel("Max:"));    p_spBox_rowLayout.addWidget(self.p_spMax)
        p_sp2_layout = QFormLayout()
        p_sp2_layout.addRow(p_spBox_rowLayout)
        p_sp2_layout.addRow(QLabel("Increment by:"),self.p_spInc)
        p_sp2_layout.addRow(QLabel("Setpoint order:"))
        p_sp2_layout.addRow(self.p_spOrder)
        self.p_sp2 = QWidget(); self.p_sp2.setLayout(p_sp2_layout)
        p_spBoxLayout = QHBoxLayout()
        p_spBoxLayout.addWidget(self.p_sp1)
        p_spBoxLayout.addWidget(self.p_sp2)
        p_spBox = QGroupBox('Setpoint:');   p_spBox.setLayout(p_spBoxLayout)
        
        self.p_durON = QSpinBox(value=defDurOn)
        self.p_durOFF = QSpinBox(value=defDurOff)
        p_isoBoxLayout = QHBoxLayout()
        p_isoBoxLayout.addWidget(QLabel("Dur open:"));      p_isoBoxLayout.addWidget(self.p_durON)
        p_isoBoxLayout.addWidget(QLabel("Dur closed:"));    p_isoBoxLayout.addWidget(self.p_durOFF)
        p_isoBox = QGroupBox('Isolation valve duration (sec):');  p_isoBox.setLayout(p_isoBoxLayout)
        
        self.p_numRuns = QSpinBox(value=defNumRuns,maximum=500)
        self.progDurLbl = QLabel()
        self.progBar = QProgressBar()
        
        self.progSettingsLayout = QFormLayout()
        self.progSettingsLayout.addRow(QLabel("Exp. type:"),self.p_additiveSelect)
        self.progSettingsLayout.addRow(self.p_vialBox)
        self.progSettingsLayout.addRow(p_spBox)
        self.progSettingsLayout.addRow(p_isoBox)
        self.progSettingsLayout.addRow(QLabel("# of runs"),self.p_numRuns)
        self.progSettingsLayout.addRow(QLabel("Total Duration:"),self.progDurLbl)
        self.progSettingsLayout.addRow(QLabel("Progress:"),self.progBar)
        self.progSettingsBox = QWidget();   self.progSettingsBox.setLayout(self.progSettingsLayout)
        
        self.programStartButton = QPushButton(text="Start",checkable=True,clicked=self.programStartClicked,toolTip="must be in auto mode to start a program")
        self.programStartButton.setEnabled(False)        
        
        layout = QFormLayout()
        layout.addRow(self.progSettingsBox)
        layout.addRow(self.programStartButton)
        self.vialProgrammingBox.setLayout(layout)

        self.p_additiveSelect.currentIndexChanged.connect(self.additive_changed);   self.additive_changed()
        self.p_spType.currentIndexChanged.connect(self.spType_changed);             self.spType_changed()        
        self.p_durON.valueChanged.connect(self.updateProgDurLabel)
        self.p_durOFF.valueChanged.connect(self.updateProgDurLabel)
        self.p_numRuns.valueChanged.connect(self.updateProgDurLabel)
        self.updateProgDurLabel()
        
    def additive_changed(self):
        currentText = self.p_additiveSelect.currentText()
        if currentText == 'Additive vials':
            self.p_vialSelect1.setEnabled(True)
            self.p_vialSelect2.setEnabled(True)
            self.p_spType.setCurrentIndex(0)
            self.p_spType.setEnabled(False)
        if currentText == 'One vial':
            self.p_vialSelect1.setEnabled(True)
            self.p_vialSelect2.setEnabled(False)
            self.p_spType.setEnabled(True)
            
    def spType_changed(self):
        currentText = self.p_spType.currentText()
        if currentText == 'Constant':
            self.p_spOrder.setEnabled(False)
            self.p_sp2.setEnabled(False)
        if currentText == 'Varied':
            self.p_spOrder.setEnabled(True)
            self.p_sp2.setEnabled(True)
    
    def programStartClicked(self, checked):
        if checked:
            if self.window().recordButton.isChecked() == False:
                self.logger.warning('not recording to file')
            self.programStartButton.setText('Stop')
            self.progSettingsBox.setEnabled(False)
            
            self.expType = self.p_additiveSelect.currentText()
            self.obj.lineToRun_1 = self.p_vialSelect1.currentText()
            self.obj.lineToRun_2 = self.p_vialSelect2.currentText()

            self.obj.dur_ON = self.p_durON.value()   # give worker all the values
            self.obj.dur_OFF = self.p_durOFF.value()
            self.obj.numRuns = self.p_numRuns.value()
            self.obj.setpoint = self.p_sp.value()
            self.obj.spOrder = self.p_spOrder.currentText()
            self.obj.expType = self.p_additiveSelect.currentText()
            self.obj.spType = self.p_spType.currentText()
            self.obj.minSp = self.p_spMin.value()
            self.obj.maxSp = self.p_spMax.value()
            self.obj.incSp = self.p_spInc.value()

            self.obj.threadON = True
            self.logger.debug('Starting thread')
            self.thread1.start()
            
        else:
            self.progSettingsBox.setEnabled(True)
            self.logger.info('program stopped early by user')
            self.threadIsFinished()
    
    def updateProgDurLabel(self):
        # iso valve duration
        # num runs

        # calculate duration of experiment
        # one vial
        totalDur = (self.p_durON.value() + self.p_durOFF.value())*self.p_numRuns.value()

        self.progDurLbl.setText(str(totalDur) + " seconds")
    
    
    
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

    def send_OpenValve(self, slave:str, vial:int, dur:int):
        #dur = self.dur_ON
        self.sendParameter(slave,vial,'OV',str(dur))

    def threadIsFinished(self):
        self.obj.threadON = False
        self.thread1.exit()
        self.programStartButton.setChecked(False);  self.programStartButton.setText('Start')
        self.progSettingsBox.setEnabled(True)
        self.logger.info('Finished program')
        self.progBar.setValue(0)

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

                        except IndexError as err:
                            self.logger.error('arduino master config file does not include vial %s', vialInfo)
                except UnicodeDecodeError as err:
                    self.logger.error('Serial read error: %s\t%s',err,text)
            else:
                self.logger.debug('warning - text from Arduino was %s bytes: %s', len(text), text)
    
    def sendParameter(self, slave:str, vial:int, parameter:str, value=""):
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
    
    def incProgBar(self, val):
        self.progBar.setValue(val)


    '''
    def updatePort(self, newPort):
        self.port = newPort
        self.logger.info('port changed to %s', self.port)
    def updateName(self, newName):
        if not self.name == newName:
            self.name = newName
            self.logger.info('name changed to %s', self.name)
            self.setTitle(self.name)
    '''