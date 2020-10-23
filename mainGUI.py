# ST 2020
# mainGUI.py

import sip, os, csv
from PyQt5.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QDialog, QTextEdit,
                             QScrollArea, QVBoxLayout, QWidget, QPushButton, QFormLayout)
import utils, config, channel_stuff

users = config.users
defFileType = config.defFileType
delimChar = config.delimChar
currentDate = utils.currentDate

fileLbl = 'exp01'


class mainGUI(QWidget):

    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        
        className = type(self).__name__
        self.logger = utils.createLogger(className)
        self.logger.info('%s channels:', len(self.channels))
        
        self.createMainSettingsBox()
        self.createChannelGroupBox()
        self.createDataFileBox()
        self.dataFileBox.setFixedWidth(330)

        col1 = QVBoxLayout()
        col1.addWidget(self.mainSettingsBox)
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
        self.channelChangeBtn = QPushButton(text="Change # of Channels",clicked=self.changeNumChannels)

        layout = QFormLayout()
        layout.addRow(userLbl,self.userSelectCb)
        layout.addRow(self.channelChangeBtn)
        self.mainSettingsBox.setLayout(layout)

    def createChannelGroupBox(self):
        self.channelGroupBox = QGroupBox("Channels")

        self.c_Rows = []
        for i in self.channels:
            c_name = i.name
            c_instrument = i.instrument
            self.logger.info('>> Creating channel for %s (%s)',c_instrument,c_name)
            
            channel_groupbox = channel_stuff.channelGroupBoxObject(c_name,c_instrument)
            self.c_Rows.append(channel_groupbox)
            num = self.c_Rows.index(channel_groupbox)
            self.c_Rows[num].setTitle('Channel ' + str(num+1))
        
        self.allChannels_layout = QVBoxLayout()
        for i in self.c_Rows:
            self.allChannels_layout.addWidget(i)
        
        self.allChannelsWid = QWidget()
        self.allChannelsWid.setLayout(self.allChannels_layout)
        
        self.allChannelsScrollArea = QScrollArea()
        self.allChannelsScrollArea.setWidget(self.allChannelsWid)

        self.cs_layout = QVBoxLayout()
        self.cs_layout.addWidget(self.allChannelsScrollArea)
        self.channelGroupBox.setLayout(self.cs_layout)
    
    def createDataFileBox(self):
        self.dataFileBox = QGroupBox("DataFile")

        self.whoRecordBox = QGroupBox()
        self.whoRecord_layout = QFormLayout()
        self.whoRecord_layout.addWidget(QLabel(text="Record from:"))
        for c in self.c_Rows:
            self.whoRecord_layout.addRow(c.checkBox,c.checkBoxLbl)
        self.whoRecordBox.setLayout(self.whoRecord_layout)

        files = os.listdir()
        dataFiles = [x for x in files if fileLbl in x]  # files with fileLbl in them
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
        defFileName = utils.makeNewFileName(fileLbl, self.lastFileNum)
        self.enterFileName = QLineEdit(text=defFileName)
        self.recordButton = QPushButton(text="Create && Start Recording",checkable=True,clicked=self.clicked_record)
        hint = self.recordButton.sizeHint()
        self.recordButton.setFixedSize(hint)
        self.endRecordButton = QPushButton(text="End Recording",clicked=self.clicked_endRecord)
        self.dataFileOutputBox = QTextEdit(readOnly=True)

        layout = QFormLayout()
        layout.addRow(self.whoRecordBox)
        layout.addRow(fileNameLbl,self.enterFileName)
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
    
    def changeNumChannels(self):
        self.logger.debug('changing # of channels')
        
        chSet_dlg = channel_stuff.channelDialog(self.channels)
        if chSet_dlg.exec_() == QDialog.Accepted:
            self.channels = chSet_dlg.channels
         
            numPrev = len(self.c_Rows)
            numNew = len(self.channels)
            for idx in range(numPrev):  # for each of the previous channels
                if idx < numNew:        # if it's a value within the newnum
                    newChan = self.channels[idx]
                    prevChan = self.c_Rows[idx]
                    if newChan.instrument != prevChan.instrument:   # if instrument is different, make new
                        newChannel = channel_stuff.channelGroupBoxObject(name=newChan.name,instrument=newChan.instrument)
                        self.allChannels_layout.removeWidget(self.c_Rows[idx])
                        sip.delete(self.c_Rows[idx])
                        self.c_Rows[idx] = newChannel
                        self.allChannels_layout.insertWidget(idx,self.c_Rows[idx])
                        self.logger.info('Channel %s updated to: %s (%s)', idx, newChan.instrument, newChan.name)
                    else:
                        if newChan.name != prevChan.name:   # if instrument is same but name is different, update name
                            self.c_Rows[idx].name = newChan.name
                            self.logger.info('Channel %s (%s) name updated to %s', idx,newChan.instrument,newChan.name)
            
            if numPrev > numNew:    # delete extra channels
                num2Delete = numPrev - numNew
                for i in range(num2Delete):
                    self.allChannels_layout.removeWidget(self.c_Rows[-1])
                    sip.delete(self.c_Rows[-1])
                    self.c_Rows.pop(-1)
                    self.logger.info('Channel %s deleted', numPrev-i)
            
            if numPrev < numNew:    # add new channels
                numChansToMake = numNew - numPrev
                for i in range(numChansToMake):
                    newChan = self.channels[i+numPrev]
                    newChannel = channel_stuff.channelGroupBoxObject(name=newChan.name,instrument=newChan.instrument)
                    self.c_Rows.append(newChannel)
                    self.allChannels_layout.addWidget(newChannel)
                    self.logger.info('Created channel %s: %s (%s)', numPrev+i,newChan.instrument,newChan.name)

            numRows = self.whoRecord_layout.count()
            for i in reversed(range(numRows)):
                r = self.whoRecord_layout.itemAt(i)
                self.whoRecord_layout.removeItem(r)
                sip.delete(r)
            
            self.whoRecord_layout.addWidget(QLabel(text="Record from:"))
            for i in self.c_Rows:
                self.whoRecord_layout.addRow(i.checkBox,i.checkBoxLbl)

    
    
    def clicked_record(self, checked):
        if checked:
            self.recordButton.setText("Pause Recording")
            self.endRecordButton.setEnabled(True)
            self.enteredFileName = self.enterFileName.text() + defFileType
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

    def clicked_endRecord(self, checked):
        self.logger.info('Ended recording to %s', self.enteredFileName)
        if self.recordButton.isChecked() == True:
            self.recordButton.setChecked(False)
        
        self.lastFileNum = self.lastFileNum + 1
        newFileName = utils.makeNewFileName(fileLbl,self.lastFileNum)

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
                            if unit == 'OV':
                                print(utils.getTimeNow() + '\trecorded to file')
                        display = str(toWrite)
                        self.dataFileOutputBox.append(display[1:-1])
