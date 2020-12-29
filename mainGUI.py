# ST 2020
# mainGUI.py

import sip, os, csv
from PyQt5.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QDialog, QTextEdit,
                             QScrollArea, QVBoxLayout, QWidget, QPushButton, QFormLayout, QSpinBox)
import utils, config, channel_stuff
from PyQt5.QtCore import QObject

currentDate = utils.currentDate
users = config.users
datafileLbl = config.datafileLbl
dataFileType = config.dataFileType
delimChar = config.delimChar


class mainGUI(QWidget):

    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.numChannels = len(self.channels)
        
        className = type(self).__name__
        self.logger = utils.createLogger(className)
        self.logger.debug('%s channels:', len(self.channels))
        
        self.createMainSettingsBox()
        self.createChannelSettingsBox()
        self.createDataFileBox()
        self.createChannelGroupBox()
        
        w = max(self.mainSettingsBox.sizeHint().width(),
                self.channelSettingsBox.sizeHint().width(),
                self.dataFileBox.sizeHint().width())
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
        self.setLayout(self.mainLayout)
        self.setWindowTitle('mainGUI')
    
    
    # TO CREATE THE GUI
    def createMainSettingsBox(self):
        self.mainSettingsBox = QGroupBox("Settings")

        userLbl = QLabel(text="User:",toolTip="just for logging")
        self.userSelectCb = QComboBox()
        self.userSelectCb.addItems(users)
        self.user = self.userSelectCb.currentText()
        self.userSelectCb.currentIndexChanged.connect(self.updateUser)

        layout = QFormLayout()
        layout.addRow(userLbl,self.userSelectCb)
        self.mainSettingsBox.setLayout(layout)

    def createChannelSettingsBox(self):
        self.channelSettingsBox = QGroupBox("Channel Settings")

        # box1: number of channels
        box1 = QGroupBox()
        numCLbl = QLabel("Number of channels:")
        self.numCBox = QSpinBox(value=self.numChannels,valueChanged=self.updateNumChans)
        layout1 = QFormLayout();    layout1.addRow(numCLbl,self.numCBox)
        box1.setLayout(layout1)
        
        # box2: channel info
        box2 = QGroupBox()
        lblRow = QHBoxLayout()
        recLbl = QLabel(text="Record");         lblRow.addWidget(recLbl)
        instLbl = QLabel(text="Instrument:");   lblRow.addWidget(instLbl)
        chanLbl = QLabel(text="Name:");         lblRow.addWidget(chanLbl)
        self.layout2 = QVBoxLayout()
        self.layout2.addLayout(lblRow)
        self.rows = []      # rows is here so we can save things ppl entered previously
        for r in range(self.numChannels):
            c = self.channels[r]
            row = QWidget();    row.setLayout(c.hLayout)
            self.rows.append(row)
            self.layout2.addWidget(row)
        box2.setLayout(self.layout2)
        
        self.channelUpdateBtn = QPushButton(text="Update",clicked=self.updateChannels,toolTip='Update display')

        layout = QVBoxLayout()
        layout.addWidget(box1)
        layout.addWidget(box2)
        layout.addWidget(self.channelUpdateBtn)
        self.channelSettingsBox.setLayout(layout)

    def createChannelGroupBox(self):
        self.channelGroupBox = QGroupBox("Channels")

        self.allChannels_layout = QVBoxLayout()
        self.c_Rows = []
        for i in self.channels:
            c_name = i.name
            c_instrument = i.instrument
            self.logger.debug('>> Creating channel for %s (%s)',c_instrument,c_name)
            channel_groupbox = channel_stuff.channelGroupBoxObject(c_name,c_instrument)
            if c_instrument != 'olfactometer':
                channel_groupbox.instrument_widget.setMaximumHeight(500)

            self.c_Rows.append(channel_groupbox)
            self.allChannels_layout.addWidget(channel_groupbox.instrument_widget)
        
        self.allChannelsWid = QWidget()
        self.allChannelsWid.setLayout(self.allChannels_layout)
        
        self.allChannelsScrollArea = QScrollArea()
        self.allChannelsScrollArea.setWidget(self.allChannelsWid)
        self.allChannelsScrollArea.setWidgetResizable(True)

        self.cs_layout = QVBoxLayout()
        #self.cs_layout.SetMinAndMaxSize
        self.cs_layout.addWidget(self.allChannelsScrollArea)
        self.channelGroupBox.setLayout(self.cs_layout)
    
    
    def updateNumChans(self):
        newNumChans = self.numCBox.value()
        if not self.numChannels == newNumChans:
            prevChannels = self.numChannels
            self.numChannels = newNumChans
            self.logger.debug('# of channels updated to %s',self.numChannels)

            # make new channels
            if newNumChans > prevChannels:
                numNewToMake = newNumChans-prevChannels
                for i in range(numNewToMake):
                    r_idx = prevChannels + i
                    numRows = len(self.rows)
                    if r_idx < numRows:       # if we've already had a row for this
                        self.layout2.addWidget(self.rows[r_idx])
                        self.channels.append(self.rows[r_idx])
                    else:
                        c = channel_stuff.channelObj(name='',instrument='')
                        self.channels.append(c)
                        row = QWidget()
                        row.setLayout(c.hLayout)
                        self.rows.append(row)
                        self.layout2.addWidget(row)
            
            # delete channels
            if prevChannels > newNumChans:
                numToDelete = prevChannels-newNumChans
                for i in range(numToDelete):
                    r_idx = prevChannels-1
                    self.layout2.removeWidget(self.rows[r_idx])
                    self.channels.pop(-1)

    def updateChannels(self):
        numPrev = len(self.c_Rows)
        numNew = len(self.channels)
        self.logger.info('updating channels')

        for idx in range(numPrev):  # for each of the previous channels
            if idx < numNew:        # if its a value within the newnum (will exist)
                newName = self.channels[idx].nameWidget.text()
                prevName = self.c_Rows[idx].name
                newInst = self.channels[idx].instWidget.currentText()
                prevInst = self.c_Rows[idx].instrument
                if newInst != prevInst:   # if instrument is different, make new
                    newChannel = channel_stuff.channelGroupBoxObject(name=newName,instrument=newInst)
                    self.allChannels_layout.removeWidget(self.c_Rows[idx].instrument_widget)
                    sip.delete(self.c_Rows[idx].instrument_widget)
                    self.c_Rows[idx] = newChannel
                    self.allChannels_layout.insertWidget(idx,self.c_Rows[idx].instrument_widget)
                else:
                    if newName != prevName:           # if instrument is same but name is different
                        self.c_Rows[idx].name = newName
                        self.c_Rows[idx].instrument_widget.setTitle(newName)

        if numPrev > numNew:        # delete extra channels
            num2Delete = numPrev - numNew
            for i in range(num2Delete):
                self.allChannels_layout.removeWidget(self.c_Rows[-1].instrument_widget)
                sip.delete(self.c_Rows[-1].instrument_widget)
                self.c_Rows.pop(-1)
        
        if numPrev < numNew:        # add new channels
            num2Make = numNew - numPrev
            for i in range(num2Make):
                newName = self.channels[i+numPrev].nameWidget.text()
                newInst = self.channels[i+numPrev].instWidget.currentText()
                self.channels[i+numPrev].name = newName
                self.channels[i+numPrev].instrument = newInst
                #newChan = self.channels[i+numPrev]
                newChannel = channel_stuff.channelGroupBoxObject(name=newName,instrument=newInst)
                self.c_Rows.append(newChannel)
                self.allChannels_layout.addWidget(newChannel.instrument_widget)
    

    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("DataFile")

        files = os.listdir()
        dataFiles = [x for x in files if datafileLbl in x]  # files with fileLbl in them
        if not dataFiles:
            self.lastFileNum = 0
        else:
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
        
        fileNameLbl = QLabel(text="File Name:")
        defFileName = utils.makeNewFileName(datafileLbl, self.lastFileNum)
        self.enterFileName = QLineEdit(text=defFileName)
        fileLayout = QHBoxLayout()
        fileLayout.addWidget(fileNameLbl)
        fileLayout.addWidget(self.enterFileName)
        self.recordButton = QPushButton(text="Create && Start Recording",checkable=True,clicked=self.clicked_record)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)
        self.dataFileOutputBox = QTextEdit(readOnly=True)

        layout = QFormLayout()
        layout.addRow(fileLayout)
        layout.addRow(self.recordButton,self.endRecordButton)
        layout.addRow(self.dataFileOutputBox)
        self.dataFileBox.setLayout(layout)
        
        self.endRecordButton.setEnabled(False)
    
    
    # FUNCTIONS THAT DO STUFF
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
            if not os.path.exists(self.enteredFileName):
                self.logger.info('Creating new datafile: %s',self.enteredFileName)
                File = self.enteredFileName, ' '
                Time = "File Created: ", str(currentDate + ' ' + utils.getTimeNow())
                DataHead = "Time","Instrument","Unit","Value"
                with open(self.enteredFileName,'a',newline='') as f:
                    writer = csv.writer(f,delimiter=delimChar)
                    writer.writerow(File)
                    writer.writerow("")
                    writer.writerow(Time)
                    writer.writerow("")
                    writer.writerow(DataHead)
            else:
                self.logger.info('Resuming recording to %s', self.enteredFileName)
                
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
            for chan in self.c_Rows:
                if chan.checkBoxLbl.text() in instrument:
                    if chan.checkBox.isChecked():
                        with open(self.enteredFileName,'a',newline='') as f:
                            writer = csv.writer(f, delimiter=delimChar)
                            writer.writerow(toWrite)
                        display = str(toWrite)
                        self.dataFileOutputBox.append(display[1:-1])
