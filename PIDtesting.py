# ST 2020
# PIDtesting.py

import serial, time, sys, csv, os
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import (QWidget, QGroupBox, QHBoxLayout, QVBoxLayout, QTextEdit, QLineEdit, QLabel, QFormLayout,
                            QScrollArea, QApplication, QComboBox, QCheckBox, QPushButton)
from serial.tools import list_ports
from datetime import datetime

import utils, config
import slave, vial


#dict_3100V = utils.getCalibrationDict('calibration_values.xlsx','Honeywell 3100V',1,[0,2])

#flow2Ard = {}
#ard2Flow = {}
#for s in config.sensorTypes:
#    print(s)
#    Fl, Ar = utils.getCalibrationDict('calibration_values.xlsx',s,1,[0,2])


#dict_3300V = utils.getCalibrationDict('calibration_values.xlsx','Honeywell 3300V',2,[0,2])
currentDate = utils.currentDate
charsToRead = config.charsToRead

class GUIMain(QWidget):
    defFoldName = currentDate
    defFilePrefix = config.defFileLbl
    defFileType = config.defFileType
    delimChar = config.delimChar
    
    def __init__(self):
        super().__init__()
        self.record = False; self.recordALL = False
        self.recA1 = False; self.recA2 = False
        self.recB1 = False; self.recB2 = False
        utils.getInCorrectDirectory()
        self.ardConfig = utils.getArduinoConfigFile('config_master.h')

        mainLayout = QHBoxLayout()
        
        # COLUMN 1
        column1Layout = QVBoxLayout()
        self.createArduinoConnectBox()
        column1Layout.addWidget(self.arduinoConnectBox)

        # COLUMN 2
        column2Layout = QVBoxLayout()
        self.createMasterBox()
        self.numSlaves = int(self.ardConfig.get('numSlaves'))
        vPSlave = self.ardConfig.get('vialsPerSlave[numSlaves]')
        slaveNames = self.ardConfig.get('slaveNames[numSlaves]')
        self.slaves = []
        for i in range(self.numSlaves): # create the slaves
            s_slave = slave.Slave(self,slaveNames[i],int(vPSlave[i]),config.sensors[i])
            self.slaves.append(s_slave)
        self.createSlaveBox()
        '''
        #column2Layout.addWidget(self.slaveBox)
        #slaveBox = QGroupBox()
        #slaveLayout = QVBoxLayout()
        #for i in range(self.numSlaves): # add them to the layout
        #    slaveLayout.addWidget(self.slaves[i])
        #slaveBox.setLayout(slaveLayout)
        '''
        column2Layout.addWidget(self.masterBox)
        column2Layout.addWidget(self.slaveBox)
        ''' scroll bar for when there's lots of slaves
            scroll = QScrollArea()
            scroll.setWidget(slaveBox)
            column2Layout.addWidget(scroll)
        '''

        # COLUMN 3
        column3Layout = QVBoxLayout()
        self.createlogFileBox()
        column3Layout.addWidget(self.logFileBox)
        
        mainLayout.addLayout(column1Layout)
        mainLayout.addLayout(column2Layout)
        mainLayout.addLayout(column3Layout)
        self.setLayout(mainLayout)

    def createArduinoConnectBox(self):
        self.arduinoConnectBox = QGroupBox("Connect to master Arduino:")

        self.COMportSelect = QComboBox()
        ports = list_ports.comports()       # get list of ListPortInfo objects             
        for ser in ports:                   # for each object
            port_device = ser[0]
            port_description = ser[1]
            ser_str = ('{}: {}').format(port_device,port_description)   # make string of device info
            self.COMportSelect.addItem(ser_str)                         # add string to combobox

        self.connectButton = QPushButton(text="Connect",checkable=True,toggled=self.toggled_connect)
        self.arduinoReadBox = QTextEdit(readOnly=True)

        layout = QVBoxLayout()
        layout.addWidget(self.COMportSelect)
        layout.addWidget(self.connectButton)
        layout.addWidget(QLabel("reading from serial port:"))
        layout.addWidget(self.arduinoReadBox)
        self.arduinoConnectBox.setLayout(layout)

    def createlogFileBox(self):
        self.logFileBox = QGroupBox("Log File (" + self.defFileType + ")")
        
        utils.getInCorrectDirectory()

        logFileDir = os.getcwd() + '\\logfiles'
        foldDir = logFileDir + '\\' + self.defFoldName
        if not os.path.exists(logFileDir):  # if logfile folder doesn't exist
            os.mkdir(logFileDir)
            os.mkdir(foldDir)
            expNum = 1
        else:
            if not os.path.exists(foldDir): # if folder doesn't exist
                os.mkdir(foldDir)
                expNum = 1
            else:
                os.chdir(foldDir)
                files = os.listdir()
                if not files:
                    expNum = 1
                else:
                    lastFile = files[len(files)-1]
                    i_fExt = lastFile.rfind('.')
                    lastFile = lastFile[:i_fExt]
                    i_us = lastFile.rfind('_')
                    lastExpNum = lastFile[i_us+1:]
                    expNum = int(lastExpNum) + 1
        expNum = str(expNum).zfill(2)
        defFileName = currentDate + '_' + self.defFilePrefix + '_' + expNum

        self.enterLogDir = QLineEdit(text=logFileDir)
        self.enterFoldName = QLineEdit(text=self.defFoldName)
        self.enterFileName = QLineEdit(text=defFileName)

        self.cbALL = QCheckBox('ALL')
        self.cbA1 = QCheckBox('A1'); self.cbA2 = QCheckBox('A2')
        self.cbB1 = QCheckBox('B1'); self.cbB2 = QCheckBox('B2')
        cbLayout = QHBoxLayout()
        cbLayout.addWidget(QLabel("Record:"))
        cbLayout.addWidget(self.cbALL)
        cbLayout.addWidget(self.cbA1); cbLayout.addWidget(self.cbA2)
        cbLayout.addWidget(self.cbB1); cbLayout.addWidget(self.cbB2)

        self.recordButton = QPushButton(text="Create File && Start Recording", checkable=True, toggled=self.toggled_startRecord)
        #self.newFileButton = QPushButton(text="End Recording & Close Window",checkable=True,toggled=self.toggled_newfile)
        self.logFileOutputBox = QTextEdit(readOnly=True,minimumWidth=250,maximumWidth=300)

        layout = QFormLayout()
        layout.addRow(QLabel("Directory:"),self.enterLogDir)
        layout.addRow(QLabel("Folder:"),self.enterFoldName)
        layout.addRow(QLabel("File Name"),self.enterFileName)
        layout.addRow(cbLayout)
        layout.addRow(self.recordButton)
        layout.addRow(self.logFileOutputBox)
        #layout.addRow(self.recordButton, self.newFileButton)

        self.logFileBox.setLayout(layout)
        utils.getInCorrectDirectory()

    def createMasterBox(self):
        self.masterBox = QGroupBox("Master Settings")

        defTimebt = self.ardConfig.get('timeBetweenRequests')
        timeBtReqLbl = QLabel(text="Time between requests for slave data (in ms):")
        timeBtReqBox = QLineEdit(text=defTimebt,returnPressed=lambda:self.sendMasterParameter('M','timebt',timeBtReqBox.text()))
        timeBtButton = QPushButton(text="Update",clicked=lambda: self.sendMasterParameter('M','timebt',timeBtReqBox.text()))
        
        timeupdateLayout = QHBoxLayout()
        timeupdateLayout.addWidget(timeBtReqLbl)
        timeupdateLayout.addWidget(timeBtReqBox)
        timeupdateLayout.addWidget(timeBtButton)
        
        self.masterBox.setLayout(timeupdateLayout)

    def createSlaveBox(self):
        self.slaveBox = QGroupBox("Slave Settings")

        layout = QVBoxLayout()
        for i in range(self.numSlaves):
            layout.addWidget(self.slaves[i])
        
        self.slaveBox.setLayout(layout)


    def toggled_connect(self, checked):

        if checked:
            port_str = self.COMportSelect.currentText()     # get selected string
            try:
                i = port_str.index(':')
                self.comPort = port_str[:i]
                self.baudrate = int(self.ardConfig.get('baudrate'))
                self.serial = QtSerialPort.QSerialPort(self.comPort, baudRate=self.baudrate, readyRead=self.receive)   # create serial object
                
                if not self.serial.isOpen():                        # if serial port is not open
                    self.serial.open(QtCore.QIODevice.ReadWrite)    # open device, set OpenMode to ReadWrite
                    self.connectButton.setText('Stop reading serial port at ' + self.comPort)
                    if not self.serial.isOpen():                    # if it's still not open
                        self.connectButton.setChecked(False)        # uncheck button
                        print("issue opening serial port at" + port_str)
            except ValueError as err:
                self.connectButton.setChecked(False)
                print("COM port selected gives ValueError: ", str(err))
        else:
            try:
                self.serial.close()
                self.connectButton.setText("Connect")
            except AttributeError as err:
                pass                # serial object does not exist

    def toggled_startRecord(self, checked):
        
        if checked:
            if self.cbALL.isChecked:
                self.recordALL = True
            else:
                self.recordALL = False
                if self.cbA1.isChecked:   self.recA1 = True
                else: self.recA1 = False
                if self.cbA2.isChecked:   self.recA2 = True
                else: self.recA2 = False
                if self.cbB1.isChecked:   self.recB1 = True
                else: self.recB1 = False
                if self.cbB2.isChecked:   self.recB2 = True
                else: self.recB2 = False

            if self.recordALL or self.recA1 or self.recA2 or self.recB1 or self.recB2: 
                self.record = True
            else: 
                self.record = False

            # get data from input boxes
            self.enteredLogDir = self.enterLogDir.text()
            self.enteredFoldName = self.enterFoldName.text()
            self.enteredFileName = self.enterFileName.text() + self.defFileType
            
            self.enteredFoldDir = self.enteredLogDir + '\\' + self.enteredFoldName
            self.enteredFileDir = self.enteredFoldDir + '\\' + self.enteredFileName
            
            if not os.path.exists(self.enteredLogDir):      # if log folder doesn't exist
                try:
                    os.mkdir(self.enteredLogDir);   print("just made a folder at " + self.enteredLogDir)
                except FileNotFoundError as err:
                    print("ok currently we're in " + str(os.getcwd()))
                    print("and that log file path isn't gonna work here" + self.enteredFileDir)
                    print(err)
            if not os.path.exists(self.enteredFoldDir):     # if folder doesn't exist
                os.mkdir(self.enteredFoldDir)
            if not os.path.exists(self.enteredFileName):    # if file doesn't exist
                os.chdir(self.enteredFoldDir)
                Heading = "ST 2020"
                Heading2 = "***********"
                File = "LogFile:", self.enteredFileName
                Date = "Date:", currentDate
                DataHead = "Time","Vial/Line","Item","Value","Ctrl (prop.valve)"
                timeNow = datetime.time(datetime.now())
                timeNow_f = timeNow.strftime('%H:%M:%S.%f')
                timeNow_str = timeNow_f[:-3]
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f, delimiter=self.delimChar)
                    writer.writerow([Heading])
                    writer.writerow([Heading2])
                    writer.writerow(File)
                    writer.writerow(Date)
                    writer.writerow("")
                    writer.writerow(DataHead)
            
            recbutton_str = "Pause Recording"
            self.recordButton.setText(recbutton_str)

        else:
            self.recA1 = False
            self.recA2 = False
            self.recB1 = False
            self.recB2 = False
            self.record = False
            self.recordALL = False
            recbutton_str = "Resume Recording to " + self.enteredFileName
            self.recordButton.setText(recbutton_str)

    def toggled_newfile(self, checked):
        if checked:
            # get data from input boxes
            self.enteredLogDir = self.enterLogDir.text()
            self.enteredFoldName = self.enterFoldName.text()
            self.enteredFileName = self.enterFileName.text() + defFileType
            self.date = self.dateWidget.text()
            self.sensorType = self.sensorTypeWidget.currentText()
            self.sensorNum = self.sensorNumWidget.text()
            
            # if file does not exist, open & write header
            if not os.path.exists(self.fileLoc):
                Heading = "ST 2020"
                Heading2 = "***********"
                File = "LogFile:", self.enteredFileName
                Date = "Date:", self.date
                SensorType = "Sensor Type:", self.sensorType
                SensorNum = "Sensor #:", self.sensorNum
                DataHead = "Time","Event"
                timeNow = datetime.time(datetime.now())
                timeNow_f = timeNow.strftime('%H:%M:%S.%f')
                timeNow_str = timeNow_f[:-3]
                SpLine = timeNow_str, "A1","Sp","768"
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f, delimiter=self.delimChar)
                    writer.writerow([Heading])
                    writer.writerow([Heading2])
                    writer.writerow(File)
                    writer.writerow("")
                    writer.writerow(Date)
                    writer.writerow(SensorType)
                    writer.writerow(SensorNum)
                    writer.writerow("")
                    writer.writerow(DataHead)
                    writer.writerow(SpLine)
            else:
                print("file already exists")

            self.newFileButton.setText("pause recording")
        
        else:
            self.newFileButton.setText("start recording")
    
    def receive(self):
        
        while self.serial.canReadLine():
            text = self.serial.readLine(100)
            if len(text) == charsToRead:      # if string received is long enough
                try:
                    text = text.decode("utf-8")
                    text = text.rstrip('\r\n')
                    self.arduinoReadBox.append(text)
                    vialInfo = text[0:2]    # 'A1'
                    value = text[2:]        # '020502550000'
                    if value.isnumeric():
                        for i in range(self.numSlaves):
                            if self.slaves[i].slaveName == vialInfo[0]: s_index = i
                            #else: print("doesn't match any slave, vialInfo[0] is " + str(vialInfo[0]))
                        v_index = int(vialInfo[1])-1
                        self.slaves[s_index].vials[v_index].appendNew(value)
                        if (vialInfo == 'A1' and self.recA1 or vialInfo == 'A2' and self.recA2 or
                            vialInfo == 'B1' and self.recB1 or vialInfo == 'B2' and self.recB2 or self.recordALL):
                            timeNow = datetime.time(datetime.now())
                            timeNow_f = timeNow.strftime('%H:%M:%S.%f')
                            timeNow_str = timeNow_f[:-3]
                            param = 'FL'       # FL = "flow"
                            flow = value[0:4]
                            ctrl = value[5:8]
                            toWrite = timeNow_str, vialInfo, param, flow, ctrl
                            with open(self.enteredFileName,'a',newline='') as f:
                                writer = csv.writer(f,delimiter=self.delimChar)
                                writer.writerow(toWrite)
                            self.logFileOutputBox.append(str(toWrite))

                except UnicodeDecodeError as err:
                    print("error: ", err)

            else:
                print("text read was " + str(len(text)) + " bytes: " + str(text))
 
    def sendParameter(self, slave, vial, parameter, value=""):
        str_line = slave + str(vial)

        if parameter[0] == 'K' and parameter != 'Kx':
            str_param = 'Kx'
            nextChar = parameter[1].capitalize()
            valToSend = nextChar + value
        else:
            str_param = parameter
            valToSend = value

        str_send = str_line + '_' + str_param + '_' + valToSend
        bArr_send = str_send.encode()
        try:
            self.serial.write(bArr_send)
            print("sending to master: " + str_send)
            
            if self.record == True:
                timeNow = datetime.time(datetime.now())
                timeNow_f = timeNow.strftime('%H:%M:%S.%f')
                timeNow_str = timeNow_f[:-3]
                toWrite = timeNow_str,str_line,parameter,valToSend
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=self.delimChar)
                    writer.writerow(toWrite)
                self.logFileOutputBox.append(str(toWrite))
        
        except AttributeError as err:
            print("serial port not open: ", err)

    def sendMasterParameter(self, slave, parameter, value=""):
        str_1 = 'M'
        str_2 = slave + '_'
        str_3 = parameter +'_'
        str_4 = value

        str_send = str_1 + str_2 + str_3 + str_4
        bArr_send = str_send.encode()
        try:
            self.serial.write(bArr_send)
        except AttributeError:
            print("serial port not open")

        if parameter == 'debug_':   self.numBytesIwant = 10
        if parameter == 'normal':   self.numBytesIwant = 6



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GUIMain()
    w.show()
    sys.exit(app.exec_())