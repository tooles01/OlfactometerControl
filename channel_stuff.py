# ST 2020
# channel_stuff.py

import sip
from serial.tools import list_ports
from PyQt5.QtWidgets import (QComboBox, QDialog, QGroupBox, QHBoxLayout, QCheckBox, QFormLayout, QTextEdit, 
                             QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget, QGridLayout)
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QPalette
import utils, config
from instrumentDrivers import olfactometer_driver, flowSensor_driver, NI_DAQ_driver

noPortMsg = config.noPortMsg
instTypes = config.instTypes

btnWidth = 50
textEditWidth = 125
whatDoOptions = ["Read & Write", "Read Only", "Write Only","Read & Record", "Don't read"]
baudrate = 9600

class channelObj(QObject):
    def __init__(self, port="", instrument="", name=""):
        super().__init__()
        self.port = port
        self.instrument = instrument
        self.name = name

        self.nameWidget = QLineEdit(text=name,toolTip="whatever you want the channel to be called")
        
        self.instWidget = QComboBox()
        self.instWidget.addItems(instTypes)
        AllItems = [self.instWidget.itemText(i) for i in range(self.instWidget.count())]
        if self.instrument in AllItems:
            i_idx = AllItems.index(self.instrument)
            self.instWidget.setCurrentIndex(i_idx)

class channelDialog(QDialog):

    def __init__(self, defChannelObjects):
        super().__init__()
        self.channels = defChannelObjects
        self.numChannels = len(defChannelObjects)
        
        className = type(self).__name__
        self.logger = utils.createLogger(className)

        self.createSettingsBox()
        self.createChannelEnterBoxes()
        self.done = QPushButton(text="Done",clicked=self.openMainGUI)
        
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.settingsBox)
        self.mainLayout.addWidget(self.channelEnterBoxes)
        self.mainLayout.addWidget(self.done)
        self.setLayout(self.mainLayout)

        self.setWindowTitle("Channel Setup Dialog")
    
    def createSettingsBox(self):
        self.settingsBox = QGroupBox()

        numCLbl = QLabel("Number of channels:")
        self.numCBox = QSpinBox(value=self.numChannels)
        numCBtn = QPushButton(text="Update",clicked=self.updateNumChannels)

        layout = QHBoxLayout()
        layout.addWidget(numCLbl)
        layout.addWidget(self.numCBox)
        layout.addWidget(numCBtn)
        self.settingsBox.setLayout(layout)
    
    def createChannelEnterBoxes(self):
        self.channelEnterBoxes = QGroupBox()

        instLbl = QLabel(text="Instrument:")
        chanLbl = QLabel(text="Name:")
        labelRow = QHBoxLayout()
        labelRow.addWidget(instLbl)
        labelRow.addWidget(chanLbl)

        layout = QFormLayout()
        layout.addRow(instLbl,chanLbl)
        
        prevChannels = self.channels
        self.channels = [None]*self.numChannels
        for i in range(self.numChannels):
            if i < len(prevChannels):    # if channel exists already, use prev name and instrument
                name_val = prevChannels[i].name
                inst_val = prevChannels[i].instrument
            else:
                name_val = ''
                inst_val = ''
            c = channelObj(name=name_val,instrument=inst_val)
            self.channels[i] = c
            layout.addRow(c.instWidget,c.nameWidget)
        
        self.channelEnterBoxes.setLayout(layout)

    def updateNumChannels(self): ##** THIS ALSO REFRESHES COM PORTS bc u make the objects again
        self.numChannels = self.numCBox.value()
        self.logger.info("Updating number of channels to %s",self.numChannels)

        self.mainLayout.removeWidget(self.channelEnterBoxes)
        sip.delete(self.channelEnterBoxes)
        self.createChannelEnterBoxes()
        self.mainLayout.insertWidget(1,self.channelEnterBoxes)
    
    def openMainGUI(self):
        for i in range(self.numChannels):
            self.channels[i].instrument = self.channels[i].instWidget.currentText()
            self.channels[i].name = self.channels[i].nameWidget.text()
        self.logger.debug("Closing window")
        self.accept()


class channelGroupBoxObject(QGroupBox):

    def __init__(self, name="", instrument=""):
        super().__init__()
        self.name = name
        self.instrument = instrument
        self.whatDo = whatDoOptions[0]
        
        self.checkBox = QCheckBox(checked=True)
        self.checkBoxLbl = QLabel(text=self.name)

        className = type(self).__name__
        loggerName = className + ' (' + self.name + ')'
        self.logger = utils.createLogger(loggerName)

        self.createInfoSpace()
        self.createInstrumentWidget()

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.infoSpace)
        self.layout.addWidget(self.instrument_widget)
        self.setLayout(self.layout)
    

    # FUNCTIONS TO CREATE GUI
    def createInfoSpace(self):
        self.infoSpace = QWidget()

        self.nameLbl = QLabel(text="Name:")
        self.nameWidget = QLineEdit(text=self.name,readOnly=True)
        self.nameEditBtn = QPushButton(text="Edit",checkable=True,toggled=self.nameEditToggled)
        self.nameEditBtn.setFixedWidth(btnWidth)
        self.nameWid_palette = QPalette()
        self.nonEditColor = self.palette().midlight().color()
        self.backToWhite = self.palette().base().color()
        self.nameWid_palette.setColor(QPalette.Base,self.nonEditColor)
        self.nameWidget.setPalette(self.nameWid_palette)
        self.nameWidget.returnPressed.connect(lambda: self.nameEditBtn.toggle())
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.nameWidget)
        name_layout.addWidget(self.nameEditBtn)

        self.instLbl = QLabel(text="Instrument:")
        self.instWidget = QComboBox()
        self.instWidget.addItems(instTypes)
        AllItems = [self.instWidget.itemText(i) for i in range(self.instWidget.count())]
        if self.instrument in AllItems:
            i_idx = AllItems.index(self.instrument)
            self.instWidget.setCurrentIndex(i_idx)
        
        self.updateButton = QPushButton(text='Update',clicked=self.update)
        
        layout1 = QFormLayout()
        layout1.addRow(self.nameLbl,name_layout)
        layout1.addRow(self.instLbl,self.instWidget)
        layout1.addRow(self.updateButton)
        self.infoSpace.setLayout(layout1)
        self.infoSpace.setFixedWidth(210)
    
    def createInstrumentWidget(self):        
        if self.instrument == 'olfactometer':
            self.instrument_widget = olfactometer_driver.olfactometer(self.name)
        elif self.instrument == 'flow sensor':
            self.instrument_widget = flowSensor_driver.flowSensor(self.name)
        elif self.instrument == 'NI-DAQ':
            self.instrument_widget = NI_DAQ_driver.NiDaq(self.name)
        else:
            self.logger.error('No module exists for selected instrument: %s',self.instrument)
            self.instrument_widget = QGroupBox("empty widget for " + self.instrument)
    
    
    # ACTUAL FUNCTIONS THE THING NEEDS
    def nameEditToggled(self):
        if self.nameEditBtn.isChecked():
            self.nameWidget.setReadOnly(False)
            self.nameWid_palette.setColor(QPalette.Base, self.backToWhite)
            self.nameWidget.setPalette(self.nameWid_palette)
            self.nameEditBtn.setText("Done")
            self.nameWidget.setEnabled(True)
        else:
            newName = self.nameWidget.text()
            if not self.name == newName:
                self.name = newName
                self.nameWidget.setText(self.name)
                self.instrument_widget.updateName(newName)
                self.logger.debug('name changed to %s', self.name)
            self.nameWidget.setReadOnly(True)
            self.nameWid_palette.setColor(QPalette.Base, self.nonEditColor)
            self.nameWidget.setPalette(self.nameWid_palette)
            self.nameEditBtn.setText("Edit")
            self.nameWidget.setEnabled(False)
    
    def update(self):
        newInst = self.instWidget.currentText()
        
        if not self.instrument == newInst:
            self.instrument = newInst
            self.logger.debug('inst changed to %s', self.instrument)

            self.layout.removeWidget(self.instrument_widget)
            sip.delete(self.instrument_widget)
            self.createInstrumentWidget()
            self.layout.addWidget(self.instrument_widget)
