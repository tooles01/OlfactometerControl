# ST 2020
# flowSensor_driver.py

# for Honeywell 5100V

import csv, os, time, serial, sip
from datetime import datetime
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QTextEdit, QWidget,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout)
from serial.tools import list_ports
import config, utils

currentDate = utils.currentDate
noPortMsg = config.noPortMsg

flowSens_baud = 9600
sensorType = "Honeywell 5101V"

class flowSensor(QGroupBox):

    def __init__(self, name, port=""):
        super().__init__()
        self.name = name
        self.port = port

        self.connected = False

        self.className = type(self).__name__
        loggerName = self.className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)

        self.createConnectBox()
        self.connectBox.setFixedWidth(325)
        self.createDataReceiveBoxes()

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.connectBox)
        mainLayout.addWidget(self.dataReceiveBox)
        self.setLayout(mainLayout)
        self.setTitle(loggerName)
    
    
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

        self.connectBoxLayout = QFormLayout()
        self.connectBoxLayout.addRow(self.portLbl,self.portWidget)
        self.connectBoxLayout.addRow(self.refreshButton,self.connectButton)
        self.connectBoxLayout.addRow(self.rawReadSpace)
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
            comPort = self.port[:i]
            baudrate = int(flowSens_baud)
            self.serial = QtSerialPort.QSerialPort(comPort,baudRate=baudrate,readyRead=self.receive)
            self.logger.info('Created serial object at %s', comPort)
            if not self.serial.isOpen():
                if self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.logger.info('successfully opened port (& set mode to ReadWrite)')
                    self.setConnected(True)
                else:
                    self.logger.warning('could not successfully open port')
                    self.setConnected(False)
            else:
                self.setConnected(True)
        else:
            try:
                if self.serial.isOpen():
                    self.serial.close()
                    self.logger.info('Closed serial port')
                    self.setConnected(False)
            except AttributeError:
                self.logger.debug('Cannot close port, serial object does not exist')
    
    def setConnected(self, connected):
        if connected == True:
            self.connectButton.setText('Stop communication w/ ' + self.portStr)
            self.refreshButton.setEnabled(False)
        else:
            self.connectButton.setText('Connect to ' + self.portStr)
            self.connectButton.setChecked(False)
            self.refreshButton.setEnabled(True)
    
    
    # RECEIVE DATA
    def createDataReceiveBoxes(self):
        self.dataReceiveBox = QGroupBox("data received")

        self.receiveBox = QTextEdit(readOnly=True)
        receiveBoxLbl = QLabel(text="Flow val (int), Flow val (SCCM)")
        receiveBoxLayout = QVBoxLayout()
        receiveBoxLayout.addWidget(receiveBoxLbl)
        receiveBoxLayout.addWidget(self.receiveBox)

        layout = QHBoxLayout()
        layout.addLayout(receiveBoxLayout)
        self.dataReceiveBox.setLayout(layout)
    
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            try:
                text = text.decode("utf-8")
                text = text.rstrip('\r\n')
                self.rawReadDisplay.append(text)
                if text.isnumeric():
                    str_value = text
                    flowVal = int(text)
                    val_SCCM = utils.convertToSCCM(flowVal,sensorType)
                    dataStr = str_value + '\t' + str(val_SCCM)
                    self.receiveBox.append(dataStr)
                    self.window().receiveDataFromChannels(self.name,'FL',str_value)
            except UnicodeDecodeError as err:
                self.logger.error('Serial read error: %s',err)
