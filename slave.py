# ST 2020
# slave device - contains vials

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
import vial

class Slave(QGroupBox):

    def __init__(self, parent, slaveName, numVials, sensorTypes):
        super().__init__()
        
        self.slaveName = slaveName
        self.numVials = numVials
        self.sensorTypes = sensorTypes

        layout = QVBoxLayout()
        self.vials = []
        for x in range(numVials):
            vialNum = x+1
            sensorType = sensorTypes[vialNum]
            if not sensorType:
                sensorType = sensorTypes[0]
                print("no sensor type listed for slave " + self.slaveName + " vial " + str(vialNum) + ": using default sensor type")
            v_vial = vial.Vial(parent,slaveName,vialNum,sensorType)
            self.vials.append(v_vial)
            layout.addWidget(v_vial)

        title = "Slave " + self.slaveName
        self.setTitle(title)
        self.setLayout(layout)

