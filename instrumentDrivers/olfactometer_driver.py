# ST 2020
# olfactometer_driver.py

import os, time, pandas, numpy, random, csv
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QTimer
from serial.tools import list_ports
import utils
import sip
from datetime import datetime, timedelta
import json


currentDate = utils.currentDate
calValue = 100

### VIAL
defMode = 'auto'
lineEditWidth = 45
defSensorCal = 'A1_2021-01-05'
keysToGet = ['defKp','defKi','defKd','defSp']
sensorTypes = ["Honeywell 3100V", "Honeywell 3300V", "Honeywell 5101V"]
testingModes = ['auto','manual']

### OLFACTOMETER
charsToRead = 16
noPortMsg = ' ~ No COM ports detected ~'
arduinoMasterConfigFile = 'config_master.h'
arduinoSlaveConfigFile = 'config_slave.h'

### DEFAULT VALUES
defDurOn = 5
defDurOff = 5
defNumRuns = 10
defSp = 100
maxSp = 200
defVl = 5
defManualCmd = 'S_OV_5_A123B1C4'

### WORKER
waitBtSpAndOV = .5
waitBtSps = 1

vialProgrammingOn = False

'''
class VialInfoWindow(QWidget):
    vial_info_changed = pyqtSignal()

    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.name = self.parent.name

        self.generate_ui()
        self.vial_info_changed.connect(self.parent.update_vial)
        self.hide()

    def generate_ui(self):
        self.setWindowTitle('Vial Info/Configuration')

        self.groupBox = QGroupBox('Vial ' + self.name)

        self.odor_wid = QLineEdit()
        self.sens_wid = QComboBox()
        self.sens_wid.addItems(sensorTypes)
        self.flowCal_wid = QComboBox()
        self.flowCal_wid.addItems(self.parent.parent.parent.sccm2Ard_dicts)

        self.applyBtn = QPushButton('Apply Values')
        self.cancelBtn = QPushButton('Cancel')
        
        self.applyBtn.clicked.connect(self.edit_info)
        self.cancelBtn.clicked.connect(self.close_window)

        layout1 = QFormLayout()
        layout1.addRow(QLabel('Odor:'),self.odor_wid)
        layout1.addRow(QLabel('Sensor type:'),self.sens_wid)
        layout1.addRow(QLabel('Calibration table:'),self.flowCal_wid)
        self.groupBox.setLayout(layout1)

        self.main_layout = QFormLayout()
        self.main_layout.addRow(self.groupBox)
        self.main_layout.addRow(self.applyBtn,self.cancelBtn)
        self.setLayout(self.main_layout)
    
        
    def edit_info(self):
        print('not set up yet')

        # change the values in vial object
        self.parent.odor = self.odor_wid.text()
        self.parent.calTable = self.flowCal_wid.currentText()
        self.parent.sensType = self.sens_wid.currentText()
        # tell the vial to make necessary changes
        self.vial_info_changed.emit()

        self.close_window()
    
    def close_window(self):
        self.hide()
'''

class Vial(QObject):

    def __init__(self, parent, vialNum, calTable, setpoint, Kp, Ki, Kd):
        super().__init__()
        self.parent = parent
        self.vialNum = vialNum

        self.calTable = calTable
        self.setpoint = setpoint
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        self.name = self.parent.slaveName + str(self.vialNum)
        self.intToSccm_dict = self.parent.parent.ard2Sccm_dicts.get(self.calTable)
        self.sccmToInt_dict = self.parent.parent.sccm2Ard_dicts.get(self.calTable)

        self.generate_ui_features()


    def generate_ui_features(self):
        self.create_vial_debug_window()
        
        self.OVcheckbox = QCheckBox(checkable=True, checked=False, toolTip='Apply update to this vial')
        self.mainBtn = QPushButton(text=self.name, checkable=True, toolTip='Vial Status (open/closed)')

        self.vialDebugBtn = QPushButton(text='Debug')
        self.vialDebugBtn.clicked.connect(lambda: self.vialDebugWindow.show())
        
        self.calTable_widget = QComboBox()
        self.calTable_widget.addItems(self.parent.parent.ard2Sccm_dicts)
        self.calTable_widget.setCurrentText(self.calTable)
        self.calTable_widget.currentIndexChanged.connect(lambda: self.new_calTable(self.calTable_widget.currentText()))

        self.setpoint_widget = QSpinBox(maximum=maxSp,value=self.setpoint)
        self.setpoint_sendBtn = QPushButton(text='Send Sp')
        self.setpoint_sendBtn.clicked.connect(self.new_setpoint)

        self.program_button = QPushButton(text=self.name, checkable=True)
        
        self.mainBtn.setMaximumWidth(50)
        self.setpoint_widget.setMaximumWidth(80)
        self.setpoint_sendBtn.setMaximumWidth(80)
        self.vialDebugBtn.setMaximumWidth(80)


    def create_vial_debug_window(self):
        self.vialDebugWindow = QWidget()
        self.vialDebugWindow.setWindowTitle('Vial ' + self.name + '- Debug')
        
        # Flow Calibration Table
        self.vialDebugWindow.calTable_wid = QComboBox(toolTip='Updates immediately')
        self.vialDebugWindow.calTable_wid.addItems(self.parent.parent.ard2Sccm_dicts)
        self.vialDebugWindow.calTable_wid.currentIndexChanged.connect(lambda: self.new_calTable(self.vialDebugWindow.calTable_wid.currentText()))

        # Setpoint
        self.vialDebugWindow.setpoint_wid = QSpinBox(maximum=maxSp,value=self.setpoint)
        self.vialDebugWindow.setpoint_sendBtn = QPushButton('Send Sp')
        self.vialDebugWindow.setpoint_sendBtn.clicked.connect(lambda: self.new_setpoint(self.vialDebugWindow.setpoint_wid.value()))
        setpoint_layout = QHBoxLayout()
        setpoint_layout.addWidget(QLabel('Setpoint:'))
        setpoint_layout.addWidget(self.vialDebugWindow.setpoint_wid)
        setpoint_layout.addWidget(self.vialDebugWindow.setpoint_sendBtn)

        # Open vial
        self.vialDebugWindow.openValve_widget = QSpinBox(maximum=5,value=5)
        self.vialDebugWindow.openValve_sendBtn = QPushButton('Open vial')
        self.vialDebugWindow.openValve_sendBtn.clicked.connect(self.open_vial)
        openValve_layout = QHBoxLayout()
        openValve_layout.addWidget(QLabel('Duration open (s):'))
        openValve_layout.addWidget(self.vialDebugWindow.openValve_widget)
        openValve_layout.addWidget(self.vialDebugWindow.openValve_sendBtn)
        
        self.vialDebugWindow.doneBtn = QPushButton(text='Done', toolTip='Close window')
        self.vialDebugWindow.doneBtn.clicked.connect(lambda: self.vialDebugWindow.hide())

        # Flow control parameters
        self.flowControlBox = QGroupBox('Flow control parameters')
        self.vialDebugWindow.Kp_wid = QLineEdit(text=str(self.Kp))
        self.vialDebugWindow.Ki_wid = QLineEdit(text=str(self.Ki))
        self.vialDebugWindow.Kd_wid = QLineEdit(text=str(self.Kd))
        self.vialDebugWindow.Kp_send = QPushButton(text='Send', clicked=lambda: self.sendP('Kp',self.vialDebugWindow.Kp_wid.text()))
        self.vialDebugWindow.Ki_send = QPushButton(text='Send', clicked=lambda: self.sendP('Ki',self.vialDebugWindow.Ki_wid.text()))
        self.vialDebugWindow.Kd_send = QPushButton(text='Send', clicked=lambda: self.sendP('Kd',self.vialDebugWindow.Kd_wid.text()))
        KpRow = QHBoxLayout();  KpRow.addWidget(QLabel('Kp:'));   KpRow.addWidget(self.vialDebugWindow.Kp_wid);   KpRow.addWidget(self.vialDebugWindow.Kp_send)
        KiRow = QHBoxLayout();  KiRow.addWidget(QLabel('Ki:'));   KiRow.addWidget(self.vialDebugWindow.Ki_wid);   KiRow.addWidget(self.vialDebugWindow.Ki_send)
        KdRow = QHBoxLayout();  KdRow.addWidget(QLabel('Kd:'));   KdRow.addWidget(self.vialDebugWindow.Kd_wid);   KdRow.addWidget(self.vialDebugWindow.Kd_send)
        flowControl_layout = QFormLayout()
        flowControl_layout.addRow(KpRow)
        flowControl_layout.addRow(KiRow)
        flowControl_layout.addRow(KdRow)
        self.flowControlBox.setLayout(flowControl_layout)

        # Manual debugging
        self.manualDebugBox = QGroupBox('Manual debug')
        self.vialDebugWindow.PIDToggle = QPushButton(text="Turn PID on", checkable=True, toggled=self.toggled_PID)
        self.vialDebugWindow.CtrlToggle = QPushButton(text="Open prop valve", checkable=True, toggled=self.toggled_ctrlOpen)
        self.vialDebugWindow.VlToggle = QPushButton(text="Open Iso Valve", checkable=True, toggled=self.toggled_valveOpen)
        manualDebug_layout = QHBoxLayout()
        manualDebug_layout.addWidget(self.vialDebugWindow.PIDToggle)
        manualDebug_layout.addWidget(self.vialDebugWindow.CtrlToggle)
        manualDebug_layout.addWidget(self.vialDebugWindow.VlToggle)
        self.manualDebugBox.setLayout(manualDebug_layout)

        layout1 = QFormLayout()
        layout1.addRow(QLabel('Calibration table:'),self.vialDebugWindow.calTable_wid)
        layout1.addRow(setpoint_layout)
        layout1.addRow(openValve_layout)
        layout1.addRow(self.flowControlBox)
        layout1.addRow(self.manualDebugBox)
        
        # Values received
        self.dataReceiveLbl = QLabel("Flow val (int), Flow (SCCM), Ctrl val (int)")
        self.dataReceiveBox = QTextEdit(readOnly=True)
        
        layout2 = QVBoxLayout()
        layout2.addWidget(self.dataReceiveLbl)
        layout2.addWidget(self.dataReceiveBox)

        self.vialInfoWindow_layout = QGridLayout()
        self.vialInfoWindow_layout.addLayout(layout1, 0, 0, 1, 1)
        self.vialInfoWindow_layout.addLayout(layout2, 0, 1, 1, 1)
        self.vialInfoWindow_layout.addWidget(self.vialDebugWindow.doneBtn, 1, 0, 1, 2)
        self.vialDebugWindow.setLayout(self.vialInfoWindow_layout)

        self.vialDebugWindow.hide()
    

    # USER ACTION    
    def sendP(self, param, value):
        param = str(param)
        value = str(value)
        vialStr = self.name

        strToSend = param + '_' + value + '_' + vialStr
        self.parent.parent.sendThisArray(strToSend)
    
    def new_calTable(self, newTable):
        newCalTable = newTable
        self.calTable = newCalTable
        self.intToSccm_dict = self.parent.parent.ard2Sccm_dicts.get(self.calTable)
        self.sccmToInt_dict = self.parent.parent.sccm2Ard_dicts.get(self.calTable)
        print('Vial ' + self.name  + ' new cal table:  '+ self.calTable)
        
    def new_setpoint(self, sccmVal):
        self.setpoint = self.vialDebugWindow.setpoint_wid.value()
        param = 'Sp'
        intVal = utils.convertToInt(self.setpoint, self.sccmToInt_dict)
        self.sendP(param, intVal)
        
    def open_vial(self, dur):
        duration_open = self.vialDebugWindow.openValve_widget.value()
        param = 'OV'
        self.sendP(param, duration_open)
        
    def toggled_PID(self, checked):
        if checked:
            self.sendP('ON', 0)
            self.vialDebugWindow.PIDToggle.setText('Turn PID Off')
        else:
            self.sendP('OF', 0)
            self.vialDebugWindow.PIDToggle.setText('Turn PID On')

    def toggled_ctrlOpen(self, checked):
        if checked:
            self.sendP('OC', 0)
            self.vialDebugWindow.CtrlToggle.setText('Close prop valve')
        else:
            self.sendP('CC', 0)
            self.vialDebugWindow.CtrlToggle.setText('Open prop valve')
    
    def toggled_valveOpen(self, checked, value=""):
        if checked:
            self.sendP('OV', 0)
            self.vialDebugWindow.VlToggle.setText('Close Iso Valve')
        else:
            self.sendP('CV', 0)
            self.vialDebugWindow.VlToggle.setText('Open Iso Valve')
    

    '''
    def new_vial_info(self):
        newSetpoint = self.vialDebugWindow.setpoint_wid.value()
        newCalTable = self.vialDebugWindow.calTable_wid.currentText()

        self.setpoint = newSetpoint
        self.calTable = newCalTable

        self.vialDebugWindow.hide()
    '''
    '''
    def getDefVals(self):
        # get default flow calibration dictionary
        dictNames = self.sensDicts
        sensNum = self.parent.slave + str(self.vialNum)
        posDicts = [x for x in dictNames if sensNum in x]
        if len(posDicts) == 0:  self.sensDict = defSensorCal;   #self.logger.warning('no calibration files for this sensor')
        if len(posDicts) > 1:   self.sensDict = defSensorCal;   #self.logger.warning('more than one calibration file for this sensor')
        if len(posDicts) == 1: self.sensDict = posDicts[0]

        # get default flow control values
        slaveVars = self.defVals
        for key in keysToGet:
            keyStr = 'self.' + key
            exec(keyStr + '=slaveVars.get(key)')
    '''
    # CREATE BOXES
    def createVialSettingsBox(self):
        self.vialSettingsBox = QGroupBox("vial settings")

        self.recBox = QCheckBox(checkable=True,checked=True)
        self.sensDictBox = QComboBox()
        self.sensDictBox.addItems(self.sensDicts)
        self.sensDictBox.setCurrentText(self.sensDict)
        self.sensDictBox.setEnabled(False)
        self.sensDictBtn = QPushButton(text="Edit",checkable=True)
        
        layout = QFormLayout()
        layout.addRow(QLabel(text="Record to file:"),self.recBox)
        layout.addRow(QLabel("Sensor Calibration Table:"))
        layout.addRow(self.sensDictBox,self.sensDictBtn)
        self.vialSettingsBox.setLayout(layout)
        self.sensDictBtn.clicked.connect(self.clicked_sensDictEdit)

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
        VlEnter = QLineEdit(text=str(defVl), maximumWidth=lineEditWidth, returnPressed=lambda: self.sendP('OV',VlEnter.text()))
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
    
    '''
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
    '''
    
    
    # ACCESSED BY EXTERNAL THINGS
    '''
    def changeMode(self, newMode):
        if self.mode == newMode:
            x=1
            #self.logger.info('same mode as previous')
        
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
    '''
    def appendNew(self, value):
        flowValue = value[0:4]
        ctrlValue = value[5:8]

        flowVal = int(flowValue)
        sccmVal = utils.convertToSCCM(flowVal, self.intToSccm_dict)
        
        dataStr = str(flowValue) + '\t' + str(sccmVal) + '\t' + str(ctrlValue)
        self.dataReceiveBox.append(dataStr)


class Slave(QGroupBox):

    def __init__(self, parent, slaveName, numVials, vialConfig):
        super().__init__()
        self.parent = parent
        self.slaveName = slaveName
        self.numVials = numVials
        #self.vialConfig = vialConfig

        self.layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(QLabel('Vial'))
        layout1.addWidget(QLabel('calibration table'))
        layout1.addWidget(QLabel('Setpoint'))
        layout1.addWidget(QLabel('send'))
        layout1.addWidget(QLabel('__'))
        #self.layout.addLayout(layout1)

        # but you have to get this from config file instead - not the arduino config
        for key in keysToGet:
            keyStr = 'self.' + key
            exec(keyStr + '=vialConfig.get(key)')


        self.vials = []
        for x in range(numVials):
            v_vialNum = x+1
            v_odor = 'pinene'
            v_sensType = sensorTypes[0]
            v_calTable = list(self.parent.ard2Sccm_dicts.keys())[0]

            v_vial = Vial(self,vialNum=v_vialNum,calTable=v_calTable, setpoint=defSp, Kp=self.defKp, Ki=self.defKi, Kd=self.defKd)
            
            self.vials.append(v_vial)
            v_layout = QHBoxLayout()
            v_layout.addWidget(self.vials[x].OVcheckbox)
            v_layout.addWidget(self.vials[x].mainBtn)
            v_layout.addWidget(self.vials[x].calTable_widget)
            v_layout.addWidget(self.vials[x].setpoint_widget)
            v_layout.addWidget(self.vials[x].setpoint_sendBtn)
            v_layout.addWidget(self.vials[x].vialDebugBtn)
            
            self.layout.addLayout(v_layout)
        
        self.setTitle("Slave " + self.slaveName)
        self.setLayout(self.layout)



class OlfactometerConfigWindow(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.generate_ui()
        self.hide()

    def generate_ui(self):
        self.setWindowTitle('Olfactometer Configuration')

        self.apply_button = QPushButton('Apply')

        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.apply_button, 2, 0)



class openValveTimer(QWidget):
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.generate_ui()
        self.hide()

        self.duration = 1

    def generate_ui(self):
        self.setWindowTitle('open vial timer')

        self.theTimer = QTimer()
        self.theTimer.timeout.connect(self.show_time)
        
        self.timeLabel = QLabel()
        self.valveTimeLabel = QLabel()
        self.stopBtn = QPushButton('Close valves early')
        self.stopBtn.clicked.connect(self.end_early)

        layout = QFormLayout()
        layout.addRow(QLabel('Current time:'), self.timeLabel)
        layout.addRow(QLabel('time since valves were opened:'),self.valveTimeLabel)
        layout.addRow(self.stopBtn)
        self.setLayout(layout)
        
    def show_time(self):
        curTime = datetime.now()
        
        curValveDur = curTime - self.valveOpenTime
        if curValveDur >= self.valve_open_duration:
            self.end_timer()
            
        curTimeDisplay = curTime.strftime("%H:%M:%S.%f")
        curTimeDisplay = curTimeDisplay[:-3]
        self.timeLabel.setText(curTimeDisplay)

        valveDurDisplay = str(curValveDur)
        self.valveTimeLabel.setText(valveDurDisplay)

    def start_timer(self):
        self.valveOpenTime = datetime.now()
        self.valve_open_duration = timedelta(0, self.duration)
        
        updateFrequency = 50
        self.theTimer.start(updateFrequency)
    
    def end_early(self):
        self.theTimer.stop()
        self.parent.closeVials()
        self.hide()

    def end_timer(self):
        self.theTimer.stop()
        self.parent.timer_finished()
        self.hide()


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
                # create list of values
                values = []
                i = self.minSp
                while i < self.maxSp:
                    for n in range(self.numRuns):   values.append(i)
                    i += self.incSp
                if self.spOrder == 'Random':    random.shuffle(values)
                
                for j in values:
                    sccmVal = j
                    if self.threadON == True:
                        self.w_sendThisSp.emit(slaveToRun,vialToRun,sccmVal);   time.sleep(waitBtSpAndOV)
                        self.w_send_OpenValve.emit(slaveToRun,vialToRun,self.dur_ON);       time.sleep(self.dur_ON)
                        time.sleep(self.dur_OFF-waitBtSpAndOV)
                        idx = values.index(j) + 1
                        progBarVal = int( (idx/len(values)) *100 )
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
        
        self.calibrationON = False
        
        # Make Logger
        self.className = type(self).__name__
        loggerName = self.className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)
        self.logger.debug('Creating %s', loggerName)
        self.logger.debug('made logger')

        # Load Flow Calibration Tables
        defFlowCal = utils.findOlfaConfigFolder() + '\calibration_tables'
        self.flowCalDir = defFlowCal
        self.load_flowCal_files()
        
        # Load Olfa Config Files
        defOlfaConfig = utils.findOlfaConfigFolder() + '\olfactometer'
        self.olfaConfigDir = defOlfaConfig
        self.load_olfaConf_files()
        
        # Create worker thread
        self.obj = worker()
        self.thread1 = QThread()
        self.obj.moveToThread(self.thread1)
        self.setUpThreads()

        # Create UI
        self.generate_ui()
        
        self.setTitle(self.className + ':' + self.name)
        
        self.connectButton.setChecked(False)
        self.refreshButton.setEnabled(True)
        self.portWidget.setEnabled(True)
        self.masterBox.setEnabled(False)
        self.programStartButton.setEnabled(False)
        for s in self.slaves:
            s.setEnabled(False)
    
        self.logger.info('done making olfactometer')

    
    def generate_ui(self):
        self.createSourceFileBox()
        self.createSlaveGroupBox()  # need to make this before vial programming box

        self.createConnectBox()

        self.createMasterBox()
        self.createCalibrationBox()
        #self.createFlowSettingsBox()
        self.createVialProgrammingBox()
        self.createBottomGroupBox()

        self.timer_for_openVials = openValveTimer(self)
        
        self.mainLayout = QGridLayout()

        self.mainLayout.addWidget(self.sourceFileBox, 0, 0, 1, 1)
        self.mainLayout.addWidget(self.connectBox, 1, 0, 4, 1)
        
        self.mainLayout.addWidget(self.masterBox, 0, 1, 1, 1)
        self.mainLayout.addWidget(self.calibrationBox, 1, 1, 1, 1)
        self.mainLayout.addWidget(self.vialProgrammingBox, 2, 1, 3, 1)
        col2w = self.vialProgrammingBox.sizeHint().width()
        self.masterBox.setMaximumWidth(col2w)
        self.calibrationBox.setMaximumWidth(col2w)
        self.vialProgrammingBox.setMaximumWidth(col2w)
        
        self.mainLayout.addWidget(self.slaveGroupBox, 0, 2, 4, 1)
        self.mainLayout.addWidget(self.bottomGroupBox, 4, 2, 1, 1)

        self.setLayout(self.mainLayout)
        
        if vialProgrammingOn == True:   self.vialProgrammingBox.setEnabled(True)
        if vialProgrammingOn == False:  self.vialProgrammingBox.setEnabled(False)

    def load_flowCal_files(self):
        self.logger.debug('getting flow sensor calibration files from %s',self.flowCalDir)
        os.chdir(self.flowCalDir)

        # GET ALL CALIBRATION TABLES
        self.cal_sheets = [];    # dictionary names
        self.sccm2Ard_dicts = {}
        self.ard2Sccm_dicts = {}
        files = os.listdir()
        # get both dictionaries for each file in this folder **** dictionaries must be in order
        for calFile in files:
            idx_ext = calFile.find('.')
            calFileName = calFile[:idx_ext]
            self.cal_sheets.append(calFileName)
            sccm2Ard = {}
            ard2Sccm = {}
            with open(calFile,newline='') as f:
                csv_reader = csv.reader(f)
                firstLine = next(csv_reader)
                reader = csv.DictReader(f,delimiter=',')
                for row in reader:
                    sccm2Ard[int(row['SCCM'])] = int(row['int'])
                    ard2Sccm[int(row['int'])] = int(row['SCCM'])
            self.sccm2Ard_dicts[calFileName] = sccm2Ard
            self.ard2Sccm_dicts[calFileName] = ard2Sccm        
    
    def load_olfaConf_files(self):
        # VARIABLES FROM MASTER CONFIG FILE
        self.ardConfig_m = utils.getArduinoConfigFile(self.olfaConfigDir + '/' + arduinoMasterConfigFile)
        self.baudrate = int(self.ardConfig_m.get('baudrate'))   # need to connect
        
        # need to make slaves
        self.numSlaves = int(self.ardConfig_m.get('numSlaves'))
        self.slaveNames = self.ardConfig_m.get('slaveNames[numSlaves]')
        self.vPSlave = self.ardConfig_m.get('vialsPerSlave[numSlaves]')

        self.defTimebt = self.ardConfig_m.get('timeBetweenRequests')
        # VARIABLES FROM SLAVE CONFIG FILE
        self.ardConfig_s = utils.getArduinoConfigFile(self.olfaConfigDir + '/' + arduinoSlaveConfigFile)

    
    # CONNECT TO DEVICE
    def createConnectBox(self):
        self.connectBox = QGroupBox("Connect")

        self.portWidget = QComboBox(currentIndexChanged=self.portChanged)
        self.connectButton = QPushButton(checkable=True,toggled=self.toggled_connect)
        self.refreshButton = QPushButton(text="Refresh",clicked=self.getPorts)

        self.rawReadDisplay = QTextEdit(readOnly=True)
        readLayout = QVBoxLayout()
        readLayout.addWidget(QLabel('raw data from serial port:'))
        readLayout.addWidget(self.rawReadDisplay)
        
        self.rawWriteDisplay = QTextEdit(readOnly=True)
        writeLayout = QVBoxLayout()
        writeLayout.addWidget(QLabel('wrote to serial port:'))
        writeLayout.addWidget(self.rawWriteDisplay)
        
        receive_space = QHBoxLayout()
        receive_space.addLayout(readLayout)
        receive_space.addLayout(writeLayout)
        
        self.connectBoxLayout = QFormLayout()
        self.connectBoxLayout.addRow(QLabel(text="Port/Device:"),self.portWidget)
        self.connectBoxLayout.addRow(self.refreshButton,self.connectButton)
        self.connectBoxLayout.addRow(receive_space)
        self.connectBox.setLayout(self.connectBoxLayout)
        self.getPorts()

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
    

    # OLFACTOMETER-SPECIFIC FUNCTIONS
    def createSourceFileBox(self):
        self.sourceFileBox = QGroupBox("Source Files")
        
        self.flowCalLbl = QLabel(text="flow sensor calibration tables:",toolTip="conversion from int to sccm")
        self.flowCalLineEdit = QLineEdit(text=self.flowCalDir)
        self.flowCalEditBtn = QPushButton("Edit",clicked=self.changeFlowCalDir)
        self.flowCalEditBtn.setFixedWidth(lineEditWidth)
        
        self.olfaConfLbl = QLabel(text="olfactometer config files:",
                                    toolTip='# of slaves (& slave names), vials/slave, baudrate (config_master.h)\ndefault setpoint,etc (config_slave.h)')
        self.olfaConfLineEdit = QLineEdit(text=self.olfaConfigDir,
                                            toolTip="config_master.h: # of slaves (& slave names), vials/slave, baudrate\nconfig_slave.h: default setpoint")
        self.olfaConfEditBtn = QPushButton("Edit",clicked=self.changeOlfaConfigDir)
        self.olfaConfEditBtn.setFixedWidth(lineEditWidth)
        #self.updateLineEditWidth()

        self.olfactometer_config_ui = OlfactometerConfigWindow(self)

        self.manualEditBtn = QPushButton('Edit olfa configuration')
        self.manualEditBtn.clicked.connect(lambda: self.olfactometer_config_ui.show())

        self.load_olfa_config_Btn = QPushButton('Load olfa config file')
        self.save_olfa_config_Btn = QPushButton('Save this olfa config')
        self.save_olfa_config_Btn.clicked.connect(self.generate_config_file)

        layout = QFormLayout()
        layout.addRow(self.flowCalLbl)
        layout.addRow(self.flowCalLineEdit,self.flowCalEditBtn)
        layout.addRow(self.olfaConfLbl)
        layout.addRow(self.olfaConfLineEdit,self.olfaConfEditBtn)
        layout.addRow(self.load_olfa_config_Btn,self.save_olfa_config_Btn)
        self.sourceFileBox.setLayout(layout)        
    
    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        timeBtReqBox = QLineEdit(text=self.defTimebt,returnPressed=lambda:self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendParameter('M','M','timebt',timeBtReqBox.text()))
        
        self.manualCmdBox = QLineEdit(text=defManualCmd,returnPressed=self.sendManualParameter)
        manualCmdBtn = QPushButton(text="Send",clicked=self.sendManualParameter)

        layout = QFormLayout()
        layout.addRow(QLabel(text="Time b/t requests for slave data (ms):"))
        layout.addRow(timeBtReqBox,timeBtButton)
        layout.addRow(QLabel(text="Manually send command:"))
        layout.addRow(self.manualCmdBox,manualCmdBtn)
        self.masterBox.setLayout(layout)
    
    def createCalibrationBox(self):
        self.calibrationBox = QGroupBox("Flow Sensor Calibration")

        self.calVial = QComboBox()
        for s in self.slaves:
            for v in s.vials:
                #slaveNum = v.name
                #slaveNum = v.slave + str(v.vialNum)
                self.calVial.addItem(v.name)
        self.calFile = QLineEdit(text=self.calVial.currentText() + '_' + currentDate)
        self.calStartBtn = QPushButton(text="Start",checkable=True)
        
        self.c_pgm_box = QGroupBox()
        lbl = QLabel("Set MFC to: ")
        self.calValueLbl = QLabel(text=str(calValue))
        self.c_pgm_start = QPushButton(text="Go")
        self.c_pgm_progBar = QProgressBar()
        layout2 = QFormLayout()
        layout2.addRow(lbl,self.calValueLbl)
        
        layout = QFormLayout()
        layout.addRow(QLabel("Sensor to calibrate:"),self.calVial)
        layout.addRow(QLabel("New calibration file:"),self.calFile)
        layout.addRow(self.calStartBtn)
        layout.addRow(self.c_pgm_box)
        self.calibrationBox.setLayout(layout)

        self.calStartBtn.clicked.connect(self.startCalibration)
    
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
        self.slaveGroupBox = QGroupBox('Slave Devices')

        allSlaves_layout = QVBoxLayout()
        self.slaves = []
        for i in range(self.numSlaves):
            s_slaveName = self.slaveNames[i]
            s_vPSlave = int(self.vPSlave[i])
            self.logger.debug('Creating slave ' + s_slaveName + ' (' + str(s_vPSlave) + ' vials)')
            s_slave = Slave(self, s_slaveName, s_vPSlave, self.ardConfig_s)
            self.slaves.append(s_slave)
            allSlaves_layout.addWidget(s_slave)
        
        allSlavesWidget = QWidget()
        allSlavesWidget.setLayout(allSlaves_layout)

        slaveScrollArea = QScrollArea()
        slaveScrollArea.setWidget(allSlavesWidget)
        slaveScrollArea.setWidgetResizable(True)

        slaveGroupBox_layout = QVBoxLayout()
        slaveGroupBox_layout.addWidget(slaveScrollArea)
        self.slaveGroupBox.setLayout(slaveGroupBox_layout)
    
    def createBottomGroupBox(self):
        self.bottomGroupBox = QGroupBox()

        self.durONBox = QSpinBox(value=defVl)
        self.OVbutton = QPushButton('Open Checked Vials')
        self.OVbutton.clicked.connect(self.openVials)

        self.setpointBox = QSpinBox(maximum=maxSp,value=defSp)
        self.spBtn = QPushButton(text='Update Setpoint for Checked Vials',toolTip='This will only work if selected vials have the same calibration table')
        # later: check which have same calibration table, then send in groups
        self.spBtn.clicked.connect(self.changeSetpoint)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Change Setpoint:'))
        row1.addWidget(self.setpointBox)
        row1.addWidget(self.spBtn)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel('Duration open:'))
        row2.addWidget(self.durONBox)
        row2.addWidget(self.OVbutton)

        layout = QVBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.bottomGroupBox.setLayout(layout)
    
    
    def generate_config_file(self):
        self.logger.debug('generating config file')
        
        self.config_info = {}
        for s in self.slaves:
            vial_contents = {}
            for v in s.vials:
                vial_contents[v.vialNum] = dict(calTable=v.calTable,setpoint=v.setpoint,Kp=v.Kp,Ki=v.Ki,Kd=v.Kd)
            self.config_info[s.slaveName] = vial_contents

        self.save_config_file()

    def save_config_file(self):
        self.logger.debug('save config file')

        fn = QFileDialog.getSaveFileName(self, 'Save File')
        if fn:
            try:
                with open(fn[0], 'wt') as json_file:
                    json.dump(self.config_info, json_file)
                    self.logger.info('saved new config file')
            except IOError as ioe:
                self.logger.info('Could not save config file: %s', ioe)

            



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
        self.p_spMax = QSpinBox(maximum=maxSp,value=defSp)
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

        self.p_additiveSelect.currentIndexChanged.connect(self.additive_changed)
        self.p_additiveSelect.currentIndexChanged.connect(self.updateProgDurLabel)
        self.additive_changed()
        self.p_spType.currentIndexChanged.connect(self.spType_changed)
        self.p_spType.currentIndexChanged.connect(self.updateProgDurLabel)
        self.spType_changed()
        self.p_spMin.valueChanged.connect(self.updateProgDurLabel)
        self.p_spMax.valueChanged.connect(self.updateProgDurLabel)
        self.p_spInc.valueChanged.connect(self.updateProgDurLabel)
        self.p_durON.valueChanged.connect(self.updateProgDurLabel)
        self.p_durOFF.valueChanged.connect(self.updateProgDurLabel)
        self.p_numRuns.valueChanged.connect(self.updateProgDurLabel)
        self.updateProgDurLabel()
    
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
            self.logger.info('Starting program')
            self.thread1.start()
            
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

    def send_OpenValve(self, slave:str, vial:int, dur:int):
        self.sendParameter(slave,vial,'OV',str(dur))

    def threadIsFinished(self):
        self.obj.threadON = False
        self.thread1.exit()
        self.programStartButton.setChecked(False);  self.programStartButton.setText('Start')
        self.progSettingsBox.setEnabled(True)
        self.logger.info('Finished program')
        self.progBar.setValue(0)

    def changeSetpoint(self):
        self.logger.warning('all lines are sent the same int value regardless of calibration table')
        # get vial string
        self.vialStr = ''
        for s in self.slaves:
            thisSlaveStr = s.slaveName
            for v in s.vials:
                if v.OVcheckbox.isChecked():
                    thisSlaveStr = thisSlaveStr + str(v.vialNum)
            if len(thisSlaveStr) > 1:
                self.vialStr = self.vialStr + thisSlaveStr

        if len(self.vialStr) == 0:   self.logger.warning('no lines selected - select checkboxes and try again')
        else:
            param = 'Sp'
            value = '500'   # get the value from the spinbox
            self.logger.warning('set to 500 for now (will fix to get from spinbox later)')

            str_send = param + '_' + value + '_' + self.vialStr
            self.sendThisArray(str_send)

    def openVials(self):
        # get vial string
        self.vialStr = ''
        for s in self.slaves:
            thisSlaveStr = s.slaveName
            for v in s.vials:
                if v.OVcheckbox.isChecked():
                    thisSlaveStr = thisSlaveStr + str(v.vialNum)
                    v.mainBtn.setChecked(True)
                    self.logger.debug('set %s mainBtn to checked', v.name)
            if len(thisSlaveStr) > 1:
                self.vialStr = self.vialStr + thisSlaveStr

        if len(self.vialStr) == 0:   self.logger.info('no vials selected')
        else:
            param = 'OV'
            value = '5'        
            str_send = param + '_' + value + '_' + self.vialStr
            self.sendThisArray(str_send)

            self.timer_for_openVials.show()
            self.timer_for_openVials.duration = 5
            self.timer_for_openVials.start_timer()
            #self.logger.info('started the timer')

    def sendThisArray(self, strToSend):
        strToSend = 'S_' + strToSend
        bArr_send = strToSend.encode()
        try:
            if self.serial.isOpen():
                self.serial.write(bArr_send)
                self.logger.info("sent to %s: %s", self.port, strToSend)
                self.rawWriteDisplay.append(strToSend)
            else:
                self.logger.warning('Serial port not open, cannot send parameter: %s', strToSend)
        except AttributeError as err:
            self.logger.warning('Serial port not open, cannot send parameter: %s', strToSend)        
    
    def closeVials(self):
        self.logger.info('valves closed early by user')
        
        param = 'CV'
        value = '0'
        str_send = param + '_' + value + '_' + self.vialStr
        self.sendThisArray(str_send)

        self.timer_finished()
    
    def timer_finished(self):
        self.logger.debug('timer finished')
        for s in self.slaves:
            for v in s.vials:
                if v.mainBtn.isChecked():
                    v.mainBtn.setChecked(False)

    
    
    # INTERFACE FUNCTIONS
    def updateLineEditWidth(self):
        fm_c = self.olfaConfLineEdit.fontMetrics()
        w_c = fm_c.boundingRect(self.olfaConfLineEdit.text()).width()
        w_c = w_c - 50
        self.olfaConfLineEdit.setMinimumWidth(w_c)
        self.flowCalLineEdit.setMinimumWidth(w_c)
    
    def changeFlowCalDir(self):
        prev_flowDir = self.flowCalLineEdit.text()
        prev_flowDir_url = QtCore.QUrl(prev_flowDir)
        prev_flowDir_url.setScheme("File")

        new_flowDir_url = QFileDialog.getExistingDirectoryUrl(self,'Select Folder',prev_flowDir_url)
        new_flowDir = new_flowDir_url.toString()
        new_flowDir = new_flowDir[8:]
        if new_flowDir == '':   self.flowCalDir = prev_flowDir  # if user clicked cancel
        else:
            if new_flowDir != self.flowCalDir:
                self.flowCalDir = new_flowDir
                self.load_flowCal_files()
                #self.getFlowCalFiles()          # get new files
                # update the vials with the new flow cal options
                self.logger.warning('does not update vials - unfinished')
                self.logger.info('finished updating flow cal tables')

        self.flowCalLineEdit.setText(self.flowCalDir)
        
    def changeOlfaConfigDir(self):
        prev_olfaDir = self.olfaConfLineEdit.text()        
        
        prev_olfaDir_url = QtCore.QUrl(prev_olfaDir)        # use URL so that cancel button doesn't give error
        prev_olfaDir_url.setScheme("file")                  # so we don't get warning
        new_olfaConfigDir_url = QFileDialog.getExistingDirectoryUrl(self,
                                                                caption='Select Folder (for olfactometer calibration files)',
                                                                directory=prev_olfaDir_url)
        new_olfaConfigDir = new_olfaConfigDir_url.toString()
        new_olfaConfigDir = new_olfaConfigDir[8:]         # cut out the scheme part
        if new_olfaConfigDir == '': self.olfaConfigDir = prev_olfaDir   # if user clicked cancel, use previous directory
        else:
            if new_olfaConfigDir != self.olfaConfigDir:
                self.olfaConfigDir = new_olfaConfigDir
                self.load_olfaConf_files()
                #self.getOlfaConfigVars()                # get new variables
                w = self.mainLayout.itemAt(self.mainLayout.count()-1).widget()  # remove old slave groupbox
                self.mainLayout.removeWidget(w)
                sip.delete(w)
                self.createSlaveGroupBox()              # make the new slaves
                self.mainLayout.addWidget(self.slaveGroupBox)
                self.logger.info('finished updating vials')

        self.olfaConfLineEdit.setText(self.olfaConfigDir)
    
    def setConnected(self, connected):
        if connected == True:
            self.connectButton.setText('Stop communication w/ ' + self.portStr)
            self.refreshButton.setEnabled(False)
            self.portWidget.setEnabled(False)
            self.masterBox.setEnabled(True)
            self.programStartButton.setEnabled(True)
            for s in self.slaves:
                s.setEnabled(True)
        else:
            self.connectButton.setText('Connect to ' + self.portStr)
            self.connectButton.setChecked(False)
            self.refreshButton.setEnabled(True)
            self.portWidget.setEnabled(True)
            self.masterBox.setEnabled(False)
            self.programStartButton.setEnabled(False)
            for s in self.slaves:
                s.setEnabled(False)
    
    def updateMode(self):
        self.mode = self.modeCb.currentText()

        for s in self.slaves:
            for v in s.vials:
                if self.mode == 'auto': 
                    v.changeMode('auto')
                if self.mode == 'manual':
                    v.changeMode('manual')
            s.resize(s.sizeHint())
        #self.allSlavesWid.resize(self.allSlavesWid.sizeHint())
        #self.slaveScrollArea.resize(self.slaveScrollArea.sizeHint())
        #self.slaveGroupBox.resize(self.slaveGroupBox.sizeHint())
        #self.resize(self.sizeHint())
        #widget_width = self.slaves[0].width()
        #widget_height = self.slaves[0].height() + self.slaves[1].height()
    

    # VIAL PROGRAMMING INTERFACE
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
            self.p_sp.setEnabled(True)
            self.p_sp2.setEnabled(False)
        if currentText == 'Varied':
            self.p_spOrder.setEnabled(True)
            self.p_sp.setEnabled(False)
            self.p_sp2.setEnabled(True)
    
    def updateProgDurLabel(self):
        # still not done for additive

        numRuns = self.p_numRuns.value()
        durON = self.p_durON.value()
        durOFF = self.p_durOFF.value()

        if self.p_spType.currentText() == 'Constant':
            numValues = numRuns
        if self.p_spType.currentText() == 'Varied':
            values = []
            i = self.p_spMin.value()
            while i < self.p_spMax.value():
                for n in range(numRuns):    values.append(i)
                i += self.p_spInc.value()
            numValues = len(values)
        totalDur = (durON+durOFF)*numValues
        totalDur_min = int(totalDur/60)
        totalDur_sec = totalDur%60
        
        #self.progDurLbl.setText(str(totalDur) + " seconds --> " + str(totalDur_min) + " min, " + str(totalDur_sec) + " sec")
        self.progDurLbl.setText(str(totalDur_min) + " min, " + str(totalDur_sec) + " sec")
    
    def incProgBar(self, val):
        self.progBar.setValue(val)
    

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
                        for s in self.slaves:
                            for v in s.vials:
                                if v.name == vialInfo:
                                    #try:
                                    v.appendNew(dataValue)

                                    #for i in range(self.numSlaves):
                                    #    if self.slaves[i].slaveName == vialInfo[0]: s_index = i
                                    #v_index = int(vialInfo[1])-1
                                    '''
                                    try:
                                        self.slaves[s_index].vials[v_index].appendNew(dataValue)
                                        #recordOn =  self.slaves[s_index].vials[v_index].recBox.isChecked()
                                        flowVal = dataValue[0:4]
                                        ctrlVal = dataValue[5:8]
                                        if self.window().recordButton.isChecked():  # if main window recording is on
                                            
                                            #if recordOn:    # if recording to this vial is on
                                            #    instrument = self.name + ' ' + str(vialInfo)
                                            #    unit = 'FL'
                                            #    value = flowVal
                                            #    self.window().receiveDataFromChannels(instrument,unit,value)
                                            
                                        if self.calibrationON == True:
                                            self.vialReceiveValues.append(int(flowVal))
                                            if len(self.vialReceiveValues) >= 500:
                                                self.logger.info('Finished calibration of %s', self.vialToCalibrate)
                                                meanInt = numpy.mean(self.vialReceiveValues)
                                    '''

                                    #except IndexError as err:
                                    #    self.logger.error('arduino master config file does not include vial %s', vialInfo)
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
    
    def startCalibration(self):
        self.masterBox.setEnabled(False)
        self.vialProgrammingBox.setEnabled(False)
        for s in self.slaves:
            s.setEnabled(False)
        
        self.vialToCalibrate = self.calVial.currentText()
        slaveToCal = self.vialToCalibrate[0]
        vialToCal = self.vialToCalibrate[1]
        self.vialReceiveValues = []
        self.calibrationON = True
        
        # save the values received for this vial

