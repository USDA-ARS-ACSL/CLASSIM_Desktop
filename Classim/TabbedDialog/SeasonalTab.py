from sqlite3 import Date
import subprocess
import time
import os
import pandas as pd
import sys
import re
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QPushButton, \
                            QSpacerItem, QSizePolicy, QHeaderView, QRadioButton, QButtonGroup, QMenu, QCheckBox, QGridLayout, QGroupBox, \
                            QHeaderView, QCalendarWidget
from PyQt5.QtCore import QFile, QTextStream, pyqtSignal, QCoreApplication
from CustomTool.custom1 import *
from CustomTool.UI import *
from CustomTool.generateModelInputFiles import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from subprocess import Popen
from dateutil.parser import parse
#import matplotlib
#matplotlib.use('Qt5Agg')

global classimDir
global runDir
global storeDir


classimDir = getClassimDir()
runDir = os.path.join(classimDir,'run')
storeDir = os.path.join(runDir,'store')

# Create soil executable
createsoilexe = os.path.join(classimDir, 'createsoilfiles.exe')

# maize model executables
maizsimexe =  os.path.join(classimDir,'2dmaizsim.exe')

# Potato model executable
spudsimexe =  os.path.join(classimDir, '2dspudsim.exe')

# Soybean model executable
glycimexe =  os.path.join(classimDir, '2dglycim.exe')

# Cotton model executable
gossymexe =  os.path.join(classimDir, '2dgossym.exe')

# Flag to tell script if output files should be removed, the default is 1 so they are removed
remOutputFilesFlag = 1

## This should always be there
if not os.path.exists(storeDir):
    print('SeasonalTab Error: Missing storeDir')

class Seasonal_Widget(QWidget):
    # Add a signal
    rotationsig = pyqtSignal(int)    
    exsystemsig = pyqtSignal(int)
    
    changedValue = pyqtSignal(int)
    checkbox_checked = pyqtSignal()
    def __init__(self):
        super(Seasonal_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
      # self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
       #self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("seasonal")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.tab_summary = QTextEdit("Pick individual entries to create your simulation.  You have the ability \
to run more than one simulation, to add or delete a simulation select the entire row and right click. It will \
open a dialog box with simple instructions. Once changes are done, please make sure to press the Run button to \
start your simulation.")        
        self.tab_summary.setReadOnly(True)        
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame) 
        self.tab_summary.setMaximumHeight(50) # need it     
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink="<a href=\"https://youtu.be/eL-0s_qccuQ\">Click here \
                to watch the Seasonal Tab Video Tutorial</a><br>"
        self.seasonalVidlabel=QLabel()
        self.seasonalVidlabel.setOpenExternalLinks(True)
        self.seasonalVidlabel.setText(urlLink)

        self.vl1 = QVBoxLayout()
        self.hl1 = QHBoxLayout()
        self.mainlayout1 = QGridLayout()
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hl1.addWidget(self.tab_summary)     
        self.hl1.setSpacing(0)   

        self.vl1.setContentsMargins(0,0,0,0)

        self.rgroupbox = QGroupBox("Simulator")
        self.stationTypeCombo = QComboBox()        
        self.weatherCombo = QComboBox()        
        self.expTreatCombo = QComboBox()  

       
        self.ExpSys = QCheckBox("Expert System")
        self.ExpSys.setChecked(False)
       
        self.selectExpSys()

        self.inseason_date = None
        self.ExpSys.stateChanged.connect(self.SelectInSeaDate)

       
        sitelists = read_sitedetailsDB()
        self.siteCombo = QComboBox()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
            self.siteCombo.addItem(item)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
        soillists = read_soilDB()
        self.soilCombo = QComboBox()
        self.soilCombo.addItem("Select from list")
        for key in soillists:            
            self.soilCombo.addItem(key)
        
        croplists = read_cropDB()
        self.cropCombo = QComboBox()          
        self.cropCombo.addItem("Select from list")
        for val in croplists:
            self.cropCombo.addItem(val)
        self.cropCombo.currentIndexChanged.connect(self.showexperimentcombo)
                
        # Create and populate waterStress combo
        self.comboWaterStress = QComboBox()          
        self.comboWaterStress.addItem("Yes") # val = 0
        self.comboWaterStress.addItem("No") # val = 1

        # Create and populate nitroStress combo
        self.comboNitroStress = QComboBox()          
        self.comboNitroStress.addItem("Yes") # val = 0
        self.comboNitroStress.addItem("No") # val = 1

        # Create and populate Temp Variance combo
        self.comboTempVar = QComboBox()
        for temp in range(-10,11):
            self.comboTempVar.addItem(str(temp))
        self.comboTempVar.setCurrentIndex(self.comboTempVar.findText("0"))

        # Create and populate Rain Variance combo
        self.comboRainVar = QComboBox()
        for rain in range(-100,105,5):
            self.comboRainVar.addItem(str(rain))
        self.comboRainVar.setCurrentIndex(self.comboRainVar.findText("0"))

        # Create and populate CO2 Variance combo
        self.comboCO2Var = QComboBox()
        self.comboCO2Var.addItem("None")
        for co2 in range(280,1010,10):
            self.comboCO2Var.addItem(str(co2))
        self.comboCO2Var.setCurrentIndex(self.comboCO2Var.findText("None"))

        self.tablebasket = QTableWidget()
        self.tablebasket.setVisible(True)        
        self.tablebasket.horizontalScrollBar().setStyleSheet("QScrollBar:: horizontal {border: 2px solid grey; background: lightgray; height: 15px; \
                                                             margin: 0px 20px 0 20px;} \
                                                             QScrollBar::handle:horizontal {background: #32CC99; min-width: 20px;} \
                                                             QScrollBar::add-line:horizontal {border: 2px solid grey; background: none; width: 20px; \
                                                             subcontrol-position: right; subcontrol-origin: margin;} \
                                                             QScrollBar::sub-line:horizontal {border: 2px solid grey; background: none; width: 20px; \
                                                             subcontrol-position: left; subcontrol-origin: margin;} \
                                                             QScrollBar::left-arrow:horizontal, {border: 2px solid grey; width: 3px; height: 3px; \
                                                             background: white;} \
                                                             QScrollBar::right-arrow:horizontal, {border: 2px solid grey; width: 3px; height: 3px; \
                                                             background: white;}")
        self.tablebasket.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tablebasket.verticalHeader().customContextMenuRequested.connect(self.tableverticalheader_popup)
      #  self.tablebaskethheaderlabels = ["Expert System", "Site","Soil","Station Name","Weather","Crop","Experiment/Treatment", "StartYear","EndYear","Water\nStress","Nitrogen\nStress","Temp\nVariance (oC)","Rain\nVariance (%)","CO2\nVariance (ppm)"]
        self.tablebaskethheaderlabels = ["Site","Soil","Station Name","Weather","Crop","Experiment/Treatment", "StartYear","EndYear","Water\nStress","Nitrogen\nStress","Temp\nVariance (oC)","Rain\nVariance (%)","CO2\nVariance (ppm)"]
         
        self.tablebasket.clear()
        self.tablebasket.setRowCount(0)
        self.tablebasket.setRowCount(1)
        self.tablebasket.setColumnCount(13)
        self.tablebasket.setAlternatingRowColors(True)
        self.tablebasket.setHorizontalHeaderLabels(self.tablebaskethheaderlabels)

        self.tablebasket.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(5,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(6,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(7,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(8,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(9,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(10,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(11,QHeaderView.ResizeToContents)
        self.tablebasket.horizontalHeader().setSectionResizeMode(12,QHeaderView.ResizeToContents)
       # self.tablebasket.horizontalHeader().setSectionResizeMode(13,QHeaderView.ResizeToContents)
        '''
        self.tablebasket.setCellWidget(0,0,self.ExpSys)
        self.tablebasket.setCellWidget(0,1,self.siteCombo)
        self.tablebasket.setCellWidget(0,2,self.soilCombo)
        self.tablebasket.setCellWidget(0,3,self.stationTypeCombo)
        self.tablebasket.setCellWidget(0,4,self.weatherCombo)
        self.tablebasket.setCellWidget(0,5,self.cropCombo)
        self.tablebasket.setCellWidget(0,6,self.expTreatCombo)
        self.tablebasket.setCellWidget(0,9,self.comboWaterStress)
        self.tablebasket.setCellWidget(0,10,self.comboNitroStress)
        self.tablebasket.setCellWidget(0,11,self.comboTempVar)
        self.tablebasket.setCellWidget(0,12,self.comboRainVar)
        self.tablebasket.setCellWidget(0,13,self.comboCO2Var)
        '''
       
        self.tablebasket.setCellWidget(0,0,self.siteCombo)
        self.tablebasket.setCellWidget(0,1,self.soilCombo)
        self.tablebasket.setCellWidget(0,2,self.stationTypeCombo)
        self.tablebasket.setCellWidget(0,3,self.weatherCombo)
        self.tablebasket.setCellWidget(0,4,self.cropCombo)
        self.tablebasket.setCellWidget(0,5,self.expTreatCombo)
        self.tablebasket.setCellWidget(0,8,self.comboWaterStress)
        self.tablebasket.setCellWidget(0,9,self.comboNitroStress)
        self.tablebasket.setCellWidget(0,10,self.comboTempVar)
        self.tablebasket.setCellWidget(0,11,self.comboRainVar)
        self.tablebasket.setCellWidget(0,12,self.comboCO2Var)

        self.rlabel = QLabel("Simulator")
        self.simStatus = QLabel("")
        self.simStatus.setWordWrap(True)
        self.buttonrun = QPushButton("Run")
        self.buttonrun.setObjectName("buttonrun")
        self.buttonreset = QPushButton("Reset")
        self.buttonreset.setObjectName("buttonreset") 
       
        # Output hourly/daily
        self.step_hourly = QRadioButton("Hourly")
        self.step_daily = QRadioButton("Daily")
        self.step_hourly.setObjectName("step_hourly")
        self.step_daily.setObjectName("step_daily")
        self.step_g = QButtonGroup()

        self.step_hourly.setChecked(True)
        self.step_g.addButton(self.step_hourly,1)
        self.step_g.addButton(self.step_daily,2)

        self.subgrid1 = QGridLayout()
        self.subgrid1.addWidget(self.tablebasket,2,0,3,4)
        self.subgrid1.addWidget(self.ExpSys,5,0)
        self.SimulationFlabel = QLabel("Simulation Output Interval")
        self.subgrid1.addWidget(self.SimulationFlabel,6,0)
        self.subgrid1.addWidget(self.step_hourly,6,1)
        self.subgrid1.addWidget(self.step_daily,6,2)
        
        self.SimulationFlabel.setObjectName("SimulationFlabel")
       
        self.subgrid1.addWidget(self.buttonrun,7,0)
        self.subgrid1.addWidget(self.buttonreset,7,1)
        self.subgrid1.addWidget(self.simStatus,8,0,1,5)
        
        self.buttonrun.clicked.connect(self.buttonrunclicked)
        self.buttonreset.clicked.connect(self.reset)
        self.tablebasket.resizeColumnsToContents()
        self.tablebasket.resizeRowsToContents()  
              
        self.hl2 = QHBoxLayout()                
        self.rgroupbox.setLayout(self.subgrid1)

        self.hl2.addWidget(self.rgroupbox)

       
        
        
        self.vl1.addLayout(self.hl1)
        self.vl1.addWidget(self.seasonalVidlabel)
        self.vl1.addWidget(self.helpcheckbox)
     
        self.vl1.addLayout(self.hl2)
        self.vl1.addStretch(1)
        
        self.mainlayout1.addLayout(self.vl1,0,0)
        self.mainlayout1.setColumnStretch(0,3)
        self.mainlayout1.addWidget(self.faqtree,0,4)
        self.setLayout(self.mainlayout1)
  
   


    def selectExpSys(self):
        if self.ExpSys.isChecked():
            self.checkbox_checked.emit()            
       
            
           # self.emit_signal()

   # def emit_signal(self, state):
                   # Emit the signal when the checkbox is not checked
     #       self.checkbox_checked.emit()

    def reset(self):
        self.ExpSys.setChecked(False)

        while self.tablebasket.rowCount() > 0:
            self.tablebasket.removeRow(0)        
        self.tablebasket.insertRow(0)

        self.stationTypeCombo = QComboBox()        
        self.weatherCombo = QComboBox()        
        self.expTreatCombo = QComboBox()          

        sitelists = read_sitedetailsDB()
        self.siteCombo = QComboBox()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
            self.siteCombo.addItem(item)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
        soillists = read_soilDB()
        self.soilCombo = QComboBox()
        self.soilCombo.addItem("Select from list")
        for key in soillists:            
            self.soilCombo.addItem(key)
        
        croplists = read_cropDB()
        self.cropCombo = QComboBox()          
        self.cropCombo.addItem("Select from list")
        for val in croplists:
            self.cropCombo.addItem(val)
        self.cropCombo.currentIndexChanged.connect(self.showexperimentcombo)
                
        # Create and populate waterStress combo
        self.comboWaterStress = QComboBox()          
        self.comboWaterStress.addItem("Yes") # val = 0
        self.comboWaterStress.addItem("No") # val = 1

        # Create and populate nitroStress combo
        self.comboNitroStress = QComboBox()          
        self.comboNitroStress.addItem("Yes") # val = 0
        self.comboNitroStress.addItem("No") # val = 1
        
        # Create and populate Temp Variance combo
        self.comboTempVar = QComboBox()
        for temp in range(-10,11):
            self.comboTempVar.addItem(str(temp))
        self.comboTempVar.setCurrentIndex(self.comboTempVar.findText("0"))

        # Create and populate Rain Variance combo
        self.comboRainVar = QComboBox()
        for rain in range(-100,105,5):
            self.comboRainVar.addItem(str(rain))
        self.comboRainVar.setCurrentIndex(self.comboRainVar.findText("0"))

        # Create and populate CO2 Variance combo
        self.comboCO2Var = QComboBox()
        self.comboCO2Var.addItem("None")
        for co2 in range(280,1010,10):
            self.comboCO2Var.addItem(str(co2))
        self.comboCO2Var.setCurrentIndex(self.comboCO2Var.findText("None"))

       # self.tablebasket.setCellWidget(0,0,self.ExpSys)
        self.tablebasket.setCellWidget(0,0,self.siteCombo)
        self.tablebasket.setCellWidget(0,1,self.soilCombo)
        self.tablebasket.setCellWidget(0,2,self.stationTypeCombo)
        self.tablebasket.setCellWidget(0,3,self.weatherCombo)
        self.tablebasket.setCellWidget(0,4,self.cropCombo)
        self.tablebasket.setCellWidget(0,5,self.expTreatCombo)
        self.tablebasket.setCellWidget(0,8,self.comboWaterStress)
        self.tablebasket.setCellWidget(0,9,self.comboNitroStress)
        self.tablebasket.setCellWidget(0,10,self.comboTempVar)
        self.tablebasket.setCellWidget(0,11,self.comboRainVar)
        self.tablebasket.setCellWidget(0,12,self.comboCO2Var)

       
        


    def tableverticalheader_popup(self, pos):
        '''
        pop menu items will come here
        '''
        if (len(self.tablebasket.selectionModel().selectedRows()) !=1):
            return True

        menu = QMenu()
        insertrowbelowaction = menu.addAction("Insert row below")
        deletethisrowaction = menu.addAction("Delete this row")
        action = menu.exec_(QtGui.QCursor.pos())
        
        if action == insertrowbelowaction:
            self.insertrowbelow()

        if action == deletethisrowaction:
            self.deletethisrow()


    def deletethisrow(self):
        '''
        deletes the current row
        '''
        crow = self.tablebasket.currentRow()
        self.tablebasket.removeRow(crow)        
        howmanyrows = self.tablebasket.rowCount()
        if howmanyrows == 0:
            self.tablebasket.insertRow(howmanyrows)
            self.weatherCombo = QComboBox()        
            self.expTreatCombo = QComboBox()          
            self.comboNitroStress = QComboBox()          

            sitelists = read_sitedetailsDB()
            self.siteCombo = QComboBox()
            self.siteCombo.addItem("Select from list")
            for item in sitelists: 
               self.siteCombo.addItem(item)
            self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
            self.soillists = read_soilDB()
            self.soilCombo = QComboBox()
            self.soilCombo.addItem("Select from list")
            for key in self.soillists:            
                self.soilCombo.addItem(key)
        
            stationtypelists = read_weather_metaDB()
            self.stationTypeCombo = QComboBox()        
            self.stationTypeCombo.addItem("Select from list")
            for key in stationtypelists:
                if stationtypelists[key] != "Add New Station Name":
                    self.stationTypeCombo.addItem(stationtypelists[key])
                
            croplists = read_cropDB()
            self.cropCombo = QComboBox()          
            self.cropCombo.addItem("Select from list")
            for val in croplists:
                self.cropCombo.addItem(val)
            self.cropCombo.currentIndexChanged.connect(self.showexperimentcombo)

            # Create and populate waterStress combo
            self.comboWaterStress = QComboBox()          
            self.comboWaterStress.addItem("Yes") # val = 0
            self.comboWaterStress.addItem("No") # val = 1

            # Create and populate nitroStress combo
            self.comboNitroStress = QComboBox()          
            self.comboNitroStress.addItem("Yes") # val = 0
            self.comboNitroStress.addItem("No") # val = 1
        
            # Create and populate Temp Variance combo
            self.comboTempVar = QComboBox()
            for temp in range(-10,11):
                self.comboTempVar.addItem(str(temp))
            self.comboTempVar.setCurrentIndex(self.comboTempVar.findText("0"))

            # Create and populate Rain Variance combo
            self.comboRainVar = QComboBox()
            for rain in range(-100,105,5):
                self.comboRainVar.addItem(str(rain))
            self.comboRainVar.setCurrentIndex(self.comboRainVar.findText("0"))

            # Create and populate CO2 Variance combo
            self.comboCO2Var = QComboBox()
            self.comboCO2Var.addItem("None")
            for co2 in range(280,1010,10):
                self.comboCO2Var.addItem(str(co2))
            self.comboCO2Var.setCurrentIndex(self.comboCO2Var.findText("None"))

          #  self.tablebasket.setCellWidget(0,0,self.ExpSys)
            self.tablebasket.setCellWidget(0,0,self.siteCombo)
            self.tablebasket.setCellWidget(0,1,self.soilCombo)
            self.tablebasket.setCellWidget(0,2,self.stationTypeCombo)
            self.tablebasket.setCellWidget(0,3,self.weatherCombo)
            self.tablebasket.setCellWidget(0,4,self.cropCombo)
            self.tablebasket.setCellWidget(0,5,self.expTreatCombo)
            self.tablebasket.setCellWidget(0,8,self.comboWaterStress)
            self.tablebasket.setCellWidget(0,9,self.comboNitroStress)
            self.tablebasket.setCellWidget(0,10,self.comboTempVar)
            self.tablebasket.setCellWidget(0,11,self.comboRainVar)
            self.tablebasket.setCellWidget(0,12,self.comboCO2Var)


    def insertrowbelow(self):
        '''
        insert row below
        '''
        crow = self.tablebasket.currentRow()
        newrowindex = crow + 1

        self.tablebasket.insertRow(newrowindex)
        self.weatherCombo = QComboBox()        
        self.expTreatCombo = QComboBox()          

        sitelists = read_sitedetailsDB()
        self.siteCombo = QComboBox()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
           self.siteCombo.addItem(item)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
        self.soillists = read_soilDB()
        self.soilCombo = QComboBox()
        self.soilCombo.addItem("Select from list")
        for key in self.soillists:            
            self.soilCombo.addItem(key)
        
        stationtypelists = read_weather_metaDB()
        self.stationTypeCombo = QComboBox()        
        self.stationTypeCombo.addItem("Select from list")
        for key in stationtypelists:
            if stationtypelists[key] != "Add New Station Name":
                self.stationTypeCombo.addItem(stationtypelists[key])
                
        croplists = read_cropDB()
        self.cropCombo = QComboBox()          
        self.cropCombo.addItem("Select from list")
        for val in croplists:
            self.cropCombo.addItem(val)
        self.cropCombo.currentIndexChanged.connect(self.showexperimentcombo)

        # Create and populate waterStress combo
        self.comboWaterStress = QComboBox()          
        self.comboWaterStress.addItem("Yes") # val = 0
        self.comboWaterStress.addItem("No") # val = 1

        # Create and populate nitroStress combo
        self.comboNitroStress = QComboBox()          
        self.comboNitroStress.addItem("Yes") # val = 0
        self.comboNitroStress.addItem("No") # val = 1
        
        # Create and populate Temp Variance combo
        self.comboTempVar = QComboBox()
        for temp in range(-10,11):
            self.comboTempVar.addItem(str(temp))
        self.comboTempVar.setCurrentIndex(self.comboTempVar.findText("0"))

        # Create and populate Rain Variance combo
        self.comboRainVar = QComboBox()
        for rain in range(-100,105,5):
            self.comboRainVar.addItem(str(rain))
        self.comboRainVar.setCurrentIndex(self.comboRainVar.findText("0"))

        # Create and populate CO2 Variance combo
        self.comboCO2Var = QComboBox()
        self.comboCO2Var.addItem("None")
        for co2 in range(280,1010,10):
            self.comboCO2Var.addItem(str(co2))
        self.comboCO2Var.setCurrentIndex(self.comboCO2Var.findText("None"))

     #   self.tablebasket.setCellWidget(newrowindex,0,self.ExpSys)
        self.tablebasket.setCellWidget(newrowindex,0,self.siteCombo)
        self.tablebasket.setCellWidget(newrowindex,1,self.soilCombo)
        self.tablebasket.setCellWidget(newrowindex,2,self.stationTypeCombo)
        self.tablebasket.setCellWidget(newrowindex,3,self.weatherCombo)
        self.tablebasket.setCellWidget(newrowindex,4,self.cropCombo)
        self.tablebasket.setCellWidget(newrowindex,5,self.expTreatCombo)
        self.tablebasket.setItem(newrowindex,6,QTableWidgetItem(""))
        self.tablebasket.setItem(newrowindex,7,QTableWidgetItem(""))
        self.tablebasket.setCellWidget(newrowindex,8,self.comboWaterStress)
        self.tablebasket.setCellWidget(newrowindex,9,self.comboNitroStress)
        self.tablebasket.setCellWidget(newrowindex,10,self.comboTempVar)
        self.tablebasket.setCellWidget(newrowindex,11,self.comboRainVar)
        self.tablebasket.setCellWidget(newrowindex,12,self.comboCO2Var)


    def showstationtypecombo(self):
        site = self.siteCombo.currentText()
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        
        self.stationTypeCombo = QComboBox()        
        stationtypelists = read_weather_metaDBforsite(site)        
        self.stationTypeCombo.addItem("Select from list") 
        for key in stationtypelists:
            if stationtypelists[key] != "Add New Station Name":
                self.stationTypeCombo.addItem(stationtypelists[key])
        self.stationTypeCombo.currentIndexChanged.connect(self.showweathercombo)

        self.tablebasket.setCellWidget(crow,2,self.stationTypeCombo)
        return True


    def showweathercombo(self):
        stationtype = self.stationTypeCombo.currentText()
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        
        self.weatherCombo = QComboBox()        
        weather_id_lists = read_weather_id_forstationtype(stationtype)
            
        self.weatherCombo.addItem("Select from list") 
        for item in weather_id_lists:
            if item != "Add New Station Name":
                self.weatherCombo.addItem(item)

        self.tablebasket.setCellWidget(crow,3,self.weatherCombo)
        return True

    def showexperimentcombo(self):
        crop = self.cropCombo.currentText()
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        stationtype = self.stationTypeCombo.currentText()
        weather_id= self.weatherCombo.currentText()
       # weatherID = read_weather_id_forstationtype(stationtype)
        rlist_max, rlist_min = read_weatherDate_forstationtype(stationtype,weather_id)
      #  print("rlist_min, rlist_max: ",  rlist_min, rlist_max )
       # print(type(rlist_min))

        r_min = parse(rlist_min)
        r_max = parse(rlist_max)

        wea_min = r_min.strftime("%Y")
        wea_max = r_max.strftime("%Y")

        self.expTreatCombo = QComboBox()          
        if crop != "Select from list":
            self.experimentlists = getExpTreatByCrop(crop)      
         #   self.experimentlists = getExpTreatByCropWeatherDate(crop,stationtype,weatherID)
            
            self.expTreatCombo.addItem("Select from list") 
            for val in self.experimentlists:
                cropExperimentTreatment = "".join([crop,'/',val])
              #  print(cropExperimentTreatment)
                weatheryears_list = read_weatheryears_fromtreatment(cropExperimentTreatment)
             #   print(weatheryears_list)
                num_weatheryears_list = len(weatheryears_list)
                if num_weatheryears_list == 1:
                    if (int(wea_min) <= weatheryears_list[0] <= int(wea_max)):
                       self.expTreatCombo.addItem(val)
                elif num_weatheryears_list == 2:
                    if (weatheryears_list[0] >= int(wea_min)) and (weatheryears_list[1] <= int(wea_max)):
                        self.expTreatCombo.addItem(val)
                else:
                    pass
       
        self.expTreatCombo.currentIndexChanged.connect(self.showtreatmentyear)
        self.tablebasket.setCellWidget(crow,5,self.expTreatCombo)
        return True
    '''
    def showexperimentcombo(self):
        crop = self.cropCombo.currentText()
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        stationtype = self.stationTypeCombo.currentText()
        weather_id= self.weatherCombo.currentText()
       # weatherID = read_weather_id_forstationtype(stationtype)
        rlist_max, rlist_min = read_weatherDate_forstationtype(stationtype,weather_id)
        print("rlist_min, rlist_max: ",  rlist_min, rlist_max )
        print(type(rlist_min))

        r_min = parse(rlist_min)
        r_max = parse(rlist_max)

        wea_min = r_min.strftime("%Y")
        wea_max = r_max.strftime("%Y")

        self.expTreatCombo = QComboBox()          
        if crop != "Select from list":
            self.experimentlists = getExpTreatByCrop(crop)      
         #   self.experimentlists = getExpTreatByCropWeatherDate(crop,stationtype,weatherID)
            
            self.expTreatCombo.addItem("Select from list") 
            for val in self.experimentlists:
                cropExperimentTreatment = "".join([crop,'/',val])
                print(cropExperimentTreatment)
                weatheryears_list = read_weatheryears_fromtreatment(cropExperimentTreatment)
                print(weatheryears_list)
                num_weatheryears_list = len(weatheryears_list)
                if num_weatheryears_list == 1:
                    if (int(wea_min) <= weatheryears_list[0] <= int(wea_max)):
                       self.expTreatCombo.addItem(val)
                elif num_weatheryears_list == 2:
                    if (weatheryears_list[0] >= int(wea_min)) and (weatheryears_list[1] <= int(wea_max)):
                        self.expTreatCombo.addItem(val)
                else:
                    pass
       
        self.expTreatCombo.currentIndexChanged.connect(self.showtreatmentyear)
        self.tablebasket.setCellWidget(crow,5,self.expTreatCombo)
        return True
    '''

    def showtreatmentyear(self):
        currentrow = self.tablebasket.currentRow()
        if(currentrow == -1):
            currentrow = 0
        crop = self.cropCombo.currentText()
        experiment = self.expTreatCombo.currentText()
        if experiment == "Select from list":
            self.tablebasket.setItem(currentrow,6,QTableWidgetItem(""))
            self.tablebasket.setItem(currentrow,7,QTableWidgetItem(""))
        else:
            cropExperimentTreatment = "".join([crop,'/',experiment])
        #    print("cropExperimentTreatment=",cropExperimentTreatment)
            # get weather years
            weatheryears_list = read_weatheryears_fromtreatment(cropExperimentTreatment)
          #  print(weatheryears_list)
            syear = str(weatheryears_list[0])
            eyear = str(weatheryears_list[-1])
            self.tablebasket.setItem(currentrow,6,QTableWidgetItem(syear))
            self.tablebasket.setItem(currentrow,7,QTableWidgetItem(eyear))
            self.tablebasket.setItem(currentrow,10,QTableWidgetItem("here"))
        return True


    def importfaq(self, thetabname=None):        
        cropname = ""
        faqlist = read_FaqDB(thetabname,cropname)         
        self.faqtree.clear()

        for item in faqlist:
            roottreeitem = QTreeWidgetItem(self.faqtree)
            roottreeitem.setText(0,item[2])
            childtreeitem = QTreeWidgetItem()
            childtreeitem.setText(0,item[3])
            roottreeitem.addChild(childtreeitem)


    def controlfaq(self):                
        if self.helpcheckbox.isChecked():
            self.importfaq("seasonal")              
            self.faqtree.setVisible(True)
        else:
            self.faqtree.setVisible(False)
        

    def buttonrunclicked(self):        
        self.saveQTextStream()


    def saveQTextStream(self):
        for irow in range(0,self.tablebasket.rowCount()):
            lsitename = self.tablebasket.cellWidget(irow,0).currentText()
            lsoilname = self.tablebasket.cellWidget(irow,1).currentText()
            lstationtype = self.tablebasket.cellWidget(irow,2).currentText()
            lweather = self.tablebasket.cellWidget(irow,3).currentText()
            lcrop = self.tablebasket.cellWidget(irow,4).currentText()
            lexperiment = self.tablebasket.cellWidget(irow,5).currentText()
            lwaterstress = self.tablebasket.cellWidget(irow,8).currentText()
            if(lwaterstress == "Yes"):
                waterStressFlag = 0
            else:
                waterStressFlag = 1
            lnitrostress = self.tablebasket.cellWidget(irow,9).currentText()
            if(lnitrostress == "Yes"):
                nitroStressFlag = 0
            else:
                nitroStressFlag = 1
            ltempVar = self.tablebasket.cellWidget(irow,10).currentText()
            lrainVar = self.tablebasket.cellWidget(irow,11).currentText()
            lCO2Var = self.tablebasket.cellWidget(irow,12).currentText()
            if lCO2Var == "None":
                lCO2Var = 0

            if lsitename == "Select from list":
                return messageUser("You need to select Site.")

            if lsoilname == "Select from list":
                return messageUser("You need to select Soilname.")

            if lstationtype == "Select from list":
                return messageUser("You need to select Station Name.")

            if lweather == "Select from list":
                return messageUser("You need to select Weather.")

            if lcrop == "Select from list":
                return messageUser("You need to select Crop.")

            if lexperiment == "Select from list":
                return messageUser("You need to select Experiment/Treatment.")

            lstartyear = int(self.tablebasket.item(irow,6).text())
            lendyear = int(self.tablebasket.item(irow,7).text())

            cropTreatment = lcrop + "/" + lexperiment
            simulation_name = update_pastrunsDB(0,lsitename,cropTreatment,lstationtype,lweather,lsoilname,str(lstartyear),str(lendyear),
                                                str(waterStressFlag),str(nitroStressFlag),str(ltempVar),str(lrainVar),str(lCO2Var)) 

            # this will execute the 2 exe's: uncomment it in final stage: 
            self.prepare_and_execute(simulation_name,irow,lstartyear)                

        
    def prepare_and_execute(self,simulation_name,irow,theyear):
        """
        this will create input files, and execute both exe's
        """

        field_path = os.path.join(runDir,str(simulation_name[0]))
        if not os.path.exists(field_path):
            os.makedirs(field_path)

     #   print("Check this part:",self.inseason_date)

        field_name= self.tablebasket.cellWidget(irow,0).currentText()  
        lsoilname = self.tablebasket.cellWidget(irow,1).currentText()
        lstationtype = self.tablebasket.cellWidget(irow,2).currentText()
        #print("lstationtype:", lstationtype)
        lweather = self.tablebasket.cellWidget(irow,3).currentText()
        lcrop = self.tablebasket.cellWidget(irow,4).currentText()
        lexperiment = self.tablebasket.cellWidget(irow,5).currentText().split('/')[0]
        ltreatmentname = self.tablebasket.cellWidget(irow,5).currentText().split('/')[1]
        lwaterstress = self.tablebasket.cellWidget(irow,8).currentText()
        if(lwaterstress == "Yes"):
            waterStressFlag = 0
        else:
            waterStressFlag = 1
        lnitrostress = self.tablebasket.cellWidget(irow,9).currentText()
        if(lnitrostress == "Yes"):
            nitroStressFlag = 0
        else:
            nitroStressFlag = 1
        ltempVar = self.tablebasket.cellWidget(irow,10).currentText()
        lrainVar = self.tablebasket.cellWidget(irow,11).currentText()
        lCO2Var = self.tablebasket.cellWidget(irow,12).currentText()

        #copy water.dat file from store to runDir
        src_file = storeDir+'\\Water.DAT'
        dest_file = field_path+'\\WatMovParam.DAT'
        copyFile(src_file,dest_file) 

        waterfilecontent=[]
        with open(dest_file, 'r') as read_file:
            waterfilecontent = read_file.readlines()
            
            
        sandcontent = WriteSoiData(lsoilname,field_name,field_path)
        if sandcontent > 75:
            with open(dest_file, 'w') as write_file:
                for line in waterfilecontent:
                        write_file.write(line.replace("-1.00000E+005", "-1.00000E+004"))  
                        

        #copy waterBound.dat file from store to runDir
        src_file= storeDir+'\\WaterBound.DAT'
        dest_file= field_path+'\\Water.dat'
        copyFile(src_file,dest_file)

        

        WriteBiologydefault(field_name,field_path)

        # Start
        #includes initial, management and fertilizer 
        rowSpacing, rootWeightPerSlab, cultivar = self.WriteIni(irow,field_name,field_path,theyear,theyear,waterStressFlag,nitroStressFlag) 
        if cultivar != "fallow":
            WriteCropVariety(lcrop,cultivar,field_name,field_path)
        else:
            src_file= storeDir+'\\fallow.var'
            dest_file= field_path+'\\fallow.var'
            copyFile(src_file,dest_file)
        WriteDripIrrigationFile(field_name,field_path)

        
        if self.ExpSys.isChecked():
            linSeaDate = self.inseason_date
       #     print("Expert System: ", linSeaDate)
            hourly_flag, edate = WriteWeather(lexperiment,ltreatmentname,lstationtype,lweather,field_path,ltempVar,lrainVar,lCO2Var,linSeaDate)
         #   print("edate:", edate)
            
        else :
            linSeaDate = None
            hourly_flag, edate = WriteWeather(lexperiment,ltreatmentname,lstationtype,lweather,field_path,ltempVar,lrainVar,lCO2Var,linSeaDate)
       #     print("edate: ", edate)
    
        WriteSoluteFile(lsoilname,field_path)
        WriteGasFile(field_path)
        hourlyFlag = 1 if self.step_hourly.isChecked() else 0


        if self.ExpSys.isChecked():
            WriteTimeFileDataExpSys(ltreatmentname,lexperiment,lcrop,lstationtype,hourlyFlag,field_name,field_path,hourly_flag,linSeaDate,0)
        else :
            WriteTimeFileData(ltreatmentname,lexperiment,lcrop,lstationtype,hourlyFlag,field_name,field_path,hourly_flag,0)

        WriteNitData(lsoilname,field_name,field_path,rowSpacing)
        self.WriteLayerGas(lsoilname,field_name,field_path,rowSpacing,rootWeightPerSlab)
       # WriteSoiData(lsoilname,field_name,field_path)
        surfResType=WriteManagement(lcrop,lexperiment,ltreatmentname,field_name,field_path,rowSpacing)

        irrType = irrigationInfo(lcrop,lexperiment,ltreatmentname)
        print(irrType)

        WriteMulchGeo(field_path,surfResType)
        o_t_exid = getTreatmentID(ltreatmentname,lexperiment,lcrop)

        WriteIrrigation(field_name,field_path, simulation_name, o_t_exid)

        WriteRunFile(lcrop,lsoilname,field_name,cultivar,field_path,lstationtype)            
        src_file= field_path+"\\"+field_name+".lyr"                    
        layerdest_file= field_path+"\\"+field_name+".lyr"
        createsoil_opfile= lsoilname
        grid_name = field_name
            
        pp = subprocess.Popen([createsoilexe,layerdest_file,"/GN",grid_name,"/SN",createsoil_opfile],cwd=field_path)
        while pp.poll() is None:
            time.sleep(1)

        runname = field_path+"\\Run"+field_name+".dat"       
        edate = edate + timedelta(days=22)
        self.simStatus.setText("")
        self.simStatus.repaint()
        os.chdir(field_path)
        try:
            QCoreApplication.processEvents()
            if(lcrop == "maize"):
                p = subprocess.Popen([maizsimexe, runname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
                file_ext = ["g01","G03","G04","G05","G07"]
            elif(lcrop == "potato"):
                p = subprocess.Popen([spudsimexe, runname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
                file_ext = ["g01","G03","G04","G05","G07"]
            elif(lcrop == "soybean"):
                p = subprocess.Popen([glycimexe, runname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
                file_ext = ["g01","G03","G04","G05","G07"]
            elif(lcrop == "cotton"):
                p = subprocess.Popen([gossymexe, runname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
                file_ext = ["g01","G03","G04","G05","G07"]
            else: # fallow
                p = subprocess.Popen([maizsimexe, runname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
                file_ext = ["G03","G05","G07"]

            for line in iter(p.stdout.readline,b''):
                print("line=",line)
                if b'Progress' in line:
                    prog = re.findall(r"[-+]?\d*\.\d+|\d+", line.decode())
                    self.simStatus.setText("<b>Simulation Progress</b>: "+prog[0]+"%")
                    self.simStatus.repaint()
             
            (out,err) = p.communicate()
            if p.returncode == 0:
                print("twosoil stage completed. %s",str(out))
            else:
                print("twosoil stage failed. Error =. %s",str(err))
        except OSError as e:
            sys.exit("failed to execute twodsoil program, %s", str(e))

        missingRec = ""
        # Check for NaN on output files
        for ext in file_ext:
            g_name2 = field_path+"\\\\"+field_name+"."+ext
            table_name = ext.lower()+"_"+lcrop
           
            print(g_name2, table_name)
            missingRec += checkNaNInOutputFile(table_name,g_name2)
            print(missingRec)

        if lcrop != "fallow":
            missingRec += checkNaNInOutputFile("plantStress_"+lcrop,field_path+"\\\\plantstress.crp")
            if lcrop == "potato" or lcrop == "soybean":
                missingRec += checkNaNInOutputFile("nitrogen_"+lcrop,field_path+"\\\\nitrogen.crp")

        if missingRec != "":
            delete_pastrunsDB(str(simulation_name[0]),lcrop)
            self.simStatus.setText("<b>Something went wrong with this run.  The details are shown below.  We are unable to store results of this run until the problem can be resolved.  Additional details shown below.  The following file/columns displayed NaN values:</b><br>"+missingRec)
        else:
            # Ingesting table  into cropOutput database
            
            self.simStatus.setText("<b>Ingesting output files in the database.</b>")
            self.simStatus.repaint()
            for ext in file_ext:
                g_name = field_path+"\\"+field_name+"."+ext
                g_name2 = field_path+"\\\\"+field_name+"."+ext
                table_name = ext.lower()+"_"+lcrop
                # Ingest .grd file and Area from G03 file on the geometry table
                if ext == 'G03' or ext == 'g03':
                    ingestGeometryFile(field_path+"\\\\"+field_name+".grd",g_name2,str(simulation_name[0]))
                ingestOutputFile(table_name,g_name2,str(simulation_name[0]))
         #       if remOutputFilesFlag:
         #          os.remove(g_name)

            ingestOutputFile("plantStress_"+lcrop,field_path+"\\\\plantstress.crp",str(simulation_name[0]))
            if remOutputFilesFlag:
                os.remove(field_path+"\\\\plantstress.crp")

            if lcrop == "soybean" or lcrop == "potato":
                ingestOutputFile("nitrogen_"+lcrop,field_path+"\\\\nitrogen.crp",str(simulation_name[0]))
                if remOutputFilesFlag:
                    os.remove(field_path+"\\\\nitrogen.crp")
 
            self.rotationsig.emit(int(simulation_name[0])) #emitting the simulation id (integer)
        #    print("BBBBBBB")
         #   print(simulation_name[0])
            self.exsystemsig.emit(int(simulation_name[0]))
            
          #  print("ExpertSystem: ", self.ExpSys)
            if self.ExpSys.isChecked():
                self.simStatus.setText("<b>Check your simulation results on Expert System tab.</b>")
             #   print("Season: ", linSeaDate)
            else:
                self.simStatus.setText("<b>Check your simulation results on Output tab.</b>")

        self.simStatus.repaint()
        #end of prepare_and_execute
    

    def WriteIni(self,irow,field_name,field_path,lstartyear,lendyear,waterStressFlag,nitroStressFlag):
        '''
        Get data from operation, soil_long
        '''
        autoirrigation=0
        rowangle=0
        xseed=0
        yseed=5
        cec=0.65
        eomult=0.5
        pop=6.5
        rowSpacing = 75
        SowingDate=0
        HarvestDate=0
      #  EndDate=0
        cultivar = "fallow"

        #get management tree                    
        cropname = self.tablebasket.cellWidget(irow,4).currentText()
        experiment = self.tablebasket.cellWidget(irow,5).currentText().split('/')[0]
        treatmentname = self.tablebasket.cellWidget(irow,5).currentText().split('/')[1]

        #find cropid
        #use crop to find exid in eperiment table
        #use exid and treatmentname to find tid from treatment table
        # use tid(o_t_exid) to find all the operations
        operationList = []
        exid = read_experimentDB_id(cropname,experiment)
        tid = read_treatmentDB_id(exid,treatmentname)
        operationList = read_operationsDB_id(tid) #gets all the operations

        if self.ExpSys.isChecked():
            inseason_date_obj = datetime.strptime(self.inseason_date, '%Y-%m-%d')           
            formatted_inseason_date = inseason_date_obj.strftime('%m/%d/%Y') 

        for ii,jj in enumerate(operationList):
            if jj[1] == 'Simulation Start':
                # Placeholder so model doesn't use the date
                if cropname == "fallow":
                    SowingDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=370)).strftime('%m/%d/%Y')
                initCond = readOpDetails(jj[0],jj[1])

                depth = initCond[0][6]
                length = initCond[0][5]
                pop = initCond[0][3]
                autoirrigation = initCond[0][4]
                rowangle = 0
                xseed = initCond[0][5]
                yseed = initCond[0][6]
                cec = initCond[0][7]
                eomult = initCond[0][8]
                rowSpacing = initCond[0][9]
                seedpieceMass = initCond[0][11]
                cultivar = initCond[0][10]

            if jj[1] == 'Sowing':                            
                SowingDate=jj[2] #month/day/year

            if jj[1] == 'Emergence':                            
                EmergenceDate=jj[2] #month/day/year

            if jj[1] == 'Harvest':                            
                HarvestDate=jj[2] #month/day/year

            if jj[1] == 'Simulation End':   
                if self.ExpSys.isChecked():
                    EndDate = formatted_inseason_date #self.inseason_date # "08/02/2014"
                else:
                    EndDate=jj[2] #month/day/year
                    # End date should be greater than sowing date
                    if cropname == "fallow":
                        EndDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=365)).strftime('%m/%d/%Y')
            
        site = self.tablebasket.cellWidget(irow,0).currentText()
        soil = self.tablebasket.cellWidget(irow,1).currentText()
        tsite_tuple = extract_sitedetails(site)   
        #maximum profile depth     
        maxSoilDepth=read_soillongDB_maxdepth(soil)
        RowSP = rowSpacing

############### Write INI file
        PopRow= rowSpacing/100 * pop 
     
        filename = field_path+"\\"+field_name+".ini"
        fh = QFile(filename)

        if not fh.open(QIODevice.WriteOnly|QIODevice.Text):
            print("Could not open file")
        else:
            yseed = maxSoilDepth - yseed
            fout = QTextStream(fh)
            CODEC="UTF-8"
            fout.setCodec(CODEC)
            fout<<"***Initialization data for location"<<"\n"
            fout<<"POPROW  ROWSP  Plant Density      ROWANG  xSeed  ySeed         CEC    EOMult"<<"\n"                    
            fout<<'%-14.6f%-14.6f%-14.6f%-14.6f%-14.6f%-14.6f%-14.6f%-14.6f' %(PopRow,RowSP,pop,rowangle,xseed,yseed,cec,eomult)<<"\n"
            fout<<"Latitude longitude altitude"<<"\n"
            fout<<'%-14.6f%-14.6f%-14.6f' %(tsite_tuple[1],tsite_tuple[2],tsite_tuple[3])<<"\n"
            if cropname == "maize" or cropname == "fallow":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Planting          Emergence           End           TimeStep(m)    sowing and end dates for fallow are setin the future so the soil model will not call a crop\n"
                fout<<"'%-10s'  '%-10s'  %d" %(SowingDate,EndDate,60)<<"\n"
                rootWeightPerSlab = 0
            elif cropname == "potato":
                fout<<"Seed  Depth  Length  Bigleaf"<<"\n"
                fout<<"%-14.6f%-14.6f%-14.6f%d" %(seedpieceMass,depth,length,1)<<"\n"
                fout<<"Planting          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Stresses (Nitrogen, Water stress: 1-nonlimiting, 2-limiting): Simulation Type (1-meteorological, 2-physiological)"<<"\n"
                fout<<"Nstressoff  Wstressoff  Water-stress-simulation-method"<<"\n"
                fout<<"%d    %d    %d" %(waterStressFlag,nitroStressFlag,0)<<"\n"
                popSlab = RowSP/100 * 0.5 * 0.01 * pop  
                rootWeightPerSlab = seedpieceMass * 0.25 * popSlab
               # rootWeightPerSlab = seedpieceMass * pop  * 0.25 * RowSP / 100 * 0.5 * 0.01
            elif cropname == "soybean":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Sowing          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                popSlab = RowSP/100 * eomult * 0.01 * pop
                rootWeightPerSlab = 0.0275 * popSlab
               
            elif cropname == "cotton":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  %d" %(EmergenceDate, HarvestDate,60)<<"\n"
                popSlab = RowSP/100 * eomult * 0.01 * pop
                rootWeightPerSlab = 0.2 * popSlab
            fout<<"output soils data (g03, g04, g05 and g06 files) 1 if true"<<"\n"
            fout<<"no soil files        output soil files"<<"\n"
            fout<<"    0                   1  "<<"\n"
               
        fh.close()

        return RowSP, rootWeightPerSlab, cultivar


    def WriteLayerGas(self,soilname,field_name,field_path,rowSpacing,rootWeightPerSlab):
        '''
        Writes Layer file (*.lyr)
        '''
        # get Grid Ratio for the soil
        gridratio_list =read_soilgridratioDB(soilname)
        NumObs = len(gridratio_list)
        CODEC="UTF-8"
        # read rowSpacing
        filename = field_path+"\\"+field_name+".lyr"             
        fh = QFile(filename)

        if not fh.open(QIODevice.WriteOnly|QIODevice.Text):
            print("Could not open file")
        else:                  
            fout = QTextStream(fh)            
            fout.setCodec(CODEC)  
            fout<<"surface ratio    internal ratio: ratio of the distance between two neighboring nodes\n"
            for rrow in range(0,NumObs):
                record_tuple=gridratio_list[rrow]
                fout<<'%-14.3f%-14.3f%-14.3f%-14.3f' %(record_tuple[0],record_tuple[1],record_tuple[2],record_tuple[3])<<"\n"

            fout<<"RowSpacing"<<"\n"
            fout<<'%-6.1f' %(rowSpacing)

            fout<<"\n"<<" Planting Depth	  X limit for roots"<<"\n"
            for rrow in range(0,len(gridratio_list)):
                record_tuple=gridratio_list[rrow]
                fout<<'%-14.3f%-14.3f%-14.3f\n' %(record_tuple[4],record_tuple[5],rootWeightPerSlab)

            fout<<"Surface water Boundary Code  surface and bottom Gas boundary codes(for all bottom nodes) 1 constant -2 seepage face, 7 drainage, 4 atmospheric\n"
            fout<<"water boundary code for bottom layer, gas BC for the surface and bottom layers\n"
            for rrow in range(0,len(gridratio_list)):
                record_tuple=gridratio_list[rrow]
                fout<<'%-14d%-14d%-14d\n' %(record_tuple[6],record_tuple[7],record_tuple[8])

            fout<<" Bottom depth   Init Type  OM (%/100)   Humus_C    Humus_N    Litter_C    Litter_N    Manure_C    Manure_N  no3(ppm)  NH4  \
                   hNew  Tmpr     CO2     O2   N2O  Sand     Silt    Clay     BD     TH33     TH1500  thr ths tha th  Alfa    n   Ks  Kk  thk\n"
            fout<<" cm         w/m       Frac      ppm    ppm    ppm    ppm   ppm    ppm   ppm     ppm   cm     0C     ppm   ppm  ----  fraction---     \
                   g/cm3    cm3/cm3   cm3/cm3\n"
            print("soilname=",soilname)
            soilgrid_list = read_soilshortDB(soilname)
            for rrow in range(0,len(soilgrid_list)):
                record_tuple = soilgrid_list[rrow]
                record_tuple = [float(i) for i in record_tuple]
                if(record_tuple[1] == 1):
                    initType = "'m'"
                else:
                    initType = "'w'"
                fout<<'%-14d%-6s%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f\
                       %-14.3f%-14.3f%-14.3f%-14.3f%-14.3f' %(record_tuple[0],initType,record_tuple[2],-1,-1,0,0,0,0,record_tuple[3], record_tuple[4],record_tuple[5],record_tuple[6],
                       record_tuple[22],record_tuple[23],record_tuple[24],record_tuple[7]/100,record_tuple[8]/100,record_tuple[9]/100,record_tuple[10],record_tuple[11],record_tuple[12],record_tuple[13],
                       record_tuple[14],record_tuple[15],record_tuple[16],record_tuple[17],record_tuple[18],record_tuple[19],record_tuple[20],record_tuple[21])<<"\n"
        fout<<"\n"
        fh.close()


    def refresh(self):
        sitelists = read_sitedetailsDB()
        self.soillists = read_soilDB()
        self.ExpSys.setChecked(False)
        for irow in range(0,self.tablebasket.rowCount()):
            lsitename = self.tablebasket.cellWidget(irow,0).currentText()
            self.siteCombo = QComboBox()
            self.siteCombo.addItem("Select from list")
            for item in sitelists: 
                self.siteCombo.addItem(item)
            if(self.siteCombo.findText(lsitename, QtCore.Qt.MatchFixedString) >= 0):
                self.siteCombo.setCurrentIndex(self.siteCombo.findText(lsitename, QtCore.Qt.MatchFixedString))
            else:
                self.siteCombo.setCurrentIndex(0)
            self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
            self.tablebasket.setCellWidget(irow,0,self.siteCombo)

            lsoilname = self.tablebasket.cellWidget(irow,1).currentText()
            self.soilCombo = QComboBox()
            self.soilCombo.addItem("Select from list")
            for key in self.soillists:            
                self.soilCombo.addItem(key)
            if(self.soilCombo.findText(lsoilname, QtCore.Qt.MatchFixedString) >= 0):
                self.soilCombo.setCurrentIndex(self.soilCombo.findText(lsoilname, QtCore.Qt.MatchFixedString))
            else:
                self.soilCombo.setCurrentIndex(0)
            self.tablebasket.setCellWidget(irow,1,self.soilCombo)

            stationtypelists = read_weather_metaDBforsite(lsitename)
            lstationtype = self.tablebasket.cellWidget(irow,2).currentText()
            self.stationTypeCombo = QComboBox()        
            self.stationTypeCombo.addItem("Select from list")
            for key in stationtypelists:
                if stationtypelists[key] != "Add New Station Name":
                    self.stationTypeCombo.addItem(stationtypelists[key])
                    if(self.stationTypeCombo.findText(lstationtype, QtCore.Qt.MatchFixedString) >= 0):
                        self.stationTypeCombo.setCurrentIndex(self.stationTypeCombo.findText(lstationtype, QtCore.Qt.MatchFixedString))
                    else:
                        self.stationTypeCombo.setCurrentIndex(0)
            self.stationTypeCombo.currentIndexChanged.connect(self.showweathercombo)
            self.tablebasket.setCellWidget(irow,2,self.stationTypeCombo)

            weather_id_lists = read_weather_id_forstationtype(lstationtype)
            lweather = self.tablebasket.cellWidget(irow,3).currentText()
            self.weatherCombo = QComboBox()        
            self.weatherCombo.addItem("Select from list")
            for item in weather_id_lists:
                if item != "Add New Station Name":
                    self.weatherCombo.addItem(item)
                    if(self.weatherCombo.findText(lweather, QtCore.Qt.MatchFixedString) >= 0):
                        self.weatherCombo.setCurrentIndex(self.weatherCombo.findText(lweather, QtCore.Qt.MatchFixedString))
                    else:
                        self.weatherCombo.setCurrentIndex(0)
            self.tablebasket.setCellWidget(irow,3,self.weatherCombo)

            lcrop = self.tablebasket.cellWidget(irow,4).currentText()
            self.experimentlists = getExpTreatByCrop(lcrop)            
            lexptreat = self.tablebasket.cellWidget(irow,5).currentText()
            self.expTreatCombo = QComboBox()          
            self.expTreatCombo.addItem("Select from list") 
            for val in self.experimentlists:
                self.expTreatCombo.addItem(val)
            if(self.expTreatCombo.findText(lexptreat, QtCore.Qt.MatchFixedString) >= 0):
                self.expTreatCombo.setCurrentIndex(self.expTreatCombo.findText(lexptreat, QtCore.Qt.MatchFixedString))
            else:
                self.expTreatCombo.setCurrentIndex(0)
            self.expTreatCombo.currentIndexChanged.connect(self.showtreatmentyear)
            self.tablebasket.setCellWidget(irow,5,self.expTreatCombo)


    def SelectInSeaDate(self, state) :#, treatmentname, experimentname ,cropname):
  
        if state == 2:
            result = self.ExpSysshowDialogcontinue()

            self.inseason_date = result
            print("self_inseasonadate: ", self.inseason_date)
            conn, c = openDB('crop.db')
            if c:
                c.execute("insert into inSeaIrri (inSeaDate, inSea_irrAmt) values (?, ?)" ,[str(self.inseason_date), 0])
            conn.commit()
            conn.close()
        
       
            
    
    def ExpSysshowDialogcontinue(self,):
        for irow in range(0,self.tablebasket.rowCount()):
             
                lcrop = self.tablebasket.cellWidget(irow,4).currentText()
                lexperiment = self.tablebasket.cellWidget(irow,5).currentText().split('/')[0]
                ltreatment = self.tablebasket.cellWidget(irow,5).currentText().split('/')[1]

              #  print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
              #  print(lcrop, lexperiment, ltreatment)
                record_tuple = (lcrop, lexperiment, ltreatment)

                firstoperation_date = getme_date_of_first_operationDB(ltreatment, lexperiment, lcrop)
                firstoperation_date_parts = firstoperation_date[0].split("/")
                print(firstoperation_date_parts)
                date = QDate(int(firstoperation_date_parts[2]),int(firstoperation_date_parts[0]),int(firstoperation_date_parts[1]))
      
                if ltreatment != "Select from list":

                    msg = QMessageBox()

                    calendar = QCalendarWidget(self)
                 
                    calendar.setSelectedDate(date)
                    msg.layout().addWidget(calendar)
                    msg.exec()
                

                    selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
                  #  print(selected_date)
        return selected_date
                  


                


                  
        
 
           