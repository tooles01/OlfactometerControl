# ST 2020
# vial.py

import time, collections
from PyQt5.QtWidgets import QGroupBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QTextEdit, QVBoxLayout
from datetime import datetime

import utils, config

vinQ = 10

class Vial(QGroupBox):
    textEditWidth = 80
    lineEditWidth = 45 # accessible as a property of the class and as a property of objects

    defSp = str(config.defSpval)
    defVl = str(config.defVlval)
    # get default shit from config_slave file
    keysToGet = ['defKp','defKi','defKd']
    slaveVars = utils.getArduinoConfigFile('config_slave.h')
    for key in keysToGet:
        if key in slaveVars.keys(): exec(key + '=slaveVars.get(key)')
        else: exec(key + '="0.000"')    

    def __init__(self, parent, slave, vialNum, sensorType):
        super().__init__()

        self.parent = parent
        self.slave = slave          # instance attr - only accessible from the scope of an object
        self.vialNum = vialNum
        self.sensorType = sensorType

        title = "Vial " + str(vialNum) + ": " + self.sensorType
        self.setTitle(title)
        
        self.arduino_time = collections.deque(vinQ*[0],vinQ)
        self.arduino_data = collections.deque(vinQ*[0],vinQ)

        self.createTuningBox(parent,slave,vialNum)
        self.createTestingBox()
        self.createSettingsBox()
        self.createDataReceiveBoxes()
        
        layout = QHBoxLayout()
        
        layout.addWidget(self.tuningBox)
        layout.addWidget(self.testingBox)
        layout.addWidget(self.settingsBox)
        layout.addWidget(self.dataReceiveBox)
        self.setLayout(layout)

    def createTuningBox(self, parent, slave, vialNum):
        self.tuningBox = QGroupBox("flow control tuning")

        KpLabel = QLabel('Kp:')
        KpEnter = QLineEdit(text=Vial.defKp, maximumWidth=self.lineEditWidth, returnPressed=lambda: self.sendP('Kp',KpEnter.text()))
        KpSend = QPushButton(text="Send Kp",clicked=lambda: self.sendP('Kp',KpEnter.text()))
        KpRow = QHBoxLayout()
        KpRow.addWidget(KpLabel)
        KpRow.addWidget(KpEnter)
        KpRow.addWidget(KpSend)
        KiLabel = QLabel('Ki:')
        KiEnter = QLineEdit(text=Vial.defKi, maximumWidth=self.lineEditWidth, returnPressed=lambda: self.sendP('Ki',KiEnter.text()))
        KiSend = QPushButton(text="Send Ki", clicked=lambda: self.sendP('Ki',KiEnter.text()))
        KiRow = QHBoxLayout()
        KiRow.addWidget(KiLabel)
        KiRow.addWidget(KiEnter)
        KiRow.addWidget(KiSend)
        KdLabel = QLabel('Kd:')
        KdEnter = QLineEdit(text=Vial.defKd, maximumWidth=self.lineEditWidth, returnPressed=lambda: self.sendP('Kd',KdEnter.text()))
        KdSend = QPushButton(text="Send Kd", clicked=lambda: self.sendP('Kd',KdEnter.text()))
        KdRow = QHBoxLayout()
        KdRow.addWidget(KdLabel)
        KdRow.addWidget(KdEnter)
        KdRow.addWidget(KdSend)
        
        SendAllButton = QPushButton(text="Send all K vals",clicked=lambda: self.sendP('Kx',KpEnter.text(),KiEnter.text(),KdEnter.text()))
        printShit = QPushButton(text="print",clicked=lambda: self.sendP('Ge'))

        tuningBoxLayout = QFormLayout()
        tuningBoxLayout.addRow(KpRow)
        tuningBoxLayout.addRow(KiRow)
        tuningBoxLayout.addRow(KdRow)
        tuningBoxLayout.addRow(SendAllButton)
        #tuningBoxLayout.addRow(printShit)
        self.tuningBox.setLayout(tuningBoxLayout)
    
    def createTestingBox(self):
        self.testingBox = QGroupBox("buttons for testing shit")

        self.PIDToggle = QPushButton(text="Turn PID on",checkable=True,toggled=self.toggled_PID)
        self.CtrlToggle = QPushButton(text="Open prop valve",checkable=True,toggled=self.toggled_ctrlOpen)
        self.VlToggle = QPushButton(text="Open Iso Valve",checkable=True,toggled=self.toggled_valveOpen)
        
        layout = QVBoxLayout()
        layout.addWidget(self.PIDToggle)
        layout.addWidget(self.CtrlToggle)
        layout.addWidget(self.VlToggle)
        self.testingBox.setLayout(layout)
    
    def createSettingsBox(self):
        self.settingsBox = QGroupBox("settings")

        sensLabel = QLabel("Sensor type:")
        sensTypeBox = QComboBox()
        sensTypeBox.addItems(config.sensorTypes)
        sensTypeBox.setCurrentText(self.sensorType)
        sensTypeUpdate = QPushButton(text="Update",clicked=lambda: self.updateSensorType(sensTypeBox.currentText()))

        SpLabel = QLabel("Setpoint (SCCM):")
        SpEnter = QLineEdit(text=Vial.defSp, maximumWidth=self.lineEditWidth, returnPressed=lambda: self.sendP('Sp',SpEnter.text()))
        SpSend = QPushButton(text="Update", clicked=lambda: self.sendP('Sp',SpEnter.text()))

        VlLabel = QLabel("Open & hit setpoint for x secs:")
        VlEnter = QLineEdit(text=Vial.defVl, maximumWidth=self.lineEditWidth, returnPressed=lambda: self.sendP('OV',VlEnter.text()))
        VlButton = QPushButton(text="Go",clicked=lambda: self.sendP('OV',VlEnter.text()))

        layout = QFormLayout()
        layout.addRow(sensLabel)
        layout.addRow(sensTypeBox,sensTypeUpdate)
        layout.addRow(SpLabel)
        layout.addRow(SpEnter,SpSend)
        layout.addRow(VlLabel)
        layout.addRow(VlEnter,VlButton)
        self.settingsBox.setLayout(layout)
    
    def createDataReceiveBoxes(self):
        self.dataReceiveBox = QGroupBox("data received")

        self.receiveBox = QTextEdit(readOnly=True, maximumWidth=self.textEditWidth)
        receiveBoxLbl = QLabel(text="Flow val (int)")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        self.flowBox = QTextEdit(readOnly=True, maximumWidth=self.textEditWidth)
        flowBoxLbl = QLabel(text="Flow (SCCM)")
        flowBoxLayout = QVBoxLayout()
        flowBoxLayout.addWidget(flowBoxLbl)
        flowBoxLayout.addWidget(self.flowBox)

        self.ctrlvalBox = QTextEdit(readOnly=True, maximumWidth=self.textEditWidth)
        ctrlvalLbl = QLabel(text="Ctrl val (int)")
        ctrlBoxLayout = QVBoxLayout()
        ctrlBoxLayout.addWidget(ctrlvalLbl)
        ctrlBoxLayout.addWidget(self.ctrlvalBox)

        layout = QHBoxLayout()
        layout.addLayout(receiveBoxLayout)
        layout.addLayout(flowBoxLayout)
        layout.addLayout(ctrlBoxLayout)
        self.dataReceiveBox.setLayout(layout)
    
    def sendP(self, parameter, val1="", val2="", val3=""):

        if parameter == 'Sp':
            calculatedSp = utils.convertToInt(int(val1),self.sensorType)
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
    
    def toggled_valveOpen(self, checked):
        if checked:
            self.sendP('OV')
            self.VlToggle.setText('Close Iso Valve')
        else:
            self.sendP('CV')
            self.VlToggle.setText('Open Iso Valve')

    def updateSensorType(self, newType):
        self.sensorType = newType

        title = "Vial " + str(self.vialNum) + ": " + self.sensorType
        self.setTitle(title)
            
    def appendNew(self, value):
        
        timeNow = datetime.time(datetime.now())
        flowValue = value[0:4]
        ctrlValue = value[5:8]

        self.arduino_time.appendleft(timeNow)
        self.arduino_data.appendleft(flowValue)
        self.arduino_time.pop()
        self.arduino_data.pop()

        self.receiveBox.append(flowValue)

        flowVal = int(flowValue)
        val_SCCM = utils.convertToSCCM(flowVal, self.sensorType)
        self.flowBox.append(str(val_SCCM))

        self.ctrlvalBox.append(ctrlValue)
