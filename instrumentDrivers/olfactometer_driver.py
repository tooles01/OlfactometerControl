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
#from pyqtgraph.parametertree import Parameter, ParameterTree

currentDate = utils.currentDate
calValue = 100

delimChar = ','


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

### FOR DEBUGGING
debugON = False

if debugON == True:
    vialProgrammingOn = True
    slavesActive = True
else:
    vialProgrammingOn = False
    slavesActive = False


olfaConfigFile = 'configFile.json'

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
'''
class calibration_worker(QObject):

    def _init__(self):
'''

class openValveTimer(QWidget):
    
    def __init__(self, parent, name=""):
        super().__init__()
        self.parent = parent
        self.name = name
        self.generate_ui()
        self.hide()

        self.duration = 1

    def generate_ui(self):
        if self.name:   self.setWindowTitle('open vial timer for ' + str(self.name))
        else:           self.setWindowTitle('open vial timer')

        self.theTimer = QTimer()
        self.theTimer.timeout.connect(self.show_time)
        
        #self.timeLabel = QLabel()
        self.valveTimeLabel = QLabel()
        self.stopBtn = QPushButton(text='Close valve', clicked=self.end_early)

        layout = QFormLayout()
        #layout.addRow(QLabel('Current time:'), self.timeLabel)
        layout.addRow(QLabel('time since valve open:'),self.valveTimeLabel)
        layout.addRow(self.stopBtn)
        self.setLayout(layout)
        
    def show_time(self):
        curTime = datetime.now()
        curValveDur = curTime - self.valveOpenTime
        if curValveDur >= self.valve_open_duration:
            self.end_timer()
        
        #curTimeDisplay = curTime.strftime("%H:%M:%S.%f")
        #curTimeDisplay = curTimeDisplay[:-3]
        #self.timeLabel.setText(curTimeDisplay)
        valveDurDisplay = str(curValveDur)
        self.valveTimeLabel.setText(valveDurDisplay)

    def start_timer(self):
        self.valveOpenTime = datetime.now()
        self.valve_open_duration = timedelta(0, self.duration)
        
        updateFrequency = 50
        self.theTimer.start(updateFrequency)
    
    def end_early(self):
        self.theTimer.stop()
        self.hide()
        self.parent.closeVials()

    def end_timer(self):
        self.theTimer.stop()
        self.hide()
        self.parent.timer_finished()


'''
class OlfactometerConfigWindow(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.generate_ui()
        self.hide()

    def generate_ui(self):
        self.setWindowTitle('Olfa Configuration')

        self.main_layout = QGridLayout()
        #self.apply_button = QPushButton('Apply')
        #self.main_layout.addWidget(self.apply_button, 2, 0)
        
        self.olfactometer_conf_tree = ParameterTree(showHeader=True)
        self.main_layout.addWidget(self.olfactometer_conf_tree, 0, 0, 1, 3)

        self.apply_button = QPushButton('Apply')
        #self.apply_button.clicked.connect(self.apply_configuration)
        self.save_button = QPushButton('Save')
        #self.save_button.clicked.connect(self.save_configuration)
        self.load_button = QPushButton('Load')
        #self.load_button.clicked.connect(self.load_configuration)
        self.main_layout.addWidget(self.apply_button, 1, 0)
        self.main_layout.addWidget(self.save_button, 1, 1)
        self.main_layout.addWidget(self.load_button, 1, 2)

        self.setLayout(self.main_layout)
        #self.resize(QtCore.QSize(600, 800))
        #self.update_config_display()
'''


class Vial(QObject):

    def __init__(self, parent, vialNum):
        super().__init__()
        self.parent = parent
        self.vialNum = vialNum  # TODO: delete this

        self.name = self.parent.slaveName + str(self.vialNum)
        
        self.config = self.parent.vialConfig.get(vialNum)
        self.load_stuff()
        
        self.generate_ui_features()

        
    def load_stuff(self):
        # load stuff from olfactometer
        self.calTable = self.config['calTable']

        # things that matter to the Arduino
        self.setpoint = self.config['setpoint']
        self.Kp = self.config['Kp']
        self.Ki = self.config['Ki']
        self.Kd = self.config['Kd']
        self.mode = self.config['mode']

        self.intToSccm_dict = self.parent.parent.ard2Sccm_dicts.get(self.calTable)
        self.sccmToInt_dict = self.parent.parent.sccm2Ard_dicts.get(self.calTable)
        

    # UI
    def generate_ui_features(self):
        self.OVcheckbox = QCheckBox(checkable=True, checked=False, toolTip='Apply update to this vial')

        self.viewFlowBtn = QPushButton(text='View Flow', checkable=True, toolTip='read flow values from this vial')
        if self.mode == 'normal':   self.viewFlowBtn.setChecked(False)
        if self.mode == 'debug':    self.viewFlowBtn.setChecked(True)
        self.viewFlowBtn.toggled.connect(self.vial_debug_toggled)

        self.mainBtn = QPushButton(text=self.name, checkable=True, toolTip='Open vial for 5s')
        self.mainBtn.clicked.connect(lambda: self.open_vial(defVl))

        self.openVialTimer = openValveTimer(self, self.name)
        
        self.create_vial_debug_window()
        self.create_vial_calibration_window()
        
        self.vialDebugBtn = QPushButton(text='Debug')
        self.vialDebugBtn.clicked.connect(lambda: self.vialDebugWindow.show())

        self.calTable_widget = QComboBox()
        self.calTable_widget.addItems(self.parent.parent.ard2Sccm_dicts)
        self.calTable_widget.currentIndexChanged.connect(lambda: self.new_calTable(self.calTable_widget.currentText()))
        self.calTable_widget.setCurrentText(self.calTable)

        self.setpoint_widget = QSpinBox(maximum=maxSp,value=self.setpoint)
        self.setpoint_sendBtn = QPushButton(text='Send Sp')
        self.setpoint_sendBtn.clicked.connect(lambda: self.update_setpoint(self.setpoint_widget.value()))

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
        self.vialDebugWindow.calTable_wid.setCurrentText(self.calTable) # need to do this before connecting function
        self.vialDebugWindow.calTable_wid.currentIndexChanged.connect(lambda: self.new_calTable(self.vialDebugWindow.calTable_wid.currentText()))
        self.vialDebugWindow.newCalibrationBtn = QPushButton('Calibrate')
        self.vialDebugWindow.newCalibrationBtn.clicked.connect(lambda: self.vialCalibrationWindow.show())
        calibration_layout = QHBoxLayout()
        calibration_layout.addWidget(QLabel('Calibration table:'))
        calibration_layout.addWidget(self.vialDebugWindow.calTable_wid)
        calibration_layout.addWidget(self.vialDebugWindow.newCalibrationBtn)

        # Setpoint
        self.vialDebugWindow.setpoint_wid = QSpinBox(maximum=maxSp,value=self.setpoint)
        self.vialDebugWindow.setpoint_sendBtn = QPushButton('Send Sp')
        self.vialDebugWindow.setpoint_sendBtn.clicked.connect(lambda: self.update_setpoint(self.vialDebugWindow.setpoint_wid.value()))
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

        self.vialDebugWindow.advancedBtn = QPushButton(text="Enable Advanced Options", checkable=True,
                toggled=self.toggled_advanced_settings, toolTip="ARE YOU SURE YOU WANT TO DO THIS")
            
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
        self.vialDebugWindow.PIDToggle = QPushButton(text="Turn flow control on", checkable=True, toggled=self.toggled_PID)
        self.vialDebugWindow.CtrlToggle = QPushButton(text="Open prop valve", checkable=True, toggled=self.toggled_ctrlOpen)
        self.vialDebugWindow.VlToggle = QPushButton(text="Open Iso Valve", checkable=True, toggled=self.toggled_valveOpen)
        manualDebug_layout = QVBoxLayout()
        manualDebug_layout.addWidget(self.vialDebugWindow.PIDToggle)
        manualDebug_layout.addWidget(self.vialDebugWindow.CtrlToggle)
        manualDebug_layout.addWidget(self.vialDebugWindow.VlToggle)
        self.manualDebugBox.setLayout(manualDebug_layout)

        layout1 = QFormLayout()
        layout1.addRow(calibration_layout)
        layout1.addRow(setpoint_layout)
        layout1.addRow(openValve_layout)
        layout1.addRow(self.vialDebugWindow.advancedBtn)
        layout1.addRow(self.flowControlBox)
        layout1.addRow(self.manualDebugBox)
        
        # Values received
        self.dataReceiveLbl = QLabel("Flow val (int), Flow (SCCM), Ctrl val (int)")
        self.dataReceiveBox = QTextEdit(readOnly=True)
        
        layout2 = QVBoxLayout()
        layout2.addWidget(self.dataReceiveLbl)
        layout2.addWidget(self.dataReceiveBox)

        self.vialInfoWindow_layout = QHBoxLayout()
        self.vialInfoWindow_layout.addLayout(layout1)
        self.vialInfoWindow_layout.addLayout(layout2)
        self.vialDebugWindow.setLayout(self.vialInfoWindow_layout)

        self.flowControlBox.setEnabled(False)
        self.manualDebugBox.setEnabled(False)
        
        self.vialDebugWindow.hide()
    
    def vial_debug_toggled(self, checked):
        # TODO: change the name of this
        if checked:
            self.mode = 'debug'
            self.viewFlowBtn.setText('Stop reading flow values')
            strToSend = 'MS_debug_' + self.name
            self.parent.parent.sendParameter(strToSend)

        else:
            self.mode = 'normal'
            self.viewFlowBtn.setText('View Flow')
            strToSend = 'MS_normal_' + self.name
            self.parent.parent.sendParameter(strToSend)

    def toggled_advanced_settings(self, checked):
        if checked:
            self.parent.parent.logger.warning('advanced flow control settings are turned on')
            self.flowControlBox.setEnabled(True)
            self.manualDebugBox.setEnabled(True)
            self.vialDebugWindow.advancedBtn.setText('Disable Advanced Options')
        else:
            self.flowControlBox.setEnabled(False)
            self.manualDebugBox.setEnabled(False)
            self.vialDebugWindow.advancedBtn.setText('Enable Advanced Options')


    # VIAL CALIBRATION
    def create_vial_calibration_window(self):
        self.vialCalibrationWindow = QWidget()
        self.vialCalibrationWindow.setWindowTitle('Calibrate flow sensor for ' + self.name)

        calFile_name = self.name + '_' + currentDate
        self.vialCalibrationWindow.calFile_name_wid = QLineEdit(text=calFile_name)

        self.vialCalibrationWindow.startBtn = QPushButton('Start')
        self.vialCalibrationWindow.startBtn.clicked.connect(self.start_calibration)

        box1 = QGroupBox('Settings')
        layout1 = QFormLayout()
        layout1.addRow(QLabel('File name: '), self.vialCalibrationWindow.calFile_name_wid)
        layout1.addRow(self.vialCalibrationWindow.startBtn)
        box1.setLayout(layout1)
        

        self.vialCalibrationWindow.flowVal_wid = QSpinBox(maximum=200, value=defSp) # this could be dependent on sensor type
        self.vialCalibrationWindow.flowVal_get = QPushButton(text='Calibrate at this flow value', checkable=True, toggled=self.get_these_cal_values)
        #self.cal_worker = calibration_worker()
        
        self.vialCalibrationWindow.box2 = QGroupBox('Calibrate')
        layout2 = QFormLayout()
        layout2.addRow(QLabel('Flow value:'), self.vialCalibrationWindow.flowVal_wid)
        layout2.addRow(self.vialCalibrationWindow.flowVal_get)
        self.vialCalibrationWindow.box2.setLayout(layout2)

        self.vialCalibrationWindow.box2.setEnabled(False)
        

        layout = QVBoxLayout()
        layout.addWidget(box1)
        layout.addWidget(self.vialCalibrationWindow.box2)
        self.vialCalibrationWindow.setLayout(layout)

        self.vialCalibrationWindow.hide()

    def start_calibration(self):
        self.vialCalibrationWindow.box2.setEnabled(True)

        print('create calibration file')

    def get_these_cal_values(self):
        cal_sccmValue = self.vialCalibrationWindow.flowVal_wid.value()
        print('calibration at ' + cal_sccmValue + ' sccm: save to file')
        
        print('collect int values for 5 seconds')

        print('average those values')

        print('save new integer cal value')


    
    

    # UPDATE PARAMETERS
    def new_calTable(self, newCalTable):
        if self.calTable_widget.count() != 0:   # if it's not zero items
            # if it's different than the last one
            if newCalTable != self.calTable:
                self.calTable = newCalTable
                self.intToSccm_dict = self.parent.parent.ard2Sccm_dicts.get(self.calTable)
                self.sccmToInt_dict = self.parent.parent.sccm2Ard_dicts.get(self.calTable)
                print('Vial ' + self.name  + ' new cal table:  '+ self.calTable)

                # since there are two calTable widgets
                if self.calTable_widget.currentText() != self.calTable:
                    self.calTable_widget.setCurrentText(self.calTable)
                if self.vialDebugWindow.calTable_wid.currentText() != self.calTable:
                    self.vialDebugWindow.calTable_wid.setCurrentText(self.calTable)
        
    def update_setpoint(self, sccmVal):
        intVal = utils.convertToInt(sccmVal, self.sccmToInt_dict)
        
        param = 'Sp'
        self.sendP(param, intVal)

        self.setpoint = sccmVal
        
        # since there are two setpoint widgets
        if self.vialDebugWindow.setpoint_wid.value() != self.setpoint:
            self.vialDebugWindow.setpoint_wid.setValue(self.setpoint)
        if self.setpoint_widget.value() != self.setpoint:
            self.setpoint_widget.setValue(self.setpoint)
    
    def open_vial(self, dur=""):
        # get duration
        duration_open = self.vialDebugWindow.openValve_widget.value()
        param = 'OV'

        # send the thing
        self.sendP(param, duration_open)

        # start timer
        self.parent.parent.timer_for_openVials.show()
        self.parent.parent.timer_for_openVials.duration = duration_open
        self.parent.parent.timer_for_openVials.start_timer()
    
    
    # USER ACTION
    def sendP(self, param, value):
        # update variable so it saves
        if param == 'Kp':   self.Kp = value
        if param == 'Ki':   self.Ki = value
        if param == 'Kd':   self.Kd = value

        if param[0] == 'K':
            # slave can receive multiple at a time, but GUI cannot send yet
            if param[1] == 'p': newP = 'P'
            if param[1] == 'i': newP = 'I'
            if param[1] == 'd': newP = 'D'
            param = 'Kx'
            value = newP + str(value)
    
        param = str(param)
        value = str(value)
        vialStr = self.name

        strToSend = param + '_' + value + '_' + vialStr
        self.parent.parent.sendSlaveUpdate(strToSend)

        # TODO: if there is an error in sending. don't update the variable
        

    # DEBUG FUNCTIONS        
    def toggled_PID(self, checked):
        if checked:
            self.sendP('ON', 0)
            self.vialDebugWindow.PIDToggle.setText('Turn flow control off')
        else:
            self.sendP('OF', 0)
            self.vialDebugWindow.PIDToggle.setText('Turn flow control on')

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

    
    # needs to match olfactometer function for openValveTimer
    def closeVials(self):
        param = 'CV'
        value = '0'
        self.sendP(param, value)
        self.timer_finished()
    
    # needs to match olfactometer function for openValveTimer
    def timer_finished(self):
        self.mainBtn.setChecked(False)


    # ACCESSED BY EXTERNAL THINGS
    def appendNew(self, value):
        flowValue = value[0:4]
        ctrlValue = value[5:8]

        flowVal = int(flowValue)
        sccmVal = utils.convertToSCCM(flowVal, self.intToSccm_dict)
        
        dataStr = str(flowValue) + '\t' + str(sccmVal) + '\t' + str(ctrlValue)
        self.dataReceiveBox.append(dataStr)

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
    
    # CREATE BOXES
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
    
    

class Slave(QGroupBox):

    def __init__(self, parent, slaveName):
        super().__init__()
        self.parent = parent
        self.slaveName = slaveName
        
        self.vialConfig = self.parent.olfaConfig.get(slaveName)
        
        self.layout = QVBoxLayout()
        
        self.vials = []
        for v in self.vialConfig:
            #conf = self.vialConfig[v]      #conf = self.vialConfig.get(v)
            
            v_vialNum = v
            v_vial = Vial(self, vialNum=v_vialNum)
            self.vials.append(v_vial)
            
            x = int(v_vialNum)-1
            v_layout = QHBoxLayout()
            v_layout.addWidget(self.vials[x].OVcheckbox)
            v_layout.addWidget(self.vials[x].viewFlowBtn)
            v_layout.addWidget(self.vials[x].mainBtn)
            v_layout.addWidget(self.vials[x].calTable_widget)
            v_layout.addWidget(self.vials[x].setpoint_widget)
            v_layout.addWidget(self.vials[x].setpoint_sendBtn)
            v_layout.addWidget(self.vials[x].vialDebugBtn)
            
            self.layout.addLayout(v_layout)
        
        self.setTitle("Slave " + self.slaveName)
        self.setLayout(self.layout)




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
        self.port = port        # TODO: delete
        self.record = False
        
        self.calibrationON = False

        self.mainDir = os.getcwd()

        # NEED TO SET AT BEGINNING
        self.olfaConfig = {}
        self.sccm2Ard_dicts = {}
        self.ard2Sccm_dicts = {}

        self.baudrate = 9600    # TODO: delete these
        self.defTimebt = '100'
        
        # Make Logger
        self.className = type(self).__name__
        loggerName = self.className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)
        self.logger.debug('Creating %s', loggerName)
        

        # Load config files
        self.configDir = self.mainDir + '\\config'
        if not os.path.exists(self.configDir):
            self.logger.info('config directory does not exist, creating config directory at: %s', self.configDir)
            os.mkdir(self.configDir)
        self.load_all_config()
        self.create_slave_objects()

        # Create UI
        self.generate_ui()
        
        # Set Buttons to Default Values
        self.connectButton.setChecked(False)
        self.refreshButton.setEnabled(True)
        self.portWidget.setEnabled(True)
        self.masterBox.setEnabled(False)
        self.programStartButton.setEnabled(False)
        for s in self.slaves:
            s.setEnabled(False)


        # ~ for debugging rn ~
        if vialProgrammingOn == False:  self.vialProgrammingBox.setEnabled(False)
        if slavesActive == True:
            for s in self.slaves:
                s.setEnabled(True)
        self.calibrationBox.setEnabled(False)

    
        self.setTitle(self.className + ': ' + self.name)
        self.logger.debug('done making olfactometer')


    def load_all_config(self):
        ## Config directory for this instrument (ex: folder called "olfa prototype")
        self.instConfigDir = self.configDir + '\\' + self.name
        if not os.path.exists(self.instConfigDir):
            self.logger.info('creating config directory for instrument %s at: %s', self.name, self.instConfigDir)
            os.mkdir(self.instConfigDir)

        ## Olfa config file
        self.olfaConfigDir = self.instConfigDir + '\\olfaConfig.json'
        if os.path.exists(self.olfaConfigDir):  self.load_olfaConfig()      # TODO: maybe move the "if exist" statement to inside self.load_olfaConfig()
        else:
            #self.logger.debug('no olfaConfig.json file at %s', self.olfaConfigDir)
            self.getDefault_olfaConfig()
        
        ## Arduino state file
        self.arduinoFileDir = self.instConfigDir + '\\arduinoValues.json'
        if os.path.exists(self.arduinoFileDir): self.load_arduinoState()
        else:
            #self.logger.debug('no arduinoValues.json file at: %s', self.arduinoFileDir)
            self.getDefault_arduinoState()
            
        ## Flow Calibration Tables
        self.flowCalDir = self.configDir + '\\calibration_tables'
        self.load_flowCal_files()

        #self.create_slave_objects()
        
        # Load Default Olfa Config
        #self.configFileDir = self.configDir + '\\' + olfaConfigFile
        #self.load_olfaConfig_file()

    def create_slave_objects(self):
        self.slaves = []
        slaveNames = list(self.olfaConfig.keys())
        for s in slaveNames:
            s_slaveName = s
            self.logger.debug('Creating slave ' + s_slaveName)
            s_slave = Slave(self, s_slaveName)
            self.slaves.append(s_slave)
    
    def generate_ui(self):
        self.createSlaveGroupBox()  # need to make this before vial programming box
        self.createSourceFileBox()
        
        self.createConnectBox()
        self.createMasterBox()
        self.createCalibrationBox()
        self.createVialProgrammingBox()
        self.createBottomGroupBox()

        self.timer_for_openVials = openValveTimer(self)
        
        self.mainLayout = QGridLayout()

        self.mainLayout.addWidget(self.sourceFileBox, 0, 0, 1, 1)
        self.mainLayout.addWidget(self.connectBox, 1, 0, 4, 1)
        
        self.mainLayout.addWidget(self.masterBox, 0, 1, 1, 1)
        self.mainLayout.addWidget(self.calibrationBox, 1, 1, 1, 1)
        self.mainLayout.addWidget(self.vialProgrammingBox, 2, 1, 3, 1)
        col2w = self.calibrationBox.sizeHint().width()
        self.masterBox.setMaximumWidth(col2w)
        self.calibrationBox.setMaximumWidth(col2w)
        self.vialProgrammingBox.setMaximumWidth(col2w)
        
        self.mainLayout.addWidget(self.slaveGroupBox, 0, 2, 4, 1)
        self.mainLayout.addWidget(self.bottomGroupBox, 4, 2, 1, 1)
        #col3w = self.slaveGroupBox.sizeHint().width()
        #self.slaveGroupBox.setMaximumWidth(col3w)
        #self.bottomGroupBox.setMaximumWidth(col3w)

        self.setLayout(self.mainLayout)     
    

    # CONFIG FILES / LOADING
    def load_flowCal_files(self):
        if os.path.exists(self.flowCalDir):
            self.logger.debug('loading flow sensor calibration tables at: %s', self.flowCalDir)
            self.mainDir = os.getcwd()
            os.chdir(self.flowCalDir)

            suffix = '.txt'
            calFileNames = os.listdir()
            calFileNames = [fn for fn in calFileNames if fn.endswith(suffix)]   # only txt files # TODO: change to csv
            if calFileNames == []:  self.logger.warning('No files with suffix '' %s '' found in %s', suffix, self.flowCalDir)
            else:
                new_sccm2Ard_dicts = {}
                new_ard2Sccm_dicts = {}
                for calFile in calFileNames:
                    x = 0
                    idx_ext = calFile.find('.')
                    fileName = calFile[:idx_ext]
                    sccm2Ard = {}
                    ard2Sccm = {}
                    with open(calFile, newline='') as f:
                        csv_reader = csv.reader(f)
                        firstLine = next(csv_reader)
                        reader = csv.DictReader(f, delimiter=delimChar)
                        for row in reader:
                            if x == 0:
                                try:
                                    sccm2Ard[int(row['SCCM'])] = int(row['int'])
                                    ard2Sccm[int(row['int'])] = int(row['SCCM'])
                                except KeyError as err:
                                    self.logger.debug('%s does not have correct headings for calibration files', calFile)
                                    x = 1   # don't keep trying to read this file
                    if bool(sccm2Ard) == True:
                        new_sccm2Ard_dicts[fileName] = sccm2Ard
                        new_ard2Sccm_dicts[fileName] = ard2Sccm
                
                # if new dicts are not empty, replace the old ones
                if len(new_sccm2Ard_dicts) != 0:
                    self.sccm2Ard_dicts = new_sccm2Ard_dicts
                    self.ard2Sccm_dicts = new_ard2Sccm_dicts
                else:   self.logger.info('no calibration files found in this directory')
            
            os.chdir(self.mainDir)
        
        else:   self.logger.info('Cannot find flow cal directory at %s', self.flowCalDir)   # TODO this is big issue if none found
    
    '''
    def load_olfaConfig_file(self):
        self.logger.info('loading olfa config file at %s', self.configFileDir)
        try:
            with open(self.configFileDir, 'rt') as u_conf_file:
                self.olfaConfig = json.load(u_conf_file)
                # create slaves
                self.slaves = []
                slaveNames = list(self.olfaConfig.keys())
                for s in slaveNames:
                    s_slaveName = s
                    self.logger.debug('Creating slave ' + s_slaveName)
                    s_slave = Slave(self, s_slaveName)
                    self.slaves.append(s_slave)
                
        except IOError as ioe:
            self.logger.info('Could not load olfa config file: %s', ioe)
    '''
    def load_olfaConfig(self):
        self.logger.info('loading olfaConfig file at: %s', self.olfaConfigDir)
        try:
            with open(self.olfaConfigDir, 'rt') as u_conf_file:
                self.olfaConfig = json.load(u_conf_file)
                #self.create_slave_objects()
                '''
                # create slaves
                self.slaves = []
                slaveNames = list(self.olfaConfig.keys())
                for s in slaveNames:
                    s_slaveName = s
                    self.logger.debug('Creating slave ' + s_slaveName)
                    s_slave = Slave(self, s_slaveName)
                    self.slaves.append(s_slave)
                '''
                
        except IOError as ioe:
            self.logger.info('Could not load olfa config file: %s', ioe)
    
    def load_arduinoState(self):
        # TODO
        self.logger.warning('loading arduinoState file (not set up)')
        
    
    def getDefault_olfaConfig(self):
        self.logger.debug('getting default olfaConfig')
        # get values from master and slave config files
        self.ardConfigDir = self.mainDir + '\\olfactometer'

        if os.path.exists(self.ardConfigDir):    
            self.logger.info('getting default olfaConfig from arduino config files at %s', self.ardConfigDir)
            
            self.ardConfig_m = utils.getArduinoConfigFile(self.ardConfigDir + '\\' + arduinoMasterConfigFile)
            self.ardConfig_s = utils.getArduinoConfigFile(self.ardConfigDir + '\\' + arduinoSlaveConfigFile)

            # create slaves/vials
            
            ## Note: this needs to exactly match the arduino config file
            self.baudrate = int(self.ardConfig_m['baudrate'])
            self.numSlaves = int(self.ardConfig_m['numSlaves'])
            self.slaveNames = self.ardConfig_m.get('slaveNames[numSlaves]')
            self.vPSlave = self.ardConfig_m.get('vialsPerSlave[numSlaves]')
            self.defTimebt = self.ardConfig_m.get('timeBetweenRequests')

            self.v_setpoint = self.ardConfig_s['defSp']
            self.v_Kp = self.ardConfig_s['defKp']
            self.v_Ki = self.ardConfig_s['defKi']
            self.v_Kd = self.ardConfig_s['defKd']
            self.v_setting = self.ardConfig_s['setting']

            # create self.olfaConfig from arduino variables (other option is to create slaves, then generate self.olfaConfig at the end)
            for i in range(len(self.slaveNames)):
                vial_contents = {}
                slaveName = self.slaveNames[i]
                numVials = self.vPSlave[i]
                for j in range(int(numVials)):
                    vialNum = j+1
                    calTable = defSensorCal
                    setpoint = self.v_setpoint
                    Kp = self.v_Kp
                    Ki = self.v_Ki
                    Kd = self.v_Kd
                    setting = self.v_setting
                    vial_contents[vialNum] = dict(calTable=calTable,
                                                    setpoint=setpoint, Kp=Kp, Ki=Ki, Kd=Kd,
                                                    mode=setting)
                self.olfaConfig[slaveName] = vial_contents

            #for s in self.slaveNames:
                #vial_contents = {}
                #for v 

        
        else:
            # TODO
            self.logger.warning('loading default olfaConfig values (not set up yet)')
            #self.logger.error('cannot get olfaConfig info from arduino config files at %s', self.ardConfigDir)
        
    def getDefault_arduinoState(self):
        # TODO
        self.logger.warning('getting default arduino state variables (not set up)')
    
    
    def select_olfaConfig_file(self):
        self.logger.debug('changing olfa config file...')
        new_olfaConfigDir = QFileDialog.getOpenFileName(self, 'Select olfa config file')    # gives a tuple
        new_olfaConfigDir = new_olfaConfigDir[0]
        if new_olfaConfigDir:
            self.olfaConfigDir = new_olfaConfigDir
            self.load_olfaConfig()  #self.load_olfaConfig_file()
            self.update_slave_display()
        else:
            self.logger.info('no config file selected')

        self.olfaConfLineEdit.setText(self.olfaConfigDir)
    
    def update_slave_display(self):
        for i in reversed(range(self.allSlaves_layout.count())):
            item = self.allSlaves_layout.itemAt(i)
            w = self.allSlaves_layout.itemAt(i).widget()
            self.allSlaves_layout.removeWidget(w)
            sip.delete(w)
        
        for s in self.slaves:
            self.allSlaves_layout.addWidget(s)
            if self.connectButton.isChecked() == False: s.setEnabled(False)

        self.logger.debug('finished updating slave display')

    
    def select_flowCal_dir(self):
        self.logger.debug('changing flow cal directory...')
        prev_flowDir = self.flowCalDir
        prev_flowDir_url = QtCore.QUrl(prev_flowDir)
        prev_flowDir_url.setScheme("File")

        new_flowDir_url = QFileDialog.getExistingDirectoryUrl(self, 'Select Folder Containing Flow Calibration files', prev_flowDir_url)
        new_flowDir = new_flowDir_url.toString()
        new_flowDir = new_flowDir[8:]   # remove scheme
        
        if new_flowDir:
            self.flowCalDir = new_flowDir
            self.load_flowCal_files()
        else:
            self.logger.info('no directory selected')

        self.flowCalLineEdit.setText(self.flowCalDir)
    
    def update_slave_flowCal(self):
        self.logger.debug('updating flow cal options for slaves')
        for s in self.slaves:
            for v in s.vials:
                thisVial_calTable = v.calTable
                v.calTable_widget.clear()
                v.calTable_widget.addItems(self.ard2Sccm_dicts) # every time you add this it's going to update the cal table
                itemsInCombobox = [v.calTable_widget.itemText(i) for i in range(v.calTable_widget.count())]
                if thisVial_calTable in itemsInCombobox:
                    v.calTable_widget.setCurrentText(thisVial_calTable)
                    #v.new_calTable(v.calTable)
                else:
                    self.logger.info('setting flow cal table for %s to default', v.name)
    
    
    
    def generate_olfaConfig_file(self):
        self.logger.debug('generating config file (stuff set by the user. ex: cal table, vial contents)')
        
        self.config_info = {}
        for s in self.slaves:
            vial_contents = {}
            for v in s.vials:
                vial_contents[v.vialNum] = dict(calTable=v.calTable,setpoint=v.setpoint,Kp=v.Kp,Ki=v.Ki,Kd=v.Kd,mode=v.mode)
            self.config_info[s.slaveName] = vial_contents

    def generate_arduinoState_file(self):
        self.logger.debug('getting arduino state variables (stuff the slaves already have: setpoint, Kp, etc)')
        
        self.arduino_info = {}
        for s in self.slaves:
            vial_contents = {}
            for v in s.vials:
                vial_contents[v.vialNum] = dict(setpoint=v.setpoint,Kp=v.Kp,Ki=v.Ki,Kd=v.Kd,mode=v.mode)
            self.arduino_info[s.slaveName] = vial_contents
    
    
    def save_arduino_variables(self):
        self.generate_arduinoState_file()
        
        if os.path.exists(self.arduinoFileDir):
            self.logger.info('deleting arduinoState file: %s', self.arduinoFileDir)
            os.remove(self.arduinoFileDir)
        
        fn = self.arduinoFileDir
        with open(fn, 'wt') as json_file:
            self.logger.info('saving arduinoState file: %s', fn)
            json.dump(self.arduino_info, json_file)


    
    # BUTTON FUNCTIONS
    def btn_load_flowCal_files(self):
        self.select_flowCal_dir()
    
    def btn_load_olfaConfig_file(self):
        self.select_olfaConfig_file()
    
    def btn_save_olfaConfig_file(self):
        self.generate_olfaConfig_file()

        fn = QFileDialog.getSaveFileName(self, 'Save File', ".json")
        if fn:
            try:
                with open(fn[0], 'wt') as json_file:
                    self.logger.info('saving olfaConfig file: %s', fn)
                    json.dump(self.config_info, json_file)
            except IOError as ioe:
                self.logger.info('Could not save config file: %s', ioe)

    def btn_overwrite_olfaConfig_file(self):
        self.generate_olfaConfig_file()

        if os.path.exists(self.olfaConfigDir):
            self.logger.info('deleting olfaConfig file: %s', self.olfaConfigDir)
            os.remove(self.olfaConfigDir)
        
        fn = self.olfaConfigDir
        with open(fn, 'wt') as json_file:
            self.logger.info('saving olfaConfig file: %s', fn)
            json.dump(self.config_info, json_file)
            

    
    
    # UI STUFF
    def createSlaveGroupBox(self):
        self.slaveGroupBox = QGroupBox('Slave Devices')

        self.allSlaves_layout = QVBoxLayout()
        for s in self.slaves:
            self.allSlaves_layout.addWidget(s)

        self.allSlavesWidget = QWidget()
        self.allSlavesWidget.setLayout(self.allSlaves_layout)

        slaveScrollArea = QScrollArea()
        slaveScrollArea.setWidget(self.allSlavesWidget)
        slaveScrollArea.setWidgetResizable(True)

        slaveGroupBox_layout = QVBoxLayout()
        slaveGroupBox_layout.addWidget(slaveScrollArea)
        self.slaveGroupBox.setLayout(slaveGroupBox_layout)
    
    def createSourceFileBox(self):
        self.sourceFileBox = QGroupBox("Source Files")
        
        self.flowCalLbl = QLabel(text="Flow Calibration Tables:",toolTip="conversion from int to sccm")
        self.flowCalLineEdit = QLineEdit(text=self.flowCalDir)
        self.flowCalEditBtn = QPushButton("Edit",clicked=self.btn_load_flowCal_files)
        self.flowCalEditBtn.setFixedWidth(lineEditWidth)
        row1 = QHBoxLayout()
        row1.addWidget(self.flowCalLbl)
        row1.addWidget(self.flowCalLineEdit)
        row1.addWidget(self.flowCalEditBtn)
        
        self.olfaConfLbl = QLabel(text="Olfactometer Config File:")
        self.olfaConfLineEdit = QLineEdit(text=self.olfaConfigDir)
        self.olfaConfEditBtn = QPushButton("Edit",clicked=self.btn_load_olfaConfig_file)
        self.olfaConfEditBtn.setFixedWidth(lineEditWidth)
        row2 = QHBoxLayout()
        row2.addWidget(self.olfaConfLbl)
        row2.addWidget(self.olfaConfLineEdit)
        row2.addWidget(self.olfaConfEditBtn)

        #self.olfactometer_config_ui = OlfactometerConfigWindow(self)
        #self.manualEditBtn = QPushButton('Edit olfa configuration')
        #self.manualEditBtn.clicked.connect(lambda: self.olfactometer_config_ui.show())

        self.save_olfa_config_Btn = QPushButton('Save as new olfa config', toolTip='Save current olfa config to new file. Note: Updated setpoints (& K parameters) will only save if they have been sent to the device.')
        self.save_olfa_config_Btn.clicked.connect(self.btn_save_olfaConfig_file)
        self.overwrite_olfa_config_Btn = QPushButton('Set current olfa config as default', toolTip='Current olfa config will automatically load next time program is started')
        self.overwrite_olfa_config_Btn.clicked.connect(self.btn_overwrite_olfaConfig_file)
        row3 = QHBoxLayout()
        row3.addWidget(self.save_olfa_config_Btn)
        row3.addWidget(self.overwrite_olfa_config_Btn)
        
        layout = QFormLayout()
        layout.addRow(row1)
        layout.addRow(row2)
        layout.addRow(row3)
        self.sourceFileBox.setLayout(layout)        
    
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

    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        timeBtReqBox = QLineEdit(text=self.defTimebt,returnPressed=lambda:self.sendParameter('MM_timebt_' + timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda:self.sendParameter('MM_timebt_' + timeBtReqBox.text()))
        
        manualCmdBox = QLineEdit(text=defManualCmd,returnPressed=lambda: self.sendParameter(manualCmdBox.text()))
        manualCmdBtn = QPushButton(text="Send",clicked=lambda: self.sendParameter(manualCmdBox.text()))

        layout = QFormLayout()
        layout.addRow(QLabel(text="Time b/t requests for slave data (ms):"))
        layout.addRow(timeBtReqBox,timeBtButton)
        layout.addRow(QLabel(text="Manually send command:"))
        layout.addRow(manualCmdBox,manualCmdBtn)
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

        # check which directory the file is saving to (start in default calibration directory)

        self.calStartBtn.clicked.connect(self.startCalibration)

    def createVialProgrammingBox(self):
        self.vialProgrammingBox = QGroupBox("Vial Programming")
        
        self.setUpThreads()
        
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
    
    def createBottomGroupBox(self):
        self.bottomGroupBox = QGroupBox()

        self.durONBox = QSpinBox(value=defVl)
        self.OVbutton = QPushButton('Open Checked Vials')
        self.OVbutton.clicked.connect(self.openVials)

        self.setpointBox = QSpinBox(maximum=maxSp,value=defSp)
        self.spBtn = QPushButton(text='Update Setpoint for Checked Vials', toolTip='Sets all checked vials to this setpoint (overrides individual setpoints) based on individual vial calibration tables.')
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

    
    
    # CONNECT TO DEVICE
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
    

    
    # VIAL PROGRAMMING
    def setUpThreads(self):
        self.obj = worker()
        self.thread1 = QThread()
        self.obj.moveToThread(self.thread1)
        
        self.obj.w_sendThisSp.connect(self.sendThisSetpoint)
        self.obj.w_send_OpenValve.connect(self.send_OpenValve)
        self.obj.w_incProgBar.connect(self.incProgBar)
        self.obj.finished.connect(self.threadIsFinished)
        self.thread1.started.connect(self.obj.exp)
    
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
    
    def threadIsFinished(self):
        self.obj.threadON = False
        self.thread1.exit()
        self.programStartButton.setChecked(False);  self.programStartButton.setText('Start')
        self.progSettingsBox.setEnabled(True)
        self.logger.info('Finished program')
        self.progBar.setValue(0)



    # FOR OPENVALVETIMER
    def closeVials(self):
        self.logger.info('valves closed early by user')
        
        param = 'CV'
        value = '0'
        str_send = param + '_' + value + '_' + self.vialStr
        self.sendSlaveUpdate(str_send)

        self.timer_finished()
    
    def timer_finished(self):
        self.logger.debug('timer finished')
        for s in self.slaves:
            for v in s.vials:
                if v.mainBtn.isChecked():
                    v.mainBtn.setChecked(False)

    
    # USER COMMANDS TO ARDUINO
    def sendThisSetpoint(self, slave:str, vial:int, sccmVal:int):
        # TODO: change worker so it receives the entire vial object when it starts a program. then it'll already have the dictionary, etc
        
        # find dictionary to use
        for s in self.slaves:
            if s.slaveName == slave:
                for v in s.vials:
                    if v.vialNum == str(vial):
                        sensDictName = v.calTable

        dictToUse = self.sccm2Ard_dicts.get(sensDictName)
        
        # convert to integer and send
        ardVal = utils.convertToInt(float(sccmVal),dictToUse)
        
        strToSend = 'Sp_' + str(ardVal) + '_' + slave + str(vial)
        self.sendSlaveUpdate(strToSend)

    def send_OpenValve(self, slave:str, vial:int, dur:int):
        strToSend = 'OV_' + str(dur) + '_' + slave + str(vial)
        self.sendSlaveUpdate(strToSend)

    def changeSetpoint(self):
        sccmVal = self.setpointBox.value()  # TODO: add warning if no vials are checked
        for s in self.slaves:
            for v in s.vials:
                if v.OVcheckbox.isChecked():
                    v.setpoint = sccmVal
                    v.setpoint_widget.setValue(sccmVal)
                    v.vialDebugWindow.setpoint_wid.setValue(sccmVal)
                    dictToUse = v.sccmToInt_dict
                    intVal = utils.convertToInt(sccmVal, dictToUse)
                    str_send = 'Sp' + '_' + str(intVal) + '_' + v.name
                    self.sendSlaveUpdate(str_send)
        self.logger.warning('need to check if these strings are sent too quickly in a row')

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

        if len(self.vialStr) == 0:   self.logger.info('no vials selected - no command to send')
        else:
            param = 'OV'
            value = '5'        
            str_send = param + '_' + value + '_' + self.vialStr
            self.sendSlaveUpdate(str_send)

            self.timer_for_openVials.show()
            self.timer_for_openVials.duration = 5
            self.timer_for_openVials.start_timer()

    
    # SEND UPDATE TO ARDUINO
    def sendSlaveUpdate(self, strToSend):
        strToSend = 'S_' + strToSend
        self.sendParameter(strToSend)
    
    def sendParameter(self, strToSend):
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

    '''
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
    '''

    
    # INTERFACE FUNCTIONS
    def updateLineEditWidth(self):
        fm_c = self.olfaConfLineEdit.fontMetrics()
        w_c = fm_c.boundingRect(self.olfaConfLineEdit.text()).width()
        w_c = w_c - 50
        self.olfaConfLineEdit.setMinimumWidth(w_c)
        self.flowCalLineEdit.setMinimumWidth(w_c)
    
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
                except UnicodeDecodeError as err:
                    self.logger.error('Serial read error: %s\t%s',err,text)
            else:
                self.logger.debug('warning - text from Arduino was %s bytes: %s', len(text), text)
    
    
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

