# ST 2020
# vial.py

import sip, os
from PyQt5.QtWidgets import (QGroupBox, QWidget, QComboBox, QHBoxLayout, QLabel, QLineEdit,
                            QPushButton, QCheckBox, QFormLayout, QTextEdit, QVBoxLayout, QGridLayout)
import utils, config

defMode = 'auto'
defVl = str(config.defVlval)
lineEditWidth = 45


class Vial(QGroupBox):

    def __init__(self, parent, slave, vialNum, sensorType):
        super().__init__()
        self.parent = parent
        self.slave = slave
        self.vialNum = vialNum
        self.sensType = sensorType      ## ** sensor type doesn't matter - just the dictionary does
        self.mode = defMode

        # get the dictionary u want
        self.sensDict = self.parent.cal_sheets[0]        

        className = type(self).__name__
        loggerName = className + ' (' + self.parent.name + ' ' + self.slave + str(self.vialNum) + ')'
        self.logger = utils.createLogger(loggerName)

        self.getDefVals()

        title = "Vial " + slave + str(vialNum) + ": " + self.sensType
        self.setTitle(title)        

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
    
    
    def getDefVals(self):
        slaveVars = self.parent.ardConfig_s
        keysToGet = self.parent.keysToGet
        for key in keysToGet:
            keyStr = 'self.' + key
            exec(keyStr + '=slaveVars.get(key)')
    
    def createVialSettingsBox(self):
        self.vialSettingsBox = QGroupBox("vial settings")

        recLabel = QLabel(text="Record to file:")
        self.recBox = QCheckBox(checkable=True,checked=True)

        sensTypeLbl = QLabel("Sensor Type:")
        self.sensTypeBox = QComboBox()
        self.sensTypeBox.addItems(config.sensorTypes)
        self.sensTypeBox.setCurrentText(self.sensType)
        self.sensTypeBox.setEnabled(False)
        self.sensTypeBtn = QPushButton(text="Edit",checkable=True)
        self.sensTypeBtn.clicked.connect(self.clicked_sensTypeEdit)

        sensDictLbl = QLabel("Sensor Calibration Table:")
        self.sensDictBox = QComboBox()
        self.sensDictBox.addItems(self.parent.cal_sheets)
        self.sensDictBox.setCurrentText(self.sensDict)
        self.sensDictBox.setEnabled(False)
        self.sensDictBtn = QPushButton(text="Edit",checkable=True)
        self.sensDictBtn.clicked.connect(self.clicked_sensDictEdit)

        layout = QFormLayout()
        layout.addRow(recLabel,self.recBox)
        layout.addRow(sensTypeLbl)
        layout.addRow(self.sensTypeBox,self.sensTypeBtn)
        layout.addRow(sensDictLbl)
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
        #self.receiveBox.setFixedWidth(210)
        receiveBoxLbl = QLabel(text="Flow val (int), Flow (SCCM), Ctrl val (int)")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        '''
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
        '''

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
            s_dict = self.parent.sccm2Ard_dicts.get(self.sensDict)
            calculatedSp = utils.convertToInt(int(val1),s_dict)
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
    
    def appendNew(self, value):
        flowValue = value[0:4]
        ctrlValue = value[5:8]        

        flowVal = int(flowValue)
        s_dict = self.parent.ard2Sccm_dicts.get(self.sensDict)
        val_SCCM = utils.convertToSCCM(flowVal,s_dict)
        
        dataStr = flowValue + '\t' + str(val_SCCM) + '\t' + ctrlValue
        self.receiveBox.append(dataStr)