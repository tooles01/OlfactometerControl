# ST 2020
# vial.py

import time, collections, sip, os
from PyQt5.QtWidgets import (QGroupBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
                            QFormLayout, QTextEdit, QVBoxLayout, QGridLayout)
from datetime import datetime
import utils, config

vinQ = 10
lineEditWidth = 45 
defSp = str(config.defSpval)
defVl = str(config.defVlval)
defMode = 'auto'
keysToGet = ['defKp','defKi','defKd']

class Vial(QGroupBox):
    #keysToGet = ['defKp','defKi','defKd']       # accessible as a property of the class and as a property of objects

    def __init__(self, parent, slave, vialNum, sensorType):
        super().__init__()
        self.parent = parent
        self.slave = slave          # instance attr - only accessible from the scope of an object
        self.vialNum = vialNum
        self.sensorType = sensorType
        self.mode = defMode

        className = type(self).__name__
        loggerName = className + ' (' + self.parent.name + ' ' + self.slave + str(self.vialNum) + ')'
        self.logger = utils.createLogger(loggerName)

        # get default shit from config_slave file
        configDir = utils.findConfigFolder()
        olfactometerFolder = configDir + '\\olfactometer'
        os.chdir(olfactometerFolder)
        slaveVars = utils.getArduinoConfigFile('config_slave.h')
        for key in keysToGet:
            keyStr = 'self.' + key
            if key in slaveVars.keys():
                exec(keyStr + '=slaveVars.get(key)')
            else:
                exec(keyStr + '="0.000"')

        title = "Vial " + slave + str(vialNum) + ": " + self.sensorType
        self.setTitle(title)
        #self.arduino_time = collections.deque(vinQ*[0],vinQ)
        #self.arduino_data = collections.deque(vinQ*[0],vinQ)
        
        if self.mode == 'auto':
            self.mainLayout = QGridLayout()
            self.setLayout(self.mainLayout)

            self.createVialSettingsBox()
            self.createRunSettingsBox()
            self.createDataReceiveBoxes()

            self.mainLayout.addWidget(self.vialSettingsBox,0,0)
            self.mainLayout.addWidget(self.runSettingsBox,1,0)
            self.mainLayout.addWidget(self.dataReceiveBox,0,1,2,1)
            #self.resize(self.sizeHint())
        
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
            #self.resize(self.sizeHint())

    
    def createVialSettingsBox(self):
        self.vialSettingsBox = QGroupBox("vial settings")

        recLabel = QLabel(text="Record to file:")
        self.recBox = QCheckBox(checkable=True,checked=True)

        sensLabel = QLabel("Sensor type:")
        self.sensTypeBox = QComboBox()
        self.sensTypeBox.addItems(config.sensorTypes)
        self.sensTypeBox.setCurrentText(self.sensorType)
        self.sensTypeBox.currentIndexChanged.connect(self.updateSensorType)

        layout = QFormLayout()
        layout.addRow(recLabel,self.recBox)
        layout.addRow(sensLabel,self.sensTypeBox)
        self.vialSettingsBox.setLayout(layout)
            
    def createRunSettingsBox(self):
        self.runSettingsBox = QGroupBox("run settings")

        SpLabel = QLabel("Setpoint (SCCM):")
        SpEnter = QLineEdit(text=defSp, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('Sp',SpEnter.text()))
        SpSend = QPushButton(text="Update", clicked=lambda: self.sendP('Sp',SpEnter.text()))
        spLayout = QHBoxLayout()
        spLayout.addWidget(SpLabel)
        spLayout.addWidget(SpEnter)
        spLayout.addWidget(SpSend)

        VlLabel = QLabel("Open @ setpoint for x secs:")
        VlEnter = QLineEdit(text=defVl, maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('OV',VlEnter.text()))
        VlButton = QPushButton(text="Go",clicked=lambda: self.sendP('OV',VlEnter.text()))
        #VlButton = QPushButton(text="Go",toggled=lambda: self.toggled_valveOpen)#=lambda: self.sendP('OV',VlEnter.text()))
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
        self.receiveBox.setFixedWidth(210)
        receiveBoxLbl = QLabel(text="Flow val (int), Flow (SCCM), Ctrl val (int)")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        self.flowBox = QTextEdit(readOnly=True)
        flowBoxLbl = QLabel(text="Flow (SCCM)")
        flowBoxLayout = QVBoxLayout()
        flowBoxLayout.addWidget(flowBoxLbl)
        flowBoxLayout.addWidget(self.flowBox)

        self.ctrlvalBox = QTextEdit(readOnly=True)
        ctrlvalLbl = QLabel(text="Ctrl val (int)")
        ctrlBoxLayout = QVBoxLayout()
        ctrlBoxLayout.addWidget(ctrlvalLbl)
        ctrlBoxLayout.addWidget(self.ctrlvalBox)

        layout = QHBoxLayout()
        layout.addLayout(receiveBoxLayout)
        #layout.addLayout(flowBoxLayout)
        #layout.addLayout(ctrlBoxLayout)
        self.dataReceiveBox.setLayout(layout)
    


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
            #sip.delete(self.mainLayout)

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
        #elif parameter == 'OV':
            
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
    
    def toggled_valveOpen(self, checked, value=""):
        if checked:
            self.sendP('OV')
            self.VlToggle.setText('Close Iso Valve')
        else:
            self.sendP('CV')
            self.VlToggle.setText('Open Iso Valve')

    def updateSensorType(self):
        self.sensorType = self.sensTypeBox.currentText()

        title = "Vial " + str(self.vialNum) + ": " + self.sensorType
        self.setTitle(title)
        self.logger.info('sensor changed to %s', self.sensorType)
            
    def appendNew(self, value):
        flowValue = value[0:4]
        ctrlValue = value[5:8]        

        flowVal = int(flowValue)
        val_SCCM = utils.convertToSCCM(flowVal, self.sensorType)
        
        dataStr = flowValue + '\t' + str(val_SCCM) + '\t' + ctrlValue
        self.receiveBox.append(dataStr)
        
        #self.receiveBox.append(flowValue)
        #self.flowBox.append(str(val_SCCM))
        #self.ctrlvalBox.append(ctrlValue)


        #self.arduino_time.appendleft(timeNow)
        #self.arduino_data.appendleft(flowValue)
        #self.arduino_time.pop()
        #self.arduino_data.pop()