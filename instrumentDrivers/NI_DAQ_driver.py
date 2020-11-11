# ST 2020
# NI_DAQ_driver.py

# need to install NI-DAQmx driver from NI website
# then install NI-DAQmx Python API by running python -m pip install nidaqmx

import time
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QTextEdit, QWidget,
                             QLabel, QLineEdit, QPushButton, QVBoxLayout)
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import nidaqmx
import utils

noPortMsg = '~ No NI devices detected ~'
analogChannel = 'ai0'

timeBt_Hz = 1000
timeBt_s = 1/timeBt_Hz
timeBtReadings = timeBt_s*1000    # in ms


class worker(QObject):
    sendTheData = pyqtSignal(float)

    def __init__(self, devName):
        super().__init__()
        self.readTheStuff = False
        self.timeToSleep = timeBt_s
        self.devName = devName
        self.analogChan = analogChannel
    
    @pyqtSlot()
    def readData(self):
        channelIWant = self.devName + '/' + self.analogChan
        t = nidaqmx.Task()      # create a task
        t.ai_channels.add_ai_voltage_chan(channelIWant) # add analog input channel to this task
        while self.readTheStuff == True:
            value = t.read(1)
            value = value[0]
            self.sendTheData.emit(value)
            time.sleep(self.timeToSleep)


class NiDaq(QGroupBox):

    def __init__(self, name, port=""):
        super().__init__()
        self.name = name
        self.port = port

        className = type(self).__name__
        loggerName = className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)
        self.logger.debug('Creating module for %s', loggerName)

        self.createConnectBox()
        self.createSettingsBox()
        col1 = QVBoxLayout()
        col1.addWidget(self.connectBox)
        col1.addWidget(self.settingsBox)

        self.createDataReceiveBoxes()

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(col1)
        #mainLayout.addWidget(self.connectBox)
        mainLayout.addWidget(self.dataReceiveBox)
        self.setLayout(mainLayout)
        self.setTitle(self.name)
    
    
    # CONNECT TO DEVICE
    def createConnectBox(self):
        self.connectBox = QGroupBox("Connect")

        self.portLbl = QLabel(text="Port/Device:")
        self.portWidget = QComboBox(currentIndexChanged=self.portChanged)
        self.connectButton = QPushButton(checkable=True,toggled=self.toggled_connect)
        self.refreshButton = QPushButton(text="Refresh",clicked=self.getPorts)
        self.getPorts()

        channelLbl = QLabel(text="channel to read:")
        self.channelToRead = QLineEdit(readOnly=True)
        if self.port != noPortMsg:
            self.channelToRead.setText(self.port + '/' + analogChannel)
        
        readLbl = QLabel(text="raw data from serial port:")
        self.rawReadDisplay = QTextEdit(readOnly=True)
        self.rawReadSpace = QWidget()
        readLayout = QVBoxLayout()
        readLayout.addWidget(readLbl)
        readLayout.addWidget(self.rawReadDisplay)
        self.rawReadSpace.setLayout(readLayout)
        
        self.connectBoxLayout = QFormLayout()
        self.connectBoxLayout.addRow(self.portLbl,self.portWidget)
        self.connectBoxLayout.addRow(channelLbl,self.channelToRead)
        self.connectBoxLayout.addRow(self.refreshButton,self.connectButton)
        self.connectBoxLayout.addRow(self.rawReadSpace)
        self.connectBox.setLayout(self.connectBoxLayout)
    
    def getPorts(self):
        self.portWidget.clear()
        local_system = nidaqmx.system.System.local()
        try:
            ports = nidaqmx.system.system.System().devices.device_names
            if ports:
                for ser in ports:
                    ser_str = str(ser)
                    self.portWidget.addItem(ser_str)
            else:
                self.portWidget.addItem(noPortMsg)
        except FileNotFoundError:
            self.portWidget.addItem(noPortMsg)
        self.port = self.portWidget.currentText()
    
    def portChanged(self):
        if self.portWidget.count() != 0:
            self.port = self.portWidget.currentText()
            if self.port == noPortMsg:
                self.connectButton.setEnabled(False)
                self.connectButton.setText(noPortMsg)
            else:
                self.connectButton.setEnabled(True)
                self.connectButton.setText("Connect to " + self.port)

    def toggled_connect(self, checked):
        if checked:
            self.logger.debug('clicked connect button')
            self.portWidget.setEnabled(False)
            self.refreshButton.setEnabled(False)
            self.connectButton.setText('Stop reading from ' + str(self.port))

            self.setUpThreads()
            self.obj.readTheStuff = True
        
        else:
            self.logger.debug('disconnect')
            self.portWidget.setEnabled(True)
            self.connectButton.setText('Connect to ' + str(self.port))
            self.refreshButton.setEnabled(True)

            self.obj.readTheStuff = False
            self.thread1.quit()
    
    def setUpThreads(self):
        self.obj = worker(self.port)
        self.thread1 = QThread()
        self.obj.moveToThread(self.thread1)
        self.obj.sendTheData.connect(self.taskFunction)
        self.thread1.started.connect(self.obj.readData)
        self.thread1.start()

    def createSettingsBox(self):
        self.settingsBox = QGroupBox("Settings")

        lbl = QLabel("Time bt readings (ms):")
        self.timeWid = QLineEdit()
        self.updateBut = QPushButton(text="Update",clicked=self.updateTimeBt)

        layout = QFormLayout()
        layout.addRow(lbl)
        layout.addRow(self.timeWid,self.updateBut)
        self.settingsBox.setLayout(layout)

    def updateTimeBt(self):
        pass
        #self.timeBt = self.timeWid.

    # RECEIVE DATA
    def createDataReceiveBoxes(self):
        self.dataReceiveBox = QGroupBox("data received")

        self.receiveBox = QTextEdit(readOnly=True)
        receiveBoxLbl = QLabel(text="raw val")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        self.flowBox = QTextEdit(readOnly=True)
        flowBoxLbl = QLabel(text="Reading (mV)")
        flowBoxLayout = QVBoxLayout()
        flowBoxLayout.addWidget(flowBoxLbl)
        flowBoxLayout.addWidget(self.flowBox)

        layout = QHBoxLayout()
        layout.addLayout(receiveBoxLayout)
        layout.addLayout(flowBoxLayout)
        self.dataReceiveBox.setLayout(layout)
    
    
    
    def taskFunction(self, incomingFlt):
        value = incomingFlt
        value_mV = value*1000
        value_mV = round(value_mV,3)

        str_value = str(value)
        str_value_mV = str(value_mV)

        self.rawReadDisplay.append(str_value)
        self.receiveBox.append(str_value)
        self.flowBox.append(str_value_mV)
        self.window().receiveDataFromChannels(self.name,'V',str_value)
    
    def updateName(self, newName):
        if not self.name == newName:
            self.name = newName
            self.logger.debug('name changed to %s', self.name)
            self.setTitle(self.name)