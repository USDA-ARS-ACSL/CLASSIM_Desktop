import subprocess
import time
import os
import pandas as pd
import sys
import re
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, \
                            QHeaderView, QRadioButton, QButtonGroup, QMenu, QCheckBox, QGridLayout, QGroupBox, QHeaderView
from PyQt5.QtCore import QFile, QTextStream, pyqtSignal, QCoreApplication
from CustomTool.getClassimDir import *
from CustomTool.custom1 import *
from CustomTool.UI import *
from CustomTool.generateModelInputFiles import *
from CustomTool.getClassimDir import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from subprocess import Popen

#global classimDir
#global runDir
#global storeDir

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
    print('RotationTab Error: Missing storeDir')

class Rotation_Widget(QWidget):
    # Add a signal
    rotationUpSig = pyqtSignal(int)    
    changedValue = pyqtSignal(int)
    def __init__(self):
        super(Rotation_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
      # self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
      # self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("rotation")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.tab_summary = QTextEdit("To create your rotation you first need to select in this order: Site, \
Soil, Station Name and Weather. Please, note that when you select crop, only experiment/treatments that are scheduled \
to happen in the timeframe that we have weather data will appear in the list.  To add or delete a rotation, please \
select the entire row and right click. It will open a dialog box with simple instructions. Once changes are done, please \
make sure to press the Execute Rotation button.")        
        self.tab_summary.setReadOnly(True)        
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame) 
        self.tab_summary.setMaximumHeight(50) # need it     
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink="<a href=\"https://youtu.be/wOC70sNX9tw\">Click here \
                to watch the Rotation Builder Tab Video Tutorial</a><br>"
        self.rotationVidlabel=QLabel()
        self.rotationVidlabel.setOpenExternalLinks(True)
        self.rotationVidlabel.setText(urlLink)

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
        self.expTreatCombo.addItem("Select from list") 

        self.sitelabel = QLabel("Site")
        sitelists = read_sitedetailsDB()
        self.siteCombo = QComboBox()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
            self.siteCombo.addItem(item)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
        self.soillabel = QLabel("Soil")
        soillists = read_soilDB()
        self.soilCombo = QComboBox()
        self.soilCombo.addItem("Select from list")
        for key in soillists:            
            self.soilCombo.addItem(key)
        
        self.stationTypelabel = QLabel("Station Name")
        self.weatherlabel = QLabel("Weather")

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
        self.tablebaskethheaderlabels = ["Crop","Experiment/Treatment", "Start Date","End Date","Water\nStress","Nitrogen\nStress","Temp\nVariance (oC)","Rain\nVariance (%)","CO2\nVariance (ppm)"]
        self.tablebasket.clear()
        self.tablebasket.setRowCount(0)
        self.tablebasket.setRowCount(1)
        self.tablebasket.setColumnCount(9)
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

        self.tablebasket.setCellWidget(0,0,self.cropCombo)
        self.tablebasket.setCellWidget(0,1,self.expTreatCombo)
        self.tablebasket.setItem(0,2,QTableWidgetItem(""))
        self.tablebasket.setItem(0,3,QTableWidgetItem(""))
        self.tablebasket.setCellWidget(0,4,self.comboWaterStress)
        self.tablebasket.setCellWidget(0,5,self.comboNitroStress)
        self.tablebasket.setCellWidget(0,6,self.comboTempVar)
        self.tablebasket.setCellWidget(0,7,self.comboRainVar)
        self.tablebasket.setCellWidget(0,8,self.comboCO2Var)

        self.simStatus = QLabel("")
        self.simStatus.setWordWrap(True)
        self.buttonrun = QPushButton("Execute Rotation")
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

        # Add site, soil, station type and weather
        self.subgrid1.addWidget(self.sitelabel,0,0)
        self.subgrid1.addWidget(self.siteCombo,0,1)
        self.subgrid1.addWidget(self.soillabel,0,2)
        self.subgrid1.addWidget(self.soilCombo,0,3)
        self.subgrid1.addWidget(self.stationTypelabel,1,0)
        self.subgrid1.addWidget(self.stationTypeCombo,1,1)
        self.subgrid1.addWidget(self.weatherlabel,1,2)
        self.subgrid1.addWidget(self.weatherCombo,1,3)
 
        self.subgrid1.addWidget(self.tablebasket,2,0,4,4)

        self.SimulationFlabel = QLabel("Simulation Output Interval")
        self.subgrid1.addWidget(self.SimulationFlabel,6,0)
        self.subgrid1.addWidget(self.step_hourly,6,1)
        self.subgrid1.addWidget(self.step_daily,6,2,1,2)
        
        self.SimulationFlabel.setObjectName("SimulationFlabel")

        self.subgrid1.addWidget(self.buttonrun,7,0)
        self.subgrid1.addWidget(self.buttonreset,7,1)
        self.subgrid1.addWidget(self.simStatus,8,0,1,4)
        
        self.buttonrun.clicked.connect(self.buttonrunclicked)
        self.buttonreset.clicked.connect(self.reset)
        self.tablebasket.resizeColumnsToContents()
        self.tablebasket.resizeRowsToContents()  
              
        self.hl2 = QHBoxLayout()                
        self.rgroupbox.setLayout(self.subgrid1)
        self.hl2.addWidget(self.rgroupbox)
        
        self.vl1.addLayout(self.hl1)
        self.vl1.addWidget(self.rotationVidlabel)
        self.vl1.addWidget(self.helpcheckbox)
        self.vl1.addLayout(self.hl2)
        self.vl1.addStretch(1)
        self.mainlayout1.addLayout(self.vl1,0,0)
        self.mainlayout1.setColumnStretch(0,3)
        self.mainlayout1.addWidget(self.faqtree,0,4)
        self.setLayout(self.mainlayout1)
  

    def reset(self):
        self.siteCombo = QComboBox()
        sitelists = read_sitedetailsDB()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
            self.siteCombo.addItem(item)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        
        self.soilCombo = QComboBox()
        soillists = read_soilDB()
        self.soilCombo.addItem("Select from list")
        for key in soillists:            
            self.soilCombo.addItem(key)
        
        self.cropCombo = QComboBox()          
        croplists = read_cropDB()
        self.cropCombo.addItem("Select from list")
        for val in croplists:
            self.cropCombo.addItem(val)
        self.cropCombo.currentIndexChanged.connect(self.showexperimentcombo)
 
        self.stationTypeCombo = QComboBox()        
        self.weatherCombo = QComboBox()    
    
        self.subgrid1.addWidget(self.siteCombo,0,1)
        self.subgrid1.addWidget(self.soilCombo,0,3)
        self.subgrid1.addWidget(self.stationTypeCombo,1,1)
        self.subgrid1.addWidget(self.weatherCombo,1,3)
               
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

        while self.tablebasket.rowCount() > 0:
            self.tablebasket.removeRow(0)        
        self.tablebasket.insertRow(0)
 
        self.expTreatCombo = QComboBox()          
        self.expTreatCombo.addItem("Select from list") 

        self.tablebasket.setCellWidget(0,0,self.cropCombo)
        self.tablebasket.setCellWidget(0,1,self.expTreatCombo)
        self.tablebasket.setItem(0,2,QTableWidgetItem(""))
        self.tablebasket.setItem(0,3,QTableWidgetItem(""))
        self.tablebasket.setCellWidget(0,4,self.comboWaterStress)
        self.tablebasket.setCellWidget(0,5,self.comboNitroStress)
        self.tablebasket.setCellWidget(0,6,self.comboTempVar)
        self.tablebasket.setCellWidget(0,7,self.comboRainVar)
        self.tablebasket.setCellWidget(0,8,self.comboCO2Var)

        self.simStatus.setText("")
        self.simStatus.repaint()


    def tableverticalheader_popup(self):
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
            self.expTreatCombo = QComboBox()          
            self.expTreatCombo.addItem("Select from list") 

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

            self.tablebasket.setCellWidget(0,0,self.cropCombo)
            self.tablebasket.setCellWidget(0,1,self.expTreatCombo)
            self.tablebasket.setItem(0,2,QTableWidgetItem(""))
            self.tablebasket.setItem(0,3,QTableWidgetItem(""))
            self.tablebasket.setCellWidget(0,4,self.comboWaterStress)
            self.tablebasket.setCellWidget(0,5,self.comboNitroStress)
            self.tablebasket.setCellWidget(0,6,self.comboTempVar)
            self.tablebasket.setCellWidget(0,7,self.comboRainVar)
            self.tablebasket.setCellWidget(0,8,self.comboCO2Var)


    def insertrowbelow(self):
        '''
        insert row below
        '''
        crow = self.tablebasket.currentRow()
        newrowindex = crow + 1

        self.tablebasket.insertRow(newrowindex)
        self.expTreatCombo = QComboBox()          
        self.expTreatCombo.addItem("Select from list") 

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

        self.tablebasket.setCellWidget(newrowindex,0,self.cropCombo)
        self.tablebasket.setCellWidget(newrowindex,1,self.expTreatCombo)
        self.tablebasket.setItem(newrowindex,2,QTableWidgetItem(""))
        self.tablebasket.setItem(newrowindex,3,QTableWidgetItem(""))
        self.tablebasket.setCellWidget(newrowindex,4,self.comboWaterStress)
        self.tablebasket.setCellWidget(newrowindex,5,self.comboNitroStress)
        self.tablebasket.setCellWidget(newrowindex,6,self.comboTempVar)
        self.tablebasket.setCellWidget(newrowindex,7,self.comboRainVar)
        self.tablebasket.setCellWidget(newrowindex,8,self.comboCO2Var)


    def showstationtypecombo(self):
        site = self.siteCombo.currentText()
        
        self.stationTypeCombo = QComboBox()        
        stationtypelists = read_weather_metaDBforsite(site)        
        self.stationTypeCombo.addItem("Select from list") 
        for key in stationtypelists:
            self.stationTypeCombo.addItem(stationtypelists[key])
        self.stationTypeCombo.currentIndexChanged.connect(self.showweathercombo)

        self.subgrid1.addWidget(self.stationTypeCombo,1,1,1,1)
        return True


    def showweathercombo(self):
        stationtype = self.stationTypeCombo.currentText()
        
        self.weatherCombo = QComboBox()        
        weather_id_lists = read_weather_id_forstationtype(stationtype)
            
        self.weatherCombo.addItem("Select from list") 
        for item in weather_id_lists:
            if item != "Add New Station Name":
                self.weatherCombo.addItem(item)

        self.subgrid1.addWidget(self.weatherCombo,1,3,1,1)
        return True


    def showexperimentcombo(self):
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        crop =  self.tablebasket.cellWidget(crow,0).currentText()

        stationtype = self.stationTypeCombo.currentText()
        if stationtype == "" or stationtype == "Select from list":
            self.cropCombo.setCurrentIndex(self.cropCombo.findText("Select from list"))
            return messageUser("You need to select 'Station Name' first!")
        weatherID = self.weatherCombo.currentText()
        if weatherID == "" or weatherID == "Select from list":
            self.cropCombo.setCurrentIndex(self.cropCombo.findText("Select from list"))
            return messageUser("You need to select 'Weather' first!")
        
        self.expTreatCombo = QComboBox()          
        if crop != "Select from list":
            self.experimentlists = getExpTreatByCropWeatherDate(crop,stationtype,weatherID)            
            self.expTreatCombo.addItem("Select from list") 
            for val in self.experimentlists:
                self.expTreatCombo.addItem(val)

        self.expTreatCombo.currentIndexChanged.connect(self.showtreatmentyear)
        self.tablebasket.setCellWidget(crow,1,self.expTreatCombo)
        self.tablebasket.setItem(crow,2,QTableWidgetItem(""))
        self.tablebasket.setItem(crow,3,QTableWidgetItem(""))
        return True


    def showtreatmentyear(self):
        crow = self.tablebasket.currentRow()
        if(crow == -1):
            crow = 0
        crop =  self.tablebasket.cellWidget(crow,0).currentText()
        experiment = self.tablebasket.cellWidget(crow,1).currentText()
        if experiment == "Select from list":
            self.tablebasket.setItem(crow,2,QTableWidgetItem(""))
            self.tablebasket.setItem(crow,3,QTableWidgetItem(""))
        else:
            cropExperimentTreatment = crop + "/" +  experiment
            # get weather years
            weatherdate_list = read_weatherdate_fromtreatment(cropExperimentTreatment)
            sdate = weatherdate_list[0].strftime("%m/%d/%Y")
            edate = weatherdate_list[-1].strftime("%m/%d/%Y")
            self.tablebasket.setItem(crow,2,QTableWidgetItem(sdate))
            self.tablebasket.setItem(crow,3,QTableWidgetItem(edate))
        return True


    def importfaq(self, thetabname=None):        
        cropname = ""
        faqlist = read_FaqDB(thetabname,cropname) 
        faqcount=0
        
        self.faqtree.clear()

        for item in faqlist:
            roottreeitem = QTreeWidgetItem(self.faqtree)
            roottreeitem.setText(0,item[2])
            childtreeitem = QTreeWidgetItem()
            childtreeitem.setText(0,item[3])
            roottreeitem.addChild(childtreeitem)


    def controlfaq(self):                
        if self.helpcheckbox.isChecked():
            self.importfaq("rotation")              
            self.faqtree.setVisible(True)
        else:
            self.faqtree.setVisible(False)
        

    def buttonrunclicked(self):        
        self.saveQTextStream()


    def saveQTextStream(self):
        # Extracting user values from the FUNNEL
        lsitename = self.siteCombo.currentText()
        lsoilname = self.soilCombo.currentText()
        lstationtype = self.stationTypeCombo.currentText()
        lweather = self.weatherCombo.currentText()

        # enter the record and get its ID
        if lsitename == "Select from list":
            return messageUser("You need to select Site.")

        if lsoilname == "Select from list":
            return messageUser("You need to select Soilname.")

        if lstationtype == "Select from list":
            return messageUser("You need to select Station Name.")

        if lweather == "Select from list":
            return messageUser("You need to select Weather.")

        # Need to validate if there is any gap among the treatment dates
        for irow in range(0,self.tablebasket.rowCount()-1):
            prevRunEndDate = datetime.strptime(self.tablebasket.item(irow,3).text(),'%m/%d/%Y')
            nextRunStartDate = datetime.strptime(self.tablebasket.item(irow+1,2).text(),'%m/%d/%Y')
            if (prevRunEndDate + timedelta(days=1)) != nextRunStartDate:
                return messageUser("There is a date gap or overlap between runs " + str(irow+1) + " and " + str(irow+2) + ".")

        rotationID = getNextRotationID()
 
        for irow in range(0,self.tablebasket.rowCount()):
            lcrop = self.tablebasket.cellWidget(irow,0).currentText()
            if lcrop == "Select from list":
                return messageUser("You need to select Crop.")

            lexperiment = self.tablebasket.cellWidget(irow,1).currentText()
            if lexperiment == "Select from list":
                return messageUser("You need to select Experiment/Treatment.")

            lwaterstress = self.tablebasket.cellWidget(irow,4).currentText()
            if(lwaterstress == "Yes"):
                waterStressFlag = 0
            else:
                waterStressFlag = 1

            lnitrostress = self.tablebasket.cellWidget(irow,5).currentText()
            if(lnitrostress == "Yes"):
                nitroStressFlag = 0
            else:
                nitroStressFlag = 1

            lstartdate = self.tablebasket.item(irow,2).text()
            lenddate = self.tablebasket.item(irow,3).text()

            lstartyear = int(lstartdate.split('/')[2])
            lendyear = int(lenddate.split('/')[2])

            ltempVar = self.tablebasket.cellWidget(irow,6).currentText()
            lrainVar = self.tablebasket.cellWidget(irow,7).currentText()
            lCO2Var = self.tablebasket.cellWidget(irow,8).currentText()
            if lCO2Var == "None":
                lCO2Var = 0

            cropTreatment = lcrop + "/" + lexperiment    
            simulation_name = update_pastrunsDB(rotationID,lsitename,cropTreatment,lstationtype,lweather,lsoilname,str(lstartyear),\
                                                str(lendyear),str(waterStressFlag),str(nitroStressFlag),str(ltempVar),str(lrainVar),str(lCO2Var)) 

            # this will execute the 2 exe's: uncomment it in final stage: 
            self.prepare_and_execute(simulation_name[0],rotationID,irow,lstartyear)                

        
    def prepare_and_execute(self,simulation_name,rotationID,irow,theyear):
        """
        this will create input files, and execute both exe's
        """
        self.simulation_name = str(simulation_name)
        field_path = os.path.join(runDir,self.simulation_name)
        print("/////*****+++++++++++++++++++++++++++++*****////")
        print(field_path)
        print("/////*****+++++++++++++++++++++++++++++*****////")
        if not os.path.exists(field_path):
            os.makedirs(field_path)

        field_name = self.siteCombo.currentText()  
        lsoilname = self.soilCombo.currentText()
        lstationtype = self.stationTypeCombo.currentText()
        lweather = self.weatherCombo.currentText()
        lcrop = self.tablebasket.cellWidget(irow,0).currentText()
        lexperiment = self.tablebasket.cellWidget(irow,1).currentText().split('/')[0]
        ltreatmentname = self.tablebasket.cellWidget(irow,1).currentText().split('/')[1]
        lwaterstress = self.tablebasket.cellWidget(irow,4).currentText()
        if(lwaterstress == "Yes"):
            waterStressFlag = 0
        else:
            waterStressFlag = 1
        lnitrostress = self.tablebasket.cellWidget(irow,5).currentText()
        if(lnitrostress == "Yes"):
            nitroStressFlag = 0
        else:
            nitroStressFlag = 1
        ltempVar = self.tablebasket.cellWidget(irow,6).currentText()
        lrainVar = self.tablebasket.cellWidget(irow,7).currentText()
        lCO2Var = self.tablebasket.cellWidget(irow,8).currentText()
        if lCO2Var == "None":
            lCO2Var = 0

        src_file = storeDir+'\\Water.DAT'
        dest_file = field_path+'\\WatMovParam.DAT'
        
        copyFile(src_file,dest_file)

        waterrotfilecontent=[]
        with open(dest_file, 'r') as read_file:
            waterrotfilecontent = read_file.readlines()
           

        sandcontent = WriteSoiData(lsoilname,field_name,field_path)       
        if sandcontent >= 75:
            with open(dest_file, 'w') as write_file:
                for line in waterrotfilecontent:
                        write_file.write(line.replace("-1.00000E+005", "-1.00000E+004"))  
                 

        #copy waterBound.dat file from store to runDir
        src_file= storeDir+'\\WaterBound.DAT'
        dest_file= field_path+'\\Water.dat'
        copyFile(src_file,dest_file)

        WriteBiologydefault(field_name,field_path)

        # Start
        #includes initial, management and fertilizer 
        rowSpacing, rootWeightPerSlab, cultivar = self.WriteIni(irow,field_name,field_path,waterStressFlag,nitroStressFlag) 
        if cultivar != "fallow":
            WriteCropVariety(lcrop,cultivar,field_name,field_path)
        else:
            src_file= storeDir+'\\fallow.var'
            dest_file= field_path+'\\fallow.var'
            copyFile(src_file,dest_file)
        WriteDripIrrigationFile(field_name,field_path)
        linSeaDate = None
        hourlyFlag = 1 if self.step_hourly.isChecked() else 0
        hourly_flag, edate = WriteWeather(lexperiment,ltreatmentname,lstationtype,lweather,field_path,ltempVar,lrainVar,lCO2Var,linSeaDate)

        
        WriteTimeFileData(ltreatmentname,lexperiment,lcrop,lstationtype,hourlyFlag,field_name,field_path,hourly_flag,1)

        WriteSoluteFile(lsoilname,field_path)
        WriteGasFile(field_path)
        
        
        WriteNitData(lsoilname,field_name,field_path,rowSpacing)
        self.WriteLayerGas(irow,lsoilname,field_name,field_path,rowSpacing,rootWeightPerSlab)
       # WriteSoiData(lsoilname,field_name,field_path)
        surfResType = WriteManagement(lcrop,lexperiment,ltreatmentname,field_name,field_path,rowSpacing)
        irrType = irrigationInfo(lcrop,lexperiment,ltreatmentname)
        WriteMulchGeo(field_path,surfResType)  
        o_t_exid = getTreatmentID(ltreatmentname,lexperiment,lcrop)
        WriteIrrigation(field_name,field_path,simulation_name,o_t_exid)
        WriteRunFile(lcrop,lsoilname,field_name,cultivar,field_path,lstationtype)            
        src_file= field_path+"\\"+field_name+".lyr"                    
        layerdest_file= field_path+"\\"+field_name+".lyr"
        createsoil_opfile= lsoilname
        grid_name = field_name
            
        pp = subprocess.Popen([createsoilexe,layerdest_file,"/GN",grid_name,"/SN",createsoil_opfile],cwd=field_path)
        while pp.poll() is None:
            time.sleep(1)

        runname = field_path+"\\Run"+field_name+".dat"       
        #endOpDate
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
                file_ext = ["g01","g03","g04","g05","g07"]
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

            # Debugging output directory and g01 file existence
            print("Output directory listing for debug:", field_path)
            for f in os.listdir(field_path):
                print("  FILE:", f)

            g01_path = os.path.join(field_path, field_name + ".g01")
            print("DEBUG: expecting g01 at:", g01_path, "exists:", os.path.exists(g01_path))

        except OSError as e:
            sys.exit("failed to execute twodsoil program, %s", str(e))

        missingRec = ""
        # Check for NaN on output files
        for ext in file_ext:
            g_name2 = field_path+"\\\\"+field_name+"."+ext
            table_name = ext.lower()+"_"+lcrop
            missingRec += checkNaNInOutputFile(table_name,g_name2)

        missingRec += checkNaNInOutputFile("plantStress_"+lcrop,field_path+"\\\\plantstress.crp")
        if lcrop == "potato" or lcrop == "soybean":
            missingRec += checkNaNInOutputFile("nitrogen_"+lcrop,field_path+"\\\\nitrogen.crp")

        if missingRec != "":
            self.simStatus.setText("<b>Something went wrong with this run for management " + ltreatmentname + " (" + lcrop + ").  The details are shown below.  We are unable to store results of this run until the problem can be resolved.  Additional details shown below.  The following file/columns displayed NaN values:</b><br>"+missingRec)
            delete_pastrunsDB_rotationID(rotationID,lcrop)
            self.rotationUpSig.emit(int(rotationID)) #emitting the simulation id (integer)
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
                    ingestGeometryFile(field_path+"\\\\"+field_name+".grd",g_name2,self.simulation_name)
                ingestOutputFile(table_name,g_name2,self.simulation_name)
                if remOutputFilesFlag:
                    os.remove(g_name)

            if lcrop != "fallow":
                ingestOutputFile("plantStress_"+lcrop,field_path+"\\\\plantstress.crp",self.simulation_name)
                if remOutputFilesFlag:
                    os.remove(field_path+"\\\\plantstress.crp")

            if lcrop == "soybean" or lcrop == "potato":
                ingestOutputFile("nitrogen_"+lcrop,field_path+"\\\\nitrogen.crp",self.simulation_name)
                if remOutputFilesFlag:
                    os.remove(field_path+"\\\\nitrogen.crp")

            self.simStatus.setText("<b>Check your simulation results on Rotation Output tab.</b>")
        self.rotationUpSig.emit(int(rotationID)) #emitting the simulation id (integer)
        self.simStatus.repaint()
        #end of prepare_and_execute


    def WriteIni(self,irow,field_name,field_path,waterStressFlag,nitroStressFlag):
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
        EndDate=0
        cultivar = "fallow"

        #get management tree                    
        cropname = self.tablebasket.cellWidget(irow,0).currentText()
        experiment = self.tablebasket.cellWidget(irow,1).currentText().split('/')[0]
        treatmentname = self.tablebasket.cellWidget(irow,1).currentText().split('/')[1]

        #find cropid
        #use crop to find exid in eperiment table
        #use exid and treatmentname to find tid from treatment table
        # use tid(o_t_exid) to find all the operations
        operationList = []
        exid = read_experimentDB_id(cropname,experiment)
        tid = read_treatmentDB_id(exid,treatmentname)
        operationList = read_operationsDB_id(tid) #gets all the operations

        for ii,jj in enumerate(operationList):
            if jj[1] == 'Simulation Start':
                if cropname == "fallow":
                # Placeholder so model doesn't use the date
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
                EndDate=jj[2] #month/day/year
                # End date should be greater than sowing date
                if cropname == "fallow":
                    EndDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=365)).strftime('%m/%d/%Y')
            
        site = self.siteCombo.currentText()
        soil = self.soilCombo.currentText()
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
                fout<<"Planting          Emergence          End	TimeStep(m)\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Stresses (Nitrogen, Water stress: 1-nonlimiting, 2-limiting): Simulation Type (1-meteorological, 2-physiological)"<<"\n"
                fout<<"Nstressoff  Wstressoff  Water-stress-simulation-method"<<"\n"
                fout<<"%d    %d    %d" %(waterStressFlag,nitroStressFlag,0)<<"\n"
                popSlab = RowSP/100 * 0.5 * 0.01 * pop  
                rootWeightPerSlab = seedpieceMass * 0.25 * popSlab
              #  rootWeightPerSlab = seedpieceMass * pop  * 0.25 * RowSP / 100 * 0.5 * 0.01
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
            fout<<"    0                     1  "<<"\n"         
        fh.close()
        return RowSP, rootWeightPerSlab, cultivar


    def WriteLayerGas(self,irow,soilname,field_name,field_path,rowSpacing,rootWeightPerSlab):
        '''
        Writes Layer file (*.lyr)
        If irow > 0, we will read information from previous run from cropOutput database to get part 
        of the information needed to build the lyr file. 
        '''
        # get Grid Ratio for the soil
        gridratio_list = read_soilgridratioDB(soilname)
        NumObs = len(gridratio_list)
        CODEC="UTF-8"
        # read rowSpacing
        filename = field_path+"\\"+field_name+".lyr"             
        fh = QFile(filename)
        #print("Debug: gridratio_list=",gridratio_list)

        if not fh.open(QIODevice.WriteOnly|QIODevice.Text):
            print("Could not open file")
        else:                  
            fout = QTextStream(fh)            
            fout.setCodec(CODEC)  
            fout<<"surface ratio    internal ratio: ratio of the distance between two neighboring nodes\n"
            for rrow in range(0,NumObs):
                record_tuple = gridratio_list[rrow]
                fout<<'%-14.3f%-14.3f%-14.3f%-14.3f' %(record_tuple[0],record_tuple[1],record_tuple[2],record_tuple[3])<<"\n"

            fout<<"RowSpacing"<<"\n"
            fout<<'%-6.1f' %(rowSpacing)

            fout<<"\n"<<" Planting Depth	  X limit for roots\n"
            for rrow in range(0,len(gridratio_list)):
                record_tuple=gridratio_list[rrow]
                fout<<'%-14.3f%-14.3f%-14.3f\n' %(record_tuple[4],record_tuple[5],rootWeightPerSlab)

            fout<<"Surface water Boundary Code  surface and bottom Gas boundary codes(for all bottom nodes) 1 constant -2 seepage face, 7 drainage, 4 atmospheric\n"
            fout<<"water boundary code for bottom layer, gas BC for the surface and bottom layers. Initial water variable depends on indicator variable. \n"
            for rrow in range(0,len(gridratio_list)):
                record_tuple=gridratio_list[rrow]
                fout<<'%-14d%-14d%-14d\n' %(record_tuple[6],record_tuple[7],record_tuple[8])

            fout<<" Bottom depth   Init Type  OM (%/100)   Humus_C    Humus_N    Litter_C    Litter_N    Manure_C    Manure_N  no3(ppm)  NH4  \
                   initial water   Tmpr     CO2     O2   N2O  Sand     Silt    Clay     BD     TH33     TH1500  thr ths tha th  Alfa    n   Ks  Kk  thk\n"
            fout<<" cm         w/m       Frac      ppm    ppm ppm    ppm    ppm   ppm    ppm   ppm     ppm   cm     0C     ppm   ppm  ----  fraction---     \
                   g/cm3    cm3/cm3   cm3/cm3\n"
            soilgrid_list = read_soilshortDB(soilname)

            # irow > 0, it means that this is not the first simulation on the rotetion, so to build the layer file we read information from geometry,
            # g03 and g07 tables for the previous simulation
            if irow > 0:
                # Previous run mumber
                runID = str(int(self.simulation_name) - 1)
                lcrop = self.tablebasket.cellWidget(irow-1,0).currentText()

                # Read geometry table for this simulation
                geo_df = readGeometrySimID(runID)

                tableName = "g03_" + lcrop
                updtSoilgridInfo = readSoilInfoCropOutputDB(lcrop,tableName,runID)
                new_df = updtSoilgridInfo['Date_Time'].str.split(' ',expand=True)
                updtSoilgridInfo['Date'] = new_df[0]
                maxDate = max(updtSoilgridInfo['Date'])
                updtSoilgridInfo = updtSoilgridInfo.loc[(updtSoilgridInfo['Date']==maxDate)]

                # Merge g03 table with geometry table
                updtSoilgrid = pd.merge(geo_df,updtSoilgridInfo,how='inner',left_on=['X','Y'],right_on=['X','Y'])

                # Since 2dsoil assigns Y values from the max depth ->0 where the surface is the maximum Depth and the bottom
                # of the profile is 0, we have to reverse this for the layer file. Thus we subtract the max depth from all
                # the Y's'
                maxY = max(updtSoilgrid['Y'])
                updtSoilgrid['Y'] = maxY-updtSoilgrid['Y']
                
                updtSoilgrid['thNew'] = updtSoilgrid['thNew'].astype(float)
                updtSoilgrid['Temp'] = updtSoilgrid['Temp'].astype(float)
                updtSoilgrid['mult'] = updtSoilgrid['mult'].astype(float)
                updtSoilgrid['NO3N'] = updtSoilgrid['NO3N'].astype(float)
                updtSoilgrid['NH4N'] = updtSoilgrid['NH4N'].astype(float)
                # Values in the g03 file are ug/cm3 of *soil water* => need to convert  NO3 grams NO3 per 1 million grams of SOIL for *lyr file
                # ug/cm3(water) * (cm3(water)/cm3(soil)) => ug/cm3(soil) 
                updtSoilgrid['NO3N_theta']= updtSoilgrid['NO3N'] * updtSoilgrid['thNew']

                # Constants used to calculate OM
                # Carbon proportion in OM
                percentC = 0.58
                # Nitrogen proportion in OM
                percentN = 0.05

                tableNameG07 = "g07_" + lcrop
                updtSoilgridInfoG07 = readSoilInfoCropOutputDB(lcrop,tableNameG07,runID)
                new_df = updtSoilgridInfoG07['Date_Time'].str.split(' ',expand=True)
                updtSoilgridInfoG07['Date'] = new_df[0]
                maxDate = max(updtSoilgridInfoG07['Date'])
                updtSoilgridInfoG07 = updtSoilgridInfoG07.loc[(updtSoilgridInfoG07['Date']==maxDate)]

                # Merge g07 table with geometry table
                updtSoilgridG07 = pd.merge(geo_df,updtSoilgridInfoG07,how='inner',left_on=['X','Y'],right_on=['X','Y'])

                # Since 2dsoil assigns Y values from the max depth ->0 where the surface is the maximum Depth and the bottom
                # of the profile is 0, we have to reverse this for the layer file. Thus we subtract the max depth from all
                # the Y's'
                maxY = max(updtSoilgridG07['Y'])
                updtSoilgridG07['Y'] = maxY-updtSoilgridG07['Y']
                           
                updtSoilgridG07['Humus_C'] = updtSoilgridG07['Humus_C'].astype(float)
                updtSoilgridG07['Humus_N'] = updtSoilgridG07['Humus_N'].astype(float)
                updtSoilgridG07['Litter_C'] = updtSoilgridG07['Litter_C'].astype(float)
                updtSoilgridG07['Litter_N'] = updtSoilgridG07['Litter_N'].astype(float)
                updtSoilgridG07['Manure_C'] = updtSoilgridG07['Manure_C'].astype(float)
                updtSoilgridG07['Manure_N'] = updtSoilgridG07['Manure_N'].astype(float)
                updtSoilgridG07['Root_C'] = updtSoilgridG07['Root_C'].astype(float)
                updtSoilgridG07['Root_N'] = updtSoilgridG07['Root_N'].astype(float)

            layer = 1
            for rrow in range(0,len(soilgrid_list)):
                record_tuple = soilgrid_list[rrow]
                record_tuple = [float(i) for i in record_tuple]
                if(record_tuple[1] == 1):
                    initType = "'m'"
                else:
                    initType = "'w'"

                if irow > 0:
                    # Start grouping the data by Layer
                    dfG03 = updtSoilgrid.loc[(updtSoilgrid['Layer']==layer)]
                    dfG07 = updtSoilgridG07.loc[(updtSoilgridG07['Layer']==layer)]
                    dfG03['BD'] = record_tuple[10]
                    
                    # calculate soil mass of node
                    dfG03['soilMass'] = dfG03['BD'] * dfG03['Area'] # result is grams of soil in node

                    # Calculate mass of NO3 and NH4 for each node
                    # theta= cm3 water/cm3 soil NO3 is ug NO3/cm3 soil water
                    # NO3N_theta = ug NO3/cm3 area
                    # NO3_Theta * area = total ug of NO3 in the node
                    dfG03['NO3N_theta_w']= dfG03['NO3N_theta']*dfG03['Area']  # result is total ug NO3 in the node
                    #NNH4 is not dissolved in water so we use soil mass
                    dfG03['NH4N_w'] = dfG03['NH4N']*dfG03['soilMass'] # this should give total ug of NH4 in the node
                                                                  
                    dfG07['Humus_C_w'] = dfG07['Humus_C']*dfG03['soilMass'] # this should give total ug of Humus_C  in the node
                                                                             # humus components are output as ug/g of soil in 2dsoil
                    dfG07['Humus_N_w'] = dfG07['Humus_N']*dfG03['soilMass']  # this should give total ug of Humus_N  in the node
                    dfG07['Litter_C_w'] = dfG07['Litter_C']*dfG03['soilMass'] # this should give total ug of Litter_C  in the node
                    dfG07['Litter_N_w'] = dfG07['Litter_N']*dfG03['soilMass'] # this should give total ug of Litter_N  in the node
                    dfG07['Manure_C_w'] = dfG07['Manure_C']*dfG03['soilMass'] # this should give total ug of Manure_C  in the node
                    dfG07['Manure_N_w'] = dfG07['Manure_N']*dfG03['soilMass'] # this should give total ug of Manure_N  in the node
                    dfG07['Root_C_w'] = dfG07['Root_C']*dfG03['soilMass']  # this should give total ug of Root_C  in the node 
                                                                                 # 2dsoil outputs RootC and RootN as ug/g soil
                    dfG07['Root_N_w'] = dfG07['Root_N']*dfG03['soilMass'] # this should give total ug of Root_N  in the node
                    # nodal calculations end here.
                 
                    dfG07 = dfG07.groupby(['Layer'],as_index=False).agg({'Humus_C_w':['sum'],'Humus_N_w':['sum'],'Litter_C_w':['sum'],
                                                                         'Litter_N_w':['sum'],'Manure_C_w':['sum'],'Manure_N_w':['sum'],
                                                                         'Root_C_w':['sum'],'Root_N_w':['sum']})
                    dfG07.columns = ["_".join(x) for x in dfG07.columns.ravel()]
                                     
                    # Leave only necessary columns
                    dfG03 = dfG03[['thNew','mult','NO3N_theta_w','NH4N_w','Temp','Layer','soilMass']]
                    dfG03 = dfG03.groupby(['Layer'],as_index=False).agg({'thNew':['mean'],'NO3N_theta_w':['sum'],'NH4N_w':['sum'],
                                                                         'soilMass':['sum'],'Temp':['mean'],'mult':['mean']})
                    dfG03.columns = ["_".join(x) for x in dfG03.columns.ravel()]
                    
                   
                    initType = "'w'"

                    # Calculate OM and Matric potential (all as scalars, not Series)
                    Humus_C_layer = (dfG07['Humus_C_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Humus_N_layer = (dfG07['Humus_N_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Litter_C_layer = (dfG07['Litter_C_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Litter_N_layer = (dfG07['Litter_N_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Manure_C_layer = (dfG07['Manure_C_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Manure_N_layer = (dfG07['Manure_N_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Root_C_layer = (dfG07['Root_C_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    Root_N_layer = (dfG07['Root_N_w_sum'] / dfG03['soilMass_sum']).iloc[0]

                    OM_layer = (Humus_C_layer + Root_C_layer) / percentC + Humus_N_layer + Root_N_layer
                    # 1% OM is .01 g OM/g soil = 10 mg OM/g = 10,000 ug/g
                    # In 2dsoil OM is input as a fraction or %/100
                    OM_frac = OM_layer / 10000.0 / 100.0

                    # Convert "ug/cm3(soil)" to "ug/g (soil)" (ppm) by dividing by bulk density
                    NO3_layer = (dfG03['NO3N_theta_w_sum'] / dfG03['soilMass_sum']).iloc[0]
                    NH4_layer = (dfG03['NH4N_w_sum'] / dfG03['soilMass_sum']).iloc[0]

                    thNew_mean = float(dfG03['thNew_mean'].iloc[0])
                    temp_mean = float(dfG03['Temp_mean'].iloc[0])
                    mult_mean = float(dfG03['mult_mean'].iloc[0])  # note: included for completeness if you use it later

                    fout<< '%-14d%-6s%-14.5f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f\
                           %-14.3f%-14.3f%-14.3f%-14.3f%-14.3f' % (
                        int(record_tuple[0]),
                        initType,
                        OM_frac,
                        Humus_C_layer,
                        Humus_N_layer,
                        Litter_C_layer,
                        Litter_N_layer,
                        Manure_C_layer,
                        Manure_N_layer,
                        NO3_layer,
                        NH4_layer,
                        thNew_mean,
                        temp_mean,
                        record_tuple[22],
                        record_tuple[23],
                        record_tuple[24],
                        record_tuple[7] / 100.0,
                        record_tuple[8] / 100.0,
                        record_tuple[9] / 100.0,
                        record_tuple[10],
                        record_tuple[11],
                        record_tuple[12],
                        record_tuple[13],
                        record_tuple[14],
                        record_tuple[15],
                        record_tuple[16],
                        record_tuple[17],
                        record_tuple[18],
                        record_tuple[19],
                        record_tuple[20],
                        record_tuple[21]
                    ) << "\n"
                    '''
                    initType = "'w'"
                    # Calculate OM and Matric potential
                    Humus_C_layer = dfG07['Humus_C_w_sum']/dfG03['soilMass_sum']  #units are ug/g or ppm
                    Humus_N_layer = dfG07['Humus_N_w_sum']/dfG03['soilMass_sum']
                    Litter_C_layer = dfG07['Litter_C_w_sum']/dfG03['soilMass_sum']
                    Litter_N_layer = dfG07['Litter_N_w_sum']/dfG03['soilMass_sum']
                    Manure_C_layer = dfG07['Manure_C_w_sum']/dfG03['soilMass_sum']
                    Manure_N_layer = dfG07['Manure_N_w_sum']/dfG03['soilMass_sum']
                    Root_C_layer = dfG07['Root_C_w_sum']/dfG03['soilMass_sum']
                    Root_N_layer = dfG07['Root_N_w_sum']/dfG03['soilMass_sum']
                    
                    OM_layer =  (Humus_C_layer+Root_C_layer)/percentC+Humus_N_layer+Root_N_layer   # total ug of soil OM components
                    # 1% OM is .01 g OM/g soil = 10 mg OM/g= 10,000 ug/g
                    # in 2dsoil OM is input as a fraction or %100 
                    dfG07['OM']=OM_layer/10000.0/100
        
                    # Convert "ug/cm3(soil)" to "ug/g (soil)" same as ppm, by dividing by Bulk density (g/cm3)
                    #DT  NO3 is now total ug in the grams in the layer. NO3 in the layer file is mg/gram
                    NO3_layer = dfG03['NO3N_theta_w_sum']/dfG03['soilMass_sum']  #result is mg NO3/g soil
                    NH4_layer = dfG03['NH4N_w_sum']/dfG03['soilMass_sum']   # result is mg NH4/g soil

                    fout<<'%-14d%-6s%-14.5f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f\
                           %-14.3f%-14.3f%-14.3f%-14.3f%-14.3f' %(record_tuple[0],initType,dfG07['OM'],Humus_C_layer,Humus_N_layer,Litter_C_layer,Litter_N_layer,Manure_C_layer,Manure_N_layer,
                           NO3_layer,NH4_layer,dfG03['thNew_mean'],dfG03['Temp_mean'],record_tuple[22],record_tuple[23],record_tuple[24],record_tuple[7]/100,record_tuple[8]/100,record_tuple[9]/100,record_tuple[10],record_tuple[11],
                           record_tuple[12],record_tuple[13],record_tuple[14],record_tuple[15],record_tuple[16],record_tuple[17],record_tuple[18],record_tuple[19],record_tuple[20],
                           record_tuple[21])<<"\n"
                    '''
                else:
                    fout<<'%-14d%-6s%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f%-14.3f\
                           %-14.3f%-14.3f%-14.3f%-14.3f%-14.3f' %(record_tuple[0],initType,record_tuple[2],-1,-1,0,0,0,0,record_tuple[3],record_tuple[4],record_tuple[5],record_tuple[6],
                           record_tuple[22],record_tuple[23],record_tuple[24],record_tuple[7]/100,record_tuple[8]/100,record_tuple[9]/100,record_tuple[10],record_tuple[11],record_tuple[12],record_tuple[13],
                           record_tuple[14],record_tuple[15],record_tuple[16],record_tuple[17],record_tuple[18],record_tuple[19],record_tuple[20],record_tuple[21])<<"\n"
                layer = layer + 1
        fout<<"\n"
        fh.close()


    def refresh(self):
        sitelists = read_sitedetailsDB()
        lsitename = self.siteCombo.currentText()
        self.siteCombo = QComboBox()
        self.siteCombo.addItem("Select from list")
        for item in sitelists: 
            self.siteCombo.addItem(item)
        if(self.siteCombo.findText(lsitename, QtCore.Qt.MatchFixedString) >= 0):
            self.siteCombo.setCurrentIndex(self.siteCombo.findText(lsitename, QtCore.Qt.MatchFixedString))
        else:
            self.siteCombo.setCurrentIndex(0)
        self.siteCombo.currentIndexChanged.connect(self.showstationtypecombo)
        self.subgrid1.addWidget(self.siteCombo,0,1,1,1)

        self.soillists = read_soilDB()
        lsoilname = self.soilCombo.currentText()
        self.soilCombo = QComboBox()
        self.soilCombo.addItem("Select from list")
        for key in self.soillists:            
            self.soilCombo.addItem(key)
        if(self.soilCombo.findText(lsoilname, QtCore.Qt.MatchFixedString) >= 0):
            self.soilCombo.setCurrentIndex(self.soilCombo.findText(lsoilname, QtCore.Qt.MatchFixedString))
        else:
            self.soilCombo.setCurrentIndex(0)
        self.subgrid1.addWidget(self.soilCombo,0,3,1,1)

        stationtypelists = read_weather_metaDBforsite(lsitename)
        lstationtype = self.stationTypeCombo.currentText()
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
        self.subgrid1.addWidget(self.stationTypeCombo,1,1,1,1)

        weather_id_lists = read_weather_id_forstationtype(lstationtype)
        lweather = self.weatherCombo.currentText()
        self.weatherCombo = QComboBox()        
        self.weatherCombo.addItem("Select from list")
        for item in weather_id_lists:
            if item != "Add New Station Name":
                self.weatherCombo.addItem(item)
                if(self.weatherCombo.findText(lweather, QtCore.Qt.MatchFixedString) >= 0):
                    self.weatherCombo.setCurrentIndex(self.weatherCombo.findText(lweather, QtCore.Qt.MatchFixedString))
                else:
                    self.weatherCombo.setCurrentIndex(0)
        self.subgrid1.addWidget(self.weatherCombo,1,3,1,1)

        for irow in range(0,self.tablebasket.rowCount()):
            lcrop = self.tablebasket.cellWidget(irow,0).currentText()
            self.experimentlists = getExpTreatByCrop(lcrop)            
            lexptreat = self.tablebasket.cellWidget(irow,1).currentText()
            self.expTreatCombo = QComboBox()          
            self.expTreatCombo.addItem("Select from list") 
            for val in self.experimentlists:
                self.expTreatCombo.addItem(val)
            if(self.expTreatCombo.findText(lexptreat, QtCore.Qt.MatchFixedString) >= 0):
                self.expTreatCombo.setCurrentIndex(self.expTreatCombo.findText(lexptreat, QtCore.Qt.MatchFixedString))
            else:
                self.expTreatCombo.setCurrentIndex(0)
            self.expTreatCombo.currentIndexChanged.connect(self.showtreatmentyear)
            self.tablebasket.setCellWidget(irow,1,self.expTreatCombo)