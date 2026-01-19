import subprocess
import time
import os
import pandas as pd
import sys
import re
import datetime
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout,  QVBoxLayout, QPushButton, QTabWidget, QGridLayout,\
                            QSpacerItem, QSizePolicy, QHeaderView,  QCheckBox, QGridLayout, QTextEdit  \
                              #QMenu,QGroupBox,QTableWidget, QTableWidgetItem, QComboBox,QRadioButton, QButtonGroup,
from PyQt5.QtCore import QFile, QTextStream, pyqtSignal, QCoreApplication # QRect
#from pyqtgraph import PlotWidget, plot
#from PyQt5.QtChart import QChart, QChartView, QPieSeries
#from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
#from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QDir
from CustomTool.custom1 import *
from CustomTool.UI import *
from CustomTool.generateModelInputFiles import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from TabbedDialog.SeasonalTab import *
#from TabbedDialog.OutputTab import Output2_Widget
#from subprocess import Popen
import matplotlib
matplotlib.use('TkAgg') #backend
import matplotlib.pyplot as plt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

#from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar





#matplotlib.use('TkAgg',force=True)

import pyqtgraph as pg
#import multiprocessing as mp
#from multiprocessing import Process
#import concurrent.futures

#print("Number of processors: ", mp.cpu_count())

global classimDir
global runDir
global storeDir


classimDir = getClassimDir()
runDir = os.path.join(classimDir,'run')
storeDir = os.path.join(runDir,'store')
tempDir0 = os.path.join(runDir, 'temp0')
tempDir1 = os.path.join(runDir, 'temp1')
tempDir2 = os.path.join(runDir, 'temp2')
tempDir3 = os.path.join(runDir, 'temp3')


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
    print('ExpertSysTab Error: Missing storeDir')

class ExpertSys_Widget(QWidget):
    # Add a signal
    expertsyssig = pyqtSignal(int)    
    changedValue = pyqtSignal(int)
    def __init__(self):
        super(ExpertSys_Widget,self).__init__()
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
    #    self.importfaq("expertsys")              
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
       # self.helpcheckbox = QCheckBox("Turn FAQ on?")
     #   self.helpcheckbox.setChecked(False)
    #    self.helpcheckbox.stateChanged.connect(self.controlfaq)

      #  urlLink="<a href=\"https://youtu.be/DXj5BOi09IU\">Click here \
      #          to watch the Expert System Tab Video Tutorial</a><br>"
        self.expSysVidlabel=QLabel()
        self.expSysVidlabel.setOpenExternalLinks(True)
      #  self.expSysVidlabel.setText(urlLink)       
     
        self.soilwater_df = None
     #   self.SoiWat = QCheckBox("Soil Water Content")
     #   self.SoiWat.setChecked(False)
     #   self.SoiWat.stateChanged.connect(self.SoiWatCheck)

        self.display1 = QTabWidget()
        self.figure1 = plt.figure(figsize=(5, 5))
        self.figureCanvas1 = FigureCanvas(self.figure1)
        self.display2 = QTabWidget()
        self.figure2 = plt.figure(figsize=(5, 5))
        self.figureCanvas2 = FigureCanvas(self.figure2)
        self.display3 = QTabWidget()
        self.figure3 = plt.figure(figsize=(5, 5))
        self.figureCanvas3 = FigureCanvas(self.figure3)
        self.display4 = QTabWidget()
        self.figure4 = plt.figure(figsize=(5, 5))
        self.figureCanvas4 = FigureCanvas(self.figure4)
        
        self.irrOptionlabel = QLabel("Run Simulation with Irrigation")
 #       self.irrcheckbox = QCheckBox("Irrigation")
     #   self.comboirrOption = QComboBox()
        self.irrOption = read_irrOption()
       
        self.runButton = QPushButton()
  
        self.simStatus = QLabel("")
        self.simStatus.setWordWrap(True)
        self.runButton.setText("Run")
        
        self.buttonreset = QPushButton("Reset")
        
        self.inSeasonirr = [0, 1, 2, 3]
   
        self.runButton.clicked.connect(lambda: self.RunSimulation(self.inSeasonirr))
        self.buttonreset.clicked.connect(self.reset)
        
        self.comButtonlabel = QLabel("Yield Comparison")
        self.comStatus = QLabel("")
        self.comStatus.setWordWrap(True)
        self.comButton = QPushButton()
        self.comButton.setText("Compare")
        self.comButton.clicked.connect(lambda: self.CompareSimulation(self.newsimulationID))

    
        self.outputlabel = QLabel("Simulation Details")   
        self.genInfoBoxSumLabel = QLabel()
        self.outputDetailslabel0 = QLabel()
        self.outputDetailslabel1 = QLabel()
        self.outputDetailslabel2 = QLabel()
        self.outputDetailslabel3 = QLabel()
        self.outputIrriglabel = QLabel()
        
        self.mainlayout1 = QVBoxLayout()
           
        self.hl1 = QHBoxLayout()
        self.hl1.addWidget(self.tab_summary)     
        self.hl1.setSpacing(0) 
        
        self.soilwatergrid = QGridLayout()
        self.soilwatergrid.addWidget(self.figureCanvas1, 0,1) 
        self.soilwatergrid.addWidget(self.figureCanvas2, 1,1) 
        self.soilwatergrid.addWidget(self.figureCanvas3, 1,0) 
        self.soilwatergrid.addWidget(self.figureCanvas4, 0,0) 
        

        self.vl1 = QVBoxLayout() 
        self.vl1.addLayout(self.hl1)
        self.vl1.addWidget(self.expSysVidlabel)
   #     self.vl1.addWidget(self.helpcheckbox)
      #  self.vl1.addWidget(self.SoiWat)
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vl1.setContentsMargins(0,0,0,0)
       ##### self.vl1.addWidget(self.display1)     

        self.vl1.addStretch(1)  
        
        self.output = QVBoxLayout()
        self.output.addWidget(self.outputlabel)
        self.output.setAlignment(self.outputlabel, Qt.AlignTop)
        self.output.addWidget( self.genInfoBoxSumLabel)
        self.output.addStretch()     
        
        self.vl3 = QVBoxLayout()
        self.vl3.addLayout(self.output)
        self.vl3.addWidget(self.outputIrriglabel)
        self.vl3.addWidget(self.outputDetailslabel0)
        self.vl3.addWidget(self.outputDetailslabel1)
        self.vl3.addWidget(self.outputDetailslabel2)
        self.vl3.addWidget(self.outputDetailslabel3)
        self.vl3.addStretch() 
        self.plot = pg.plot()
        self.vl3.addWidget(self.plot)
        

        self.vl2 = QGridLayout()   

        self.vl2.addLayout(self.soilwatergrid, 0,0)
        self.vl2.addLayout(self.vl3, 0,1)
        
        
        
       
        self.hl2 = QHBoxLayout() 
        self.hl2.addWidget(self.irrOptionlabel)

        self.hl2.addWidget(self.runButton)
        self.hl2.addWidget(self.buttonreset)
        self.hl2.addWidget(self.simStatus)   

    
        
        self.hl4 = QHBoxLayout() 
        self.hl4.addWidget(self.comButtonlabel)
        self.hl4.addWidget(self.comButton)
        self.hl4.addWidget(self.comStatus)

        self.vl2.addLayout(self.hl2, 1,0)

        self.vl2.addLayout(self.hl4, 3,0)

          
        self.mainlayout1.addLayout(self.vl1)  
        self.mainlayout1.addLayout(self.vl2)
        self.setLayout(self.mainlayout1)
        

    def reset(self):
        plt.ion()    
        self.figureCanvas1.figure.clf()
        self.figureCanvas2.figure.clf()
        self.figureCanvas3.figure.clf()
        self.figureCanvas4.figure.clf()
 
    def make_connection(self,exsys_object):
        exsys_object.exsystemsig.connect(self.populate)


    def populate(self):     
        self.prevsimulationID = read_simulationID()   
        
        self.result = extract_pastrunsExpSys(self.prevsimulationID)
        field_name= self.result['site'] 
        self.sitename = field_name.iloc[0]        
        lsoilname = self.result['soil'] 
        self.soilname = lsoilname.iloc[0] 
        lstationtype = self.result['stationtype'] 
        self.stationtypename = lstationtype.iloc[0]
        lweather = self.result['weather'] 
        self.weather = lweather.iloc[0]
        strVar = pd.Series(self.result['treatment'])
        strVar_split = strVar.str.split('/')
        lcrop = strVar_split.str[0]
        self.crop = lcrop.iloc[0]
        lexperiment =  strVar_split.str[1]
        self.experimentname = lexperiment.iloc[0]
        ltreatmentname = strVar_split.str[-1]
        self.treatmentname = ltreatmentname.iloc[0]  
        
        self.soilwater_df = []
        self.soilwater_df= readSoilWater(self.prevsimulationID, self.crop)        
        self.last_soilwater = self.soilwater_df.iloc[-1:]       
        self.soilwater_content = float(self.last_soilwater['ThetaAvail'].values[0] )
       # self.soilwater_content = self.soilwater_content.    
        self.needed_water = float(1.000-self.soilwater_content)  
     #   print(type(self.soilwater_content), type(self.needed_water))
        
         # Ensure sizes sum to 1
        total = self.soilwater_content + self.needed_water
        if not np.isclose(total, 1.0):
            print("Sizes do not sum to 1")
            return
        
        labels = ['Soil Water', 'Soil Water Deficit']

        sizes = [round(self.soilwater_content, 3), round(self.needed_water, 3)] 
       # self.figureCanvas1.figure.clf()
        # Check if sizes contain valid data
        if sizes and all(isinstance(size, (int, float)) for size in sizes):
            ax = self.figure1.add_subplot(111)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title("No Irrigation")
            self.figureCanvas1.draw()
        else:
            print("Invalid data for pie chart")
    
        
        inseasonDate = self.last_soilwater['Date_Time']
        inseasonDate = inseasonDate.values[0]
      #  print(inseasonDate)
        input_datetime = datetime.strptime(inseasonDate, '%Y-%m-%d %H:%M:%S')   
       # input_datetime += timedelta(1)
        formatted_inseasonDate = input_datetime.strftime('%m/%d/%Y')

        self.simSummaryGen = "<br>" + " " + "<b>Site: </b>" + self.sitename + "  " 
        self.simSummaryGen += "<b>Soil: </b>" + self.soilname + "  " 
        self.simSummaryGen += "<b>Weather: </b>" + self.weather  #self.stationtypename 
        self.simSummaryGen += "<br>" + " " + "<b>Crop: </b>" + self.crop + "  " 
        self.simSummaryGen += "<b>Experiment: </b>" + self.experimentname + "  " 
        self.simSummaryGen += "<b>Treatment: </b>" + self.treatmentname
       # self.simSummaryGen += "<b>Water: </b>" + self.soilwater_content
        self.simSummaryGen += "<br><b>In-Season Date:  </b>" + formatted_inseasonDate
        self.genInfoBoxSumLabel.setText(self.simSummaryGen)
        
    

    def RunSimulation(self,inSeasonirr):        
        # Deleting temp folder
        temp_folder0 = QDir(tempDir0)
        temp_folder1 = QDir(tempDir1)
        temp_folder2 = QDir(tempDir2)
        temp_folder3 = QDir(tempDir3)
        
        for file_info in temp_folder0.entryInfoList():
            if file_info.isFile():
                temp_folder0.remove(file_info.fileName())           
        for file_info in temp_folder1.entryInfoList():
            if file_info.isFile():
                temp_folder1.remove(file_info.fileName())                     
        for file_info in temp_folder2.entryInfoList():
            if file_info.isFile():
                temp_folder2.remove(file_info.fileName())                  
        for file_info in temp_folder3.entryInfoList():
            if file_info.isFile():
                temp_folder3.remove(file_info.fileName())
   
        self.newsimulationID = self.prevsimulationID + 1        
        self.prepareandexecuteExpSys(self.newsimulationID, self.result, inSeasonirr) 

        
            
    
    
    def selInSeadate(self,):
        conn, c = openDB('crop.db')
        if c:
            c1 = c.execute("SELECT inSeaDate FROM inSeaIrri ORDER BY ID DESC LIMIT 1")
            c1_row = c1.fetchone()
            conn.close()
        linSeaDate = c1_row[0]
        return linSeaDate
       
   
        
    def prepareandexecuteExpSys(self,simulation_name,result, inSeasonirr):
        """
        this will create input files, and execute both exe's
        """

        simulation_names = [simulation_name + i for i in range(4)]
        tempDirs = [tempDir0, tempDir1, tempDir2, tempDir3]
        field_paths = tempDirs
        str_field_paths = [str(tempDir) for tempDir in tempDirs]
        
        #field_paths= [field_path0, field_path1, field_path2, field_path3]

        # Assign individual variables if needed
        sim0, sim1, sim2, sim3 = simulation_names
        str_field_path0, str_field_path1, str_field_path2, str_field_path3 = str_field_paths

        
        for field_path in field_paths:
            if not os.path.exists(field_path):
                os.makedirs(field_path)
      

        field_name= result['site']       
        theyear = result['startyear']
        
        lwaterstress = result['waterstress'] 

        if (lwaterstress == 0).all():
            waterStressFlag = 0
        else:
            waterStressFlag = 1
        lnitrostress = result['nitrostress'] 
        if (lnitrostress == 0).all():
            nitroStressFlag = 0
        else:
            nitroStressFlag = 1
        ltempVar = result['tempVar'] 
        str_ltempVar = ltempVar.iloc[0]

        lrainVar = result['rainVar'] 
        str_lrainVar = lrainVar.iloc[0]

        lCO2Var = result['CO2Var'] 
        str_lCO2Var = lCO2Var.iloc[0]
        
        #copy water.dat file from store to runDir
         # Copy water.dat file from store to runDir
        src_file = storeDir + '\\Water.DAT'
        dest_files = [f'{field_path}\\WatMovParam.DAT' for field_path in field_paths]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

        waterfilecontent = []
        with open(dest_files[0], 'r') as read_file:
            waterfilecontent = read_file.readlines()
        
       
            
 #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
 
        sandcontent = WriteSoiData(self.soilname, self.sitename, str_field_paths[0]) 
        src_file_soil = f'{field_paths[0]}\\{self.sitename}.soi'
        if sandcontent > 75:
            with open(src_file_soil, 'w') as write_file:
                for line in waterfilecontent:
                    write_file.write(line.replace("-1.00000E+005", "-1.00000E+004"))  
                    
        src_file_water = storeDir + '\\WaterBound.DAT'
        WriteBiologydefault(field_name, field_paths[0])
        src_file_bio= f'{field_paths[0]}\\BiologyDefault.bio'
        
        for i in range(4):          
            dest_file = f'{field_paths[i]}\\{self.sitename}.soi'
            copyFile(src_file_soil, dest_file)            
            dest_file = f'{field_paths[i]}\\Water.dat' 
            copyFile(src_file_water, dest_file)            
            dest_file = f'{field_paths[i]}\\BiologyDefault.bio' 
            copyFile(src_file_bio, dest_file)

        self.linSeaDate = self.selInSeadate()

        inSeasonirrs = [inSeasonirr[0], inSeasonirr[1], inSeasonirr[2], inSeasonirr[3]]
        rowSpacings = []
        rootWeightPerSlabs = []
        cultivars = []
        irrs = []

        for str_field_path, inSeasonirr in zip(str_field_paths, inSeasonirrs):
            rowSpacing, rootWeightPerSlab, cultivar, irr = self.WriteIni(self.sitename, str_field_path, str(theyear), str(theyear), str(waterStressFlag), str(nitroStressFlag), str(inSeasonirr), self.linSeaDate)
          #  print("PPPPPPPPPPPP")
         #   print(irr)
            rowSpacings.append(rowSpacing)
            rootWeightPerSlabs.append(rootWeightPerSlab)
            cultivars.append(cultivar)
            irrs.append(irr)
       
        for i, cultivar in enumerate(cultivars):
            if cultivar != "fallow":
                WriteCropVariety(self.crop, cultivar, self.sitename, str_field_paths[i])
            else:
                src_file = storeDir + '\\fallow.var'
                dest_file = field_paths[i] + '\\fallow.var'
                copyFile(src_file, dest_file)

        
  #      print(str_field_paths[0])

        WriteDripIrrigationFile(self.sitename,str_field_paths[0])       
        src_file = field_paths[0] + '\\' + self.sitename + '.drp'
        dest_files = [f'{field_paths[i]}\\{self.sitename}.drp' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

        hourly_flag, self.edate = WriteWeatherExpSysIrrig(self.experimentname, self.treatmentname, self.stationtypename, self.weather, str_field_paths[0], str_ltempVar, str_lrainVar, str_lCO2Var, self.linSeaDate)

        src_file = field_paths[0] + '\\' + self.stationtypename + '.wea'
        dest_files = [f'{field_paths[i]}\\{self.stationtypename}.wea' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)
     
       # Copy .cli files
        src_file = field_paths[0] + '\\' + self.stationtypename + '.cli'
        dest_files = [f'{field_paths[i]}\\{self.stationtypename}.cli' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

        WriteSoluteFile(self.soilname, str_field_paths[0])
        src_file = field_paths[0] + '\\NitrogenDefault.sol'
        dest_files = [f'{field_paths[i]}\\NitrogenDefault.sol' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)
        
    
        WriteGasFile(str_field_path0)
        src_file = field_paths[0] + '\\GasID.gas'
        dest_files = [f'{field_paths[i]}\\GasID.gas' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

        # Code is for daily data
        # hourlyFlag = 1 if self.step_hourly.isChecked() else 0
        hourlyFlag = 0
        WriteTimeFileData(self.treatmentname, self.experimentname, self.crop, self.stationtypename, hourlyFlag, self.sitename, str_field_path0, hourly_flag, 0)
        src_file = field_paths[0] + '\\' + self.sitename + '.tim'
        dest_files = [f'{field_paths[i]}\\{self.sitename}.tim' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

      
        o_t_exid = getTreatmentID(self.treatmentname,self.experimentname,self.crop)
        irrType = "Sprinkler"
        
       # str_field_paths = [str_field_path0, str_field_path1, str_field_path2, str_field_path3]
        
        surfResType =[]
        
        for str_field_path, rowSpacing, rootWeightPerSlab, in zip(str_field_paths, rowSpacings, rootWeightPerSlabs):
            WriteNitData(self.soilname, self.sitename, str_field_path, rowSpacing)
            self.WriteLayerGas(self.soilname,self.sitename,str_field_path,rowSpacing,rootWeightPerSlab)
            surfResType_var=WriteManagement(self.crop,self.experimentname,self.treatmentname,self.sitename,str_field_path,rowSpacing)  
            surfResType.append(surfResType_var)
            WriteMulchGeo(str_field_path,surfResType_var)
        for sim, irr, str_field_path in zip(simulation_names, irrs, str_field_paths):
          #  print(sim, irr, str_field_path)
            WriteIrrigationExpSys(self.sitename,str_field_path,irrType, sim, o_t_exid, irr)
        

        for str_field_path in zip(str_field_paths):
            WriteRunFile(self.crop,self.soilname,self.sitename,cultivar,str_field_path[0],self.stationtypename)          
       
      
            
        self.path0 = str_field_path0
        self.path1 = str_field_path1
        self.path2 = str_field_path2
        self.path3 = str_field_path3
        
        for i, sim in enumerate(simulation_names):
            self.runPath(i, sim)
            
        exid = read_experimentDB_id(self.crop,self.experiment)
        tid = read_treatmentDB_id(exid,self.treatment)
        plantDensity = getPlantDensity(tid)	
     #   print(inSeasonirrs)
     
                    
        for _, (inSeasonirr_counter, sim) in enumerate(zip(inSeasonirrs, simulation_names)):
            runname = runDir + "\\" + "temp" + str(inSeasonirr_counter) + "\\" +  self.sitename + ".g01"
         #   print("Runname: ", runname)
                
            if self.crop == "potato":
                potato_df =   pd.read_csv(runname, usecols = ['tuberDM'])
                last_ptato_df = potato_df.tail(1)      
                agroDataTuple = last_ptato_df['tuberDM']
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                
            elif self.crop == "soybean":
                soy_df =   pd.read_csv(runname, usecols = ['    seedDM'])
                last_soy_df = soy_df.tail(1) 
                agroDataTuple = last_soy_df[ '    seedDM']
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                       
                
            elif self.crop == "maize":                        
                corn_df = pd.read_csv(runname) #, usecols = ['earDM']) #, 'date', 'Note     '])
                last_corn_df = corn_df.tail(1)    
                last_corn = last_corn_df['earDM']
                agroDataTuple = last_corn * 0.86   
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10
             #   print(last_corn,agroDataTuple)
                
            elif self.crop == "cotton":
                cotton_df =   pd.read_csv(runname)  
                last_cotton_df = cotton_df.tail(1) 
                agroDataTuple = last_cotton_df['       Yield']
                self.Yield = agroDataTuple.iloc[0]
                       
            else:
                pass	
                    
       
      
            date_object = datetime.strptime(self.linSeaDate, "%Y-%m-%d")
            new_date = date_object + timedelta(days=1)
            formatted_date = new_date.strftime("%m/%d/%Y") 


            if inSeasonirr_counter == 0:           
                self.yld0 = self.Yield
                self.simOutput0 = "Yield (Irrigation 0 inch): " + str(round(self.yld0))  + " kg/ha"   
               
                self.outputDetailslabel0.setText(self.simOutput0)           
                expSysOutput(sim0, inSeasonirr_counter, self.Yield)
            
            elif inSeasonirr_counter == 1:
                str_field_path1 = str(tempDir1)
                csv_file1 = str_field_path1+"\\"+self.sitename+"."+'G05'
                df1= pd.read_csv(csv_file1)
             
                thetaAvail_df1 = df1.loc[df1.iloc[:,1] == '     '+ formatted_date, '     ThetaAvail']              
                theta_value = thetaAvail_df1.iloc[0]
                needed_water1 = 1.000- theta_value 
                labels = ['Soil Water', 'Soil Water Deficit']
                sizes = [theta_value, needed_water1]
                ax = self.figure2.add_subplot(111)
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title("Irrigation = 1 inch")
                self.figureCanvas2.draw()   
                
                self.yld1 = self.Yield 
                self.simOutput1 = "Yield (Irrigation 1 inch): " + str(round(self.yld1)) + " kg/ha"              
                self.outputDetailslabel1.setText(self.simOutput1)           
                expSysOutput(sim1, inSeasonirr_counter, self.Yield)
                
            elif inSeasonirr_counter == 2:
                str_field_path2 = str(tempDir2)
                csv_file2 = str_field_path2+"\\"+self.sitename+"."+'G05'
                df2 = pd.read_csv(csv_file2)               
                thetaAvail_df2 = df2.loc[df2.iloc[:,1] == '     '+ formatted_date, '     ThetaAvail']                            
                theta_value = thetaAvail_df2.iloc[0]                       
                needed_water2 = 1.000-theta_value
                labels = ['Soil Water', 'Soil Water Deficit']
                sizes = [theta_value, needed_water2]
                ax = self.figure3.add_subplot(111)
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title("Irrigation = 2 inch")
                self.figureCanvas3.draw() 
                
                self.yld2 = self.Yield  
                self.simOutput2 = "Yield (Irrigation 2 inch): " + str(round(self.yld2))  + " kg/ha"                    
                self.outputDetailslabel2.setText(self.simOutput2)           
                expSysOutput(sim2, inSeasonirr_counter, self.Yield)
            
            elif inSeasonirr_counter == 3:
                str_field_path3 = str(tempDir3)
                csv_file3 = str_field_path3+"\\"+self.sitename+"."+'G05'
                df3 = pd.read_csv(csv_file3)
                
                thetaAvail_df3 = df3.loc[df3.iloc[:,1] == '     '+ formatted_date, '     ThetaAvail']            
                theta_value = thetaAvail_df3.iloc[0]          
                needed_water3 = 1.000-theta_value
                labels = ['Soil Water', 'Soil Water Deficit']
                sizes = [theta_value, needed_water3]
                ax = self.figure4.add_subplot(111)
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title("Irrigation = 3 inch")
                self.figureCanvas4.draw() 
                
                self.yld3 = self.Yield 
                self.simOutput3 = "Yield (Irrigation 3 inch): " + str(round(self.yld3)) + " kg/ha" 
               
                self.outputDetailslabel3.setText(self.simOutput3)           
                expSysOutput(sim3, inSeasonirr_counter, self.Yield)
    
                
    def runPath(self, index, simulation_name):
        path_attr = f'path{index}'
        simulation_path = getattr(self, path_attr)
    
        print(f"Run {index} starts")
        
        layerdest_file = simulation_path + "\\" + self.sitename + ".lyr"
        grid_name = self.sitename
        createsoil_opfile = self.soilname

      
        pp = subprocess.Popen([createsoilexe, layerdest_file, "/GN", grid_name, "/SN", createsoil_opfile], cwd=simulation_path)
        while pp.poll() is None:
            time.sleep(1)

        runname = simulation_path + "\\Run" + self.sitename + ".dat"

        self.simStatus.setText("")
        self.simStatus.repaint()
        os.chdir(simulation_path)  # Change to the correct directory for the current simulation

        try:
            QCoreApplication.processEvents()
            if self.crop == "maize":
             #   print(f"Executing: {maizsimexe} {runname}")
                p = subprocess.Popen([maizsimexe, runname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                file_ext = ["g01", "G03", "G04", "G05", "G07"]
            elif self.crop == "potato":
                p = subprocess.Popen([spudsimexe, runname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                file_ext = ["g01", "G03", "G04", "G05", "G07"]
            elif self.crop == "soybean":
                p = subprocess.Popen([glycimexe, runname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                file_ext = ["g01", "G03", "G04", "G05", "G07"]
            elif self.crop == "cotton":
                p = subprocess.Popen([gossymexe, runname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                file_ext = ["g01", "G03", "G04", "G05", "G07"]
            else:  # fallow
                p = subprocess.Popen([maizsimexe, runname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
                file_ext = ["G03", "G05", "G07"]

            for line in iter(p.stdout.readline, b''):
                print("line=", line)
                if b'Progress' in line:
                    prog = re.findall(r"[-+]?\d*\.\d+|\d+", line.decode())
                    self.simStatus.setText("<b>Simulation Progress</b>: " + prog[0] + "%")
                    self.simStatus.repaint()

            out, err = p.communicate()
            if p.returncode == 0:
                print("twosoil stage completed. %s", str(out))
            else:
                print("twosoil stage failed. Error =. %s", str(err))
        except OSError as e:
            sys.exit("failed to execute twodsoil program, %s" % str(e))

        print(f"Run {index} ends")
        self.simStatus.repaint()

               
    def WriteIni(self,field_name,field_path,lstartyear,lendyear,waterStressFlag,nitroStressFlag, inSeairr, linSeaDate):
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

        strVar = pd.Series(self.result['treatment'])
        strVar_split = strVar.str.split('/')
        cropname = strVar_split.str[0]
   
        experiment =  strVar_split.str[1]
        treatmentname = strVar_split.str[-1]
        lcropname = cropname.iloc[0]
        lexperiment = experiment.iloc[0]
        ltreatmentname = treatmentname.iloc[0]
        self.treatment = ltreatmentname
        self.experiment = lexperiment 
        self.crop = lcropname 
        
        

        #find cropid
        #use crop to find exid in eperiment table
        #use exid and treatmentname to find tid from treatment table
        # use tid(o_t_exid) to find all the operations
        operationList = []
        exid = read_experimentDB_id(lcropname,lexperiment)
        tid = read_treatmentDB_id(exid,ltreatmentname)
        operationList = read_operationsDB_id(tid) #gets all the operations

       # inSeasonirr = ReadIrrigation(str(self.linSeaDate))
       # inSeasonirr = [1, 2, 3] 
        inSeaDate_obj = datetime.strptime(linSeaDate, '%Y-%m-%d')
        formatted_linSeaDate = inSeaDate_obj.strftime('%m/%d/%Y') 

        formatted_inSeasonirr = int(inSeairr)*25.4
        self.irrExpSys = (formatted_inSeasonirr, 'Irrigation', formatted_linSeaDate)
        self.irrigationExpSys = (formatted_linSeaDate, formatted_inSeasonirr)


        operationList.append(self.irrExpSys)

       # operationList.sort() We need sort on Irrigation first
        truncated_operationList = [x for x in operationList if 'Irrigation' not in x]


        irrigation_operationList = [x for x in operationList if 'Irrigation' in x]


            

        sorted_irrigation_operationList = sorted(irrigation_operationList, key=lambda x: datetime.strptime(x[2], '%m/%d/%Y'))

        truncated_operationList.extend(sorted_irrigation_operationList )
        extended_operationList = truncated_operationList

 

        for ii,jj in enumerate(extended_operationList):
            if jj[1] == 'Simulation Start':
                # Placeholder so model doesn't use the date
                if lcropname == "fallow":
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
                self.harvestdate = jj[2]

            if jj[1] == 'Simulation End':   
                EndDate=jj[2] #month/day/year
            #    print("EndDate: ", EndDate)
                # End date should be greater than sowing date
                if lcropname == "fallow":
                    EndDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=365)).strftime('%m/%d/%Y')
            
        site = self.result['site'] 
        lsite = site.iloc[0]
        soil = self.result['soil']  
        lsoil = soil.iloc[0]
     #   print("Site for ini file:", lsite)
        tsite_tuple = extract_sitedetails(lsite)   
        #maximum profile depth     
        maxSoilDepth=read_soillongDB_maxdepth(lsoil)
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
            if lcropname == "maize" or lcropname == "fallow":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Planting          Emergence           End           TimeStep(m)    sowing and end dates for fallow are setin the future so the soil model will not call a crop\n"
                fout<<"'%-10s'  '%-10s'  %d" %(SowingDate,EndDate,60)<<"\n"
                rootWeightPerSlab = 0
            elif lcropname == "potato":
                fout<<"Seed  Depth  Length  Bigleaf"<<"\n"
                fout<<"%-14.6f%-14.6f%-14.6f%d" %(seedpieceMass,depth,length,1)<<"\n"
                fout<<"Planting          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Stresses (Nitrogen, Water stress: 1-nonlimiting, 2-limiting): Simulation Type (1-meteorological, 2-physiological)"<<"\n"
                fout<<"Nstressoff  Wstressoff  Water-stress-simulation-method"<<"\n"
                fout<<"%d    %d    %d" %(int(waterStressFlag),int(nitroStressFlag),0)<<"\n"
                rootWeightPerSlab = seedpieceMass * pop  * 0.25 * RowSP / 100 * 0.5 * 0.01
            elif lcropname == "soybean":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Sowing          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                rootWeightPerSlab = 0.0275
            elif lcropname == "cotton":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  %d" %(EmergenceDate, HarvestDate,60)<<"\n"
                rootWeightPerSlab = 0.0275
            fout<<"output soils data (g03, g04, g05 and g06 files) 1 if true"<<"\n"
            fout<<"no soil files        output soil files"<<"\n"
            fout<<"    0                     1  "<<"\n"
               
        fh.close()

        return RowSP, rootWeightPerSlab, cultivar, self.irrigationExpSys


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
                   hNew  Tmpr     CO2     O2    N2O   Sand     Silt    Clay     BD     TH33     TH1500  thr ths tha th  Alfa    n   Ks  Kk  thk\n"
            fout<<" cm         w/m       Frac      ppm    ppm    ppm    ppm   ppm    ppm   ppm     ppm   cm     0C     ppm   ppm  ----  fraction---     \
                   g/cm3    cm3/cm3   cm3/cm3\n"
     #       print("soilname=",soilname)
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
   
    
    def CompareSimulation(self, id): 
        yieldlist = []        
        yieldlist = [self.yld0, self.yld1, self.yld2, self.yld3]     
       
        xlist = [0, 1, 2, 3] 
        ylist = [y for y in yieldlist] 
        
        bargraph = pg.BarGraphItem(x = xlist, height = ylist, width = 0.6, brushes = ['m', 'y', 'g', 'c'])        
        self.plot.addItem(bargraph)
        
        self.plot.getAxis('bottom').setLabel('Irrigation (inch)')
        self.plot.getAxis('left').setLabel('Yield (kg/ha)')
        self.plot.getAxis('left').setRange(min=0)
   
    
    def output_yield(self,id):

        exid = read_experimentDB_id(self.crop,self.experimentname)
        tid = read_treatmentDB_id(exid,self.treatmentname)
        plantDensity = getPlantDensity(tid)
        
        operationList = read_operationsDB_id(tid)
        
        for ii,jj in enumerate(operationList):
            if jj[1] == 'Harvest':                            
                HarvestDate=jj[2] 
                self.harvestdate = jj[2]

        if self.crop == "potato":
            agroDataTuple = getPotatoAgronomicData(id, self.harvestdate)
            self.Yield = agroDataTuple[0]*plantDensity*10	
        elif self.crop == "soybean":
            agroDataTuple = getSoybeanAgronomicData(id, self.harvestdate)
            self.Yield = agroDataTuple[0]*plantDensity*10		
        elif self.crop == "maize":
            MaturityDate = getMaizeDateByDev(id,"Matured")
            if(MaturityDate != "N/A"):
                agroDataTuple = getMaizeAgronomicData(id, MaturityDate)
            else:
                agroDataTuple = getMaizeAgronomicData(id, self.harvestdate)	
            self.Yield = agroDataTuple[0]*plantDensity*10		
        elif self.crop == "cotton":
            yieldDataTuple = getCottonAgronomicData(id)	
            self.Yield = yieldDataTuple[1]
        else:
            pass
        return self.Yield
    
