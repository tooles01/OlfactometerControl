# ST 2020
# run.py

import sys, os, csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject
import sip
from instrumentDrivers import olfactometer_driver, flowSensor_driver, NI_DAQ_driver
import utils

currentDate = utils.currentDate
datafileLbl = 'exp01'
delimChar = ','
dataFileType = ".csv"

instTypes = ['olfactometer','flow sensor','NI-DAQ']
users = ['Shannon','Ophir','Other']


class channelObj(QObject):
    
    def __init__(self, instrument="", name=""):
        super().__init__()
        self.instrument = instrument
        self.name = name

        self.checkBox = QCheckBox(checked=True)
        self.checkBoxLbl = QLabel(text=self.name)

        self.nameWidget = QLineEdit(text=name,toolTip="whatever you want the channel to be called")
        
        self.instWidget = QComboBox()
        self.instWidget.addItems(instTypes)
        AllItems = [self.instWidget.itemText(i) for i in range(self.instWidget.count())]
        if self.instrument in AllItems:
            i_idx = AllItems.index(self.instrument)
            self.instWidget.setCurrentIndex(i_idx)

        self.instrument = self.instWidget.currentText()

        # for channel settings box in mainGUI
        self.infoRow = QWidget()
        infoRowLayout = QHBoxLayout()
        infoRowLayout.addWidget(self.checkBox)
        infoRowLayout.addWidget(self.instWidget)
        infoRowLayout.addWidget(self.nameWidget)
        self.infoRow.setLayout(infoRowLayout)

class channelGroupBoxObject(QGroupBox):

    def __init__(self, name="", instrument=""):
        super().__init__()
        self.name = name
        self.instrument = instrument
        
        self.checkBox = QCheckBox(checked=True)
        self.checkBoxLbl = QLabel(text=self.name)

        self.createInstrumentWidget()

    # FUNCTIONS TO CREATE GUI
    def createInstrumentWidget(self):
        if self.instrument == 'olfactometer':
            self.instrument_widget = olfactometer_driver.olfactometer(self.name)
        elif self.instrument == 'flow sensor':
            self.instrument_widget = flowSensor_driver.flowSensor(self.name)
        elif self.instrument == 'NI-DAQ':
            self.instrument_widget = NI_DAQ_driver.NiDaq(self.name)
        else:
            self.instrument_widget = QGroupBox("empty widget for " + self.instrument)

class mainGUI(QMainWindow):

    def __init__(self, channel_objs):
        super().__init__()
        self.channels = channel_objs
        self.numChannels = len(self.channels)
        
        className = type(self).__name__
        self.logger = utils.createLogger(className)

        self.createMainSettingsBox()
        self.createChannelSettingsBox()
        self.createDataFileBox()
        self.createChannelGroupBox()
        
        w = max(self.mainSettingsBox.sizeHint().width(),
                self.channelSettingsBox.sizeHint().width(),
                self.dataFileBox.sizeHint().width()) + 5
        self.mainSettingsBox.setFixedWidth(w)
        self.channelSettingsBox.setFixedWidth(w)
        self.dataFileBox.setFixedWidth(w)
        
        col1 = QVBoxLayout()
        col1.addWidget(self.mainSettingsBox)
        col1.addWidget(self.channelSettingsBox)
        col1.addWidget(self.dataFileBox)
        
        self.mainLayout = QHBoxLayout()
        self.mainLayout.addLayout(col1)
        self.mainLayout.addWidget(self.channelGroupBox)
        self.setWindowTitle('Olfactometer Prototype & Accessory Control')

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.mainLayout)
        self.setCentralWidget(self.central_widget)

        # Menu Bar
        self.createMenuBar()
        
        self.resize(self.sizeHint())
        
    
    def createMenuBar(self):
        self.menu_bar = self.menuBar()

        self.olfaSettings_menu = self.menu_bar.addMenu('Olfactometer')

        self.olfaSettings_createNew_action = self.olfaSettings_menu.addAction('Create new/reset olfactometer')
        self.olfaSettings_createNew_action.triggered.connect(self.create_new_olfactometer)

        self.olfaSettings_loadConf_action = self.olfaSettings_menu.addAction('Load olfa config file')
        self.olfaSettings_loadConf_action.triggered.connect(self.load_olfa_config_file)
        #self.olfaSettings_menu.addAction
        self.info_menu = self.menu_bar.addMenu('Info')

        
    def create_new_olfactometer(self):
        # to start, need: name, slaves, vials per slave
        # maybe do this like the parameter tree thing
        self.logger.info('do this manually in the config file - i don''t feel like setting it up yet')
        #new_olfa = olfactometer_driver.OlfactometerConfigWindow(self)
        #new_olfa.show()


    # TO CREATE THE GUI
    def createMainSettingsBox(self):
        self.mainSettingsBox = QGroupBox("Main Settings")

        userLbl = QLabel(text="User:",toolTip="just for logging")
        self.userSelectCb = QComboBox()
        self.userSelectCb.addItems(users)
        self.user = self.userSelectCb.currentText()
        
        layout = QFormLayout()
        layout.addRow(userLbl,self.userSelectCb)
        self.mainSettingsBox.setLayout(layout)

        self.userSelectCb.currentIndexChanged.connect(self.updateUser)

    def createChannelSettingsBox(self):
        self.channelSettingsBox = QGroupBox("Channel Settings")

        # number of channels
        self.numCBox = QSpinBox(value=self.numChannels,minimum=1)
        layout1 = QFormLayout()
        layout1.addRow(QLabel("Number of channels:"),self.numCBox)
        box1 = QGroupBox(); box1.setLayout(layout1)
        
        # channel info
        lblRow = QHBoxLayout()
        lblRow.addWidget(QLabel(text="Record:"))
        lblRow.addWidget(QLabel(text="Instrument:"))
        lblRow.addWidget(QLabel(text="Name:"))
        self.layout2 = QVBoxLayout()
        self.layout2.addLayout(lblRow)
        self.prevChans_ever = []      # set up a list to keep track of previously entered
        for c in self.channels:
            self.prevChans_ever.append(c)
            self.layout2.addWidget(c.infoRow)
        box2 = QGroupBox(); box2.setLayout(self.layout2)
        
        self.channelUpdateBtn = QPushButton(text="Update",toolTip='Update display')

        layout = QVBoxLayout()
        layout.addWidget(box1)
        layout.addWidget(box2)
        layout.addWidget(self.channelUpdateBtn)
        self.channelSettingsBox.setLayout(layout)

        self.numCBox.valueChanged.connect(self.updateNumChans)
        self.channelUpdateBtn.clicked.connect(self.updateChannels)

    def createChannelGroupBox(self):
        self.channelGroupBox = QGroupBox("Instrument Channels")

        self.channelWidget_layout = QVBoxLayout()
        self.inst_drivers = []
        for i in self.channels:
            c_name = i.name
            c_instrument = i.instrument
            self.logger.debug('>> Creating channel for %s (%s)',c_instrument,c_name)
            channel_groupbox = channelGroupBoxObject(c_name,c_instrument)
            if c_instrument != 'olfactometer':  channel_groupbox.instrument_widget.setMaximumHeight(500)
            self.inst_drivers.append(channel_groupbox)
            self.channelWidget_layout.addWidget(channel_groupbox.instrument_widget)
        
        allChannelsWidget = QWidget()
        allChannelsWidget.setLayout(self.channelWidget_layout)
        allChannelsWidget.resize(allChannelsWidget.sizeHint())
        
        channelScrollArea = QScrollArea()
        channelScrollArea.setWidget(allChannelsWidget)
        channelScrollArea.setWidgetResizable(True)
        channelScrollArea.resize(channelScrollArea.sizeHint())

        channelGroupBox_layout = QVBoxLayout()
        channelGroupBox_layout.addWidget(channelScrollArea)
        self.channelGroupBox.setLayout(channelGroupBox_layout)
        self.channelGroupBox.resize(self.channelGroupBox.sizeHint())
    
    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("DataFile")

        self.datafileDir = utils.findTodayDir()
        files = os.listdir(self.datafileDir)
        dataFiles = [x for x in files if datafileLbl in x]  # find the files with fileLbl in them
        if not dataFiles:   self.lastFileNum = 0
        else:
            # find the number of the last file
            lastFile = dataFiles[len(dataFiles)-1]
            i_fExt = lastFile.rfind('.')
            lastFile = lastFile[:i_fExt]    # remove file extension
            i_us = lastFile.rfind('_')      # find last underscore
            lastFilePosNum = lastFile[i_us+1:]
            if lastFilePosNum.isnumeric():  # if what's after the underscore is a number
                self.lastFileNum = int(lastFilePosNum)
            else:
                fileIdx = 2
                while lastFilePosNum.isnumeric() == False:
                    lastFile = dataFiles[len(dataFiles)-fileIdx]
                    i_fExt = lastFile.rfind('.')
                    lastFile = lastFile[:i_fExt]
                    i_us = lastFile.rfind('_')
                    lastFilePosNum = lastFile[i_us+1:]
                    fileIdx=fileIdx+1
                self.lastFileNum = int(lastFilePosNum)
        
        defFileName = utils.makeNewFileName(datafileLbl, self.lastFileNum)
        self.enterFileName = QLineEdit(text=defFileName)
        
        self.recordButton = QPushButton(text="Create && Start Recording",checkable=True,clicked=self.clicked_record)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)
        self.dataFileOutputBox = QTextEdit(readOnly=True)

        fileLayout = QHBoxLayout()
        fileLayout.addWidget(QLabel(text="File Name:"))
        fileLayout.addWidget(self.enterFileName)
        
        layout = QFormLayout()
        layout.addRow(fileLayout)
        layout.addRow(self.recordButton,self.endRecordButton)
        layout.addRow(self.dataFileOutputBox)
        self.dataFileBox.setLayout(layout)
        
        self.endRecordButton.setEnabled(False)
    
    
    # FUNCTIONS THAT DO STUFF
    def updateNumChans(self):
        newNumChans = self.numCBox.value()
        prevNumChans = len(self.channels)
        self.numChannels = newNumChans
        self.logger.debug('# of channels changed to %s',self.numChannels)

        # to make new channels
        if newNumChans > prevNumChans:  # it's only going to increment by 1
            idx_toMake = prevNumChans
            numRows = len(self.prevChans_ever)
            if idx_toMake < numRows:       # if we've already had a row for this
                c = channelObj(name=self.prevChans_ever[idx_toMake].name,instrument=self.prevChans_ever[idx_toMake].instrument)
            else:
                c = channelObj(name='',instrument='')
                self.prevChans_ever.append(c)
            self.channels.append(c)
            self.layout2.addWidget(self.channels[idx_toMake].infoRow)
        
        # to delete channels
        if prevNumChans > newNumChans:
            idx_toDel = prevNumChans - 1
            self.prevChans_ever[idx_toDel].name = self.channels[idx_toDel].nameWidget.text()    # save the name and instrument to prevchans
            self.prevChans_ever[idx_toDel].instrument = self.channels[idx_toDel].instWidget.currentText()
            self.layout2.removeWidget(self.channels[idx_toDel].infoRow)    # remove the last infoRow
            sip.delete(self.channels[idx_toDel].infoRow)   # also delete that widget
            self.channels.pop(-1)

    def updateChannels(self):
        numPrev = len(self.inst_drivers)
        numNew = len(self.channels)
        self.logger.info('updating channels...')

        for idx in range(numPrev):  # for each of the previous channels
            if idx < numNew:        # if its a value within the newnum (will exist)
                newName = self.channels[idx].nameWidget.text()
                prevName = self.inst_drivers[idx].name
                newInst = self.channels[idx].instWidget.currentText()
                prevInst = self.inst_drivers[idx].instrument
                if newInst != prevInst:   # if instrument is different, make new
                    newChannel = channelGroupBoxObject(name=newName,instrument=newInst)
                    self.channelWidget_layout.removeWidget(self.inst_drivers[idx].instrument_widget)
                    sip.delete(self.inst_drivers[idx].instrument_widget)
                    self.inst_drivers[idx] = newChannel
                    self.channelWidget_layout.insertWidget(idx,self.inst_drivers[idx].instrument_widget)
                else:
                    if newName != prevName:           # if instrument is same but name is different
                        self.inst_drivers[idx].name = newName
                        self.inst_drivers[idx].instrument_widget.setTitle(newName)

        if numPrev > numNew:        # delete extra channels
            num2Delete = numPrev - numNew
            for i in range(num2Delete):
                self.channelWidget_layout.removeWidget(self.inst_drivers[-1].instrument_widget)
                sip.delete(self.inst_drivers[-1].instrument_widget)
                self.inst_drivers.pop(-1)
        
        if numPrev < numNew:        # add new channels
            num2Make = numNew - numPrev
            for i in range(num2Make):
                newName = self.channels[i+numPrev].nameWidget.text()
                newInst = self.channels[i+numPrev].instWidget.currentText()
                self.channels[i+numPrev].name = newName
                self.channels[i+numPrev].instrument = newInst
                newChannel = channelGroupBoxObject(name=newName,instrument=newInst)
                self.inst_drivers.append(newChannel)
                self.channelWidget_layout.addWidget(newChannel.instrument_widget)
        
        self.logger.debug('finished updating channels')
    
    def updateUser(self):
        newUser = self.userSelectCb.currentText()
        if self.user != newUser:
            self.user = newUser
            self.logger.info('New user: %s', self.user)
    
    def clicked_record(self):
        if self.recordButton.isChecked() == True:
            self.recordButton.setText("Pause Recording")
            self.endRecordButton.setEnabled(True)
            self.enteredFileName = self.enterFileName.text() + dataFileType
            self.enteredFilePath = self.datafileDir + '\\' + self.enteredFileName
            if not os.path.exists(self.enteredFilePath):
                self.logger.info('Creating new datafile: %s (%s)',self.enteredFileName, self.datafileDir)
                File = self.enteredFileName, ' '
                Time = "File Created: ", str(currentDate + ' ' + utils.getTimeNow())
                DataHead = "Time","Instrument","Unit","Value"
                with open(self.enteredFilePath,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=delimChar)
                    writer.writerow(File)
                    writer.writerow("")
                    writer.writerow(Time)
                    writer.writerow("")
                    writer.writerow(DataHead)
            else:
                self.logger.info('Resuming recording to %s (%s)', self.enteredFileName, self.datafileDir)
                
        else:
            self.logger.info('Paused recording to %s',self.enteredFileName)
            self.recordButton.setText("Resume Recording")

    def clicked_endRecord(self):
        self.logger.info('Ended recording to %s', self.enteredFileName)
        if self.recordButton.isChecked() == True:
            self.recordButton.setChecked(False)
        
        self.lastFileNum = self.lastFileNum + 1
        newFileName = utils.makeNewFileName(datafileLbl,self.lastFileNum)

        self.enterFileName.setText(newFileName)
        self.recordButton.setText("Create File && Start Recording")
        self.dataFileOutputBox.clear()
    
    def receiveDataFromChannels(self, instrument, unit, value):
        if self.recordButton.isChecked():
            toWrite = utils.getTimeNow(),instrument,unit,str(value)
            for chan in self.inst_drivers:
                if chan.checkBoxLbl.text() in instrument:
                    if chan.checkBox.isChecked():
                        with open(self.enteredFileName,'a',newline='') as f:
                            writer = csv.writer(f, delimiter=delimChar)
                            writer.writerow(toWrite)
                        display = str(toWrite)
                        self.dataFileOutputBox.append(display[1:-1])

    def load_olfa_config_file(self):
        self.logger.info('not set up')

    
    # OTHER
    def closeEvent(self, event):
        result = QMessageBox.question(self,
            'Confirm exit',
            'are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No)

        event.ignore()

        if result == QMessageBox.Yes:
            # save current olfa state - based on the last shit you sent to the Arduinos
            
            self.inst_drivers[0].instrument_widget.save_arduino_variables()
            self.inst_drivers[0].instrument_widget.btn_overwrite_olfaConfig_file()
            
            # TODO: add popup that shows where it saved it to
            
            # THIS ONLY WORKS NOW when you have just the single instrument
            self.logger.info('~~~~~~closing program~~~~~~~~')
            event.accept()



if __name__ == "__main__":
    # Create logger
    mainLogger = utils.createLogger(__name__)
    mainLogger.info('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    
    app1 = QApplication(sys.argv)
    
    # Default Channel objects
    channelObjs = []
    channelObjs.append(channelObj(name='olfa prototype',instrument='olfactometer'))
    channelObjs.append(channelObj(name='PID reading',instrument='NI-DAQ'))
    
    # Open main window
    mainWindow = mainGUI(channelObjs)
    size = mainWindow.sizeHint()
    mainWindow.resize(size)
    #mainLogger.debug('Done creating interface')
    mainWindow.show()

    # when closed: print setpoints or something

    sys.exit(app1.exec_())
    mainLogger.info('~~~~~~~~~~~~~~~done~~~~~~~~~~~~~~')