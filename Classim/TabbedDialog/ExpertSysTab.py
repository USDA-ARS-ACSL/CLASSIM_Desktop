from ast import Lambda
import subprocess
import time
import os
os.environ['PYDEV_WARN_SLOW_RESOLVE_TIMEOUT'] = '1.0'
import pandas as pd
import json
import sys
import re
import datetime
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout,  QVBoxLayout, QPushButton, QTabWidget, QGridLayout,\
                            QSpacerItem, QSizePolicy, QHeaderView,  QCheckBox, QGridLayout, QTextEdit  
                         

from PyQt5.QtCore import QFile, QTextStream, pyqtSignal, QCoreApplication, QThread, QTimer
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
import matplotlib.dates as mdates
from CustomTool.getClassimDir import *
import pyqtgraph as pg
from helper.threadWrapperES import start_simulationES, on_simulation_progressES, on_simulation_finishedES
from helper.threadWrapper import start_simulation, on_simulation_progress, on_simulation_finished
# Add these imports near the top of the file (update the existing import lines)
from PyQt5.QtWidgets import QCalendarWidget, QDialog, QDialogButtonBox, QTableWidgetItem
from PyQt5.QtCore import QDate
import subprocess

from matplotlib.lines import Line2D
import matplotlib.dates as mdates
import matplotlib.ticker as mticker



classimDir = getClassimDir()
runDir = os.path.join(classimDir,'run')
storeDir = os.path.join(runDir,'store')
tempDir0 = os.path.join(runDir, 'temp0')
tempDir1 = os.path.join(runDir, 'temp1')
tempDir2 = os.path.join(runDir, 'temp2')
tempDir3 = os.path.join(runDir, 'temp3')
tempDirN = os.path.join(runDir, 'tempN')  # <-- for Full Season
tempDirISN = os.path.join(runDir, 'tempISN') # <-- For In-Season

# ensure temp folders exist and clean any old files
for td in (tempDirN, tempDirISN):
    if not os.path.exists(td):
        try:
            os.makedirs(td)
        except Exception:
            pass
    temp_folder = QDir(td)
    for file_info in temp_folder.entryInfoList():
        if file_info.isFile():
            temp_folder.remove(file_info.fileName())


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

class SignalEmitterES(QObject):
    
    def __init__(self):       
        super().__init__()
        self.subscribers = []

    def connect(self, callback):
        self.subscribers.append(callback)

    def emit(self, exe, runname, result, sim_status, simulation_id, widget_instanceES, controller):
        for callback in self.subscribers:
            callback(exe, runname, result, sim_status, simulation_id, widget_instanceES, controller)
 
class ControllerES:
    """
    Acts as the simulation launcher. It uses the SignalEmitter to send
    the appropriate crop model execution command to the subscriber.
    """
    def __init__(self):
        self.emitter = SignalEmitterES()
     #   self.emitter.connect(start_simulationES)
        # Connect to the start_simulationES, passing self (the controller instance)
        self.emitter.connect(lambda *args: start_simulationES(*args))

        self.completedSimCountES = 0
        self.totalSimCountES = 0
        self.active_simulations = {} # To keep track of running simulations by ID


    def launch(self, crop_choice, runname, result, sim_status, simulation_id, parent_widget):
        exe_map = {
            "maize": maizsimexe,
            "potato": spudsimexe,
            "soybean": glycimexe,
            "cotton": gossymexe,
            "fallow": maizsimexe
        }

        exe = exe_map.get(crop_choice.lower())
        if exe:
            self.emitter.emit(exe, runname, result, sim_status, simulation_id, parent_widget, self)
        else:
            print(f"Unsupported crop: {crop_choice}")

    def increment_completed_count(self):
        self.completedSimCountES += 1
        if self.completedSimCountES == self.totalSimCountES:
            self.onAllSimulationsComplete()

    def onAllSimulationsComplete(self):
        print("All simulations are complete.")
        # Perform any final actions after all simulations are done
        # e.g., enable UI elements, display final results
        # You might want to emit a signal from here as well to notify the UI
        if hasattr(self, 'widget_instance') and self.widget_instance:
            self.widget_instance.allSimsFinished.emit()

class SignalEmitter(QObject):
    
    exsystemsig = pyqtSignal(int)
    seasonalsig = pyqtSignal(int)
    
    def __init__(self):
    #    signal_instance = SignalEmitter()

        self.subscribers = []
        super().__init__()

    def connect(self, callback):
        self.subscribers.append(callback)

    def emit(self, exe, runname, result, sim_status, simulation_id, widget_instance, controller):
        for callback in self.subscribers:
            callback(exe, runname, result, sim_status, simulation_id, widget_instance, controller)
 
class Controller:
    """
    Acts as the simulation launcher. It uses the SignalEmitter to send
    the appropriate crop model execution command to the subscriber.
    """
    def __init__(self):
        self.emitter = SignalEmitter()
        self.emitter.connect(start_simulation)

    def launch(self, crop_choice, runname, result, sim_status, simulation_id, parent_widget):
        exe_map = {
            "maize": maizsimexe,
            "potato": spudsimexe,
            "soybean": glycimexe,
            "cotton": gossymexe,
            "fallow": maizsimexe
        }

        exe = exe_map.get(crop_choice.lower())
        if exe:
            self.emitter.emit(exe, runname, result, sim_status, simulation_id, parent_widget,self)
        else:
            print(f"Unsupported crop: {crop_choice}")

    def NFullSimulationComplete(self):
        print("All simulations are complete.")
        # Perform any final actions after all simulations are done
        # e.g., enable UI elements, display final results
        # You might want to emit a signal from here as well to notify the UI
        if hasattr(self, 'widget_instance') and self.widget_instance:
            self.widget_instance.NFullSimFinished.emit()

signal_instance = SignalEmitter() 

class ExpertSys_Widget(QWidget):
    # Add a signal
#    expertsyssig = pyqtSignal(int)    
    changedValue = pyqtSignal(int)
    expertsyssigN = pyqtSignal(int) 

    allSimsFinished = pyqtSignal()
    NFullSimFinished = pyqtSignal()
    
    def __init__(self):
        super(ExpertSys_Widget,self).__init__()
        self.simWorker = None
        self.simWorkerThread = None
        self.activeSimWorkers = []
        self.activeSimThreads = []
      #  create_simulation_table()

       # "Running wheel" state
      # self._busy_timer = QTimer(self)
     #  self._busy_timer.timeout.connect(self._update_busy_indicator)
      # self._busy_tick = 0

        self.controller = ControllerES() # Create one controller instance for the widget
        self.controller.widget_instance = self # Let controller know about its widget

        self.init_ui()
        self.make_connection()
       #self.simStatus = QLabel("Ready to run simulations.") # Assuming you have a QLabel for status
        #elf.simStatus.setWordWrap(True)

        


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
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
    #    self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink="<a href=\"https://youtu.be/DXj5BOi09IU\">Click here \
                to watch the Expert System Tab Video Tutorial</a><br>"
        self.expSysVidlabel=QLabel()
        self.expSysVidlabel.setOpenExternalLinks(True)
        self.expSysVidlabel.setText(urlLink)       
        
        # Adding the tabs
        self.display = QTabWidget()
        self.display.clear()
        self.irrTab = QWidget()
        self.nitroTab = QWidget()
        self.display.addTab(self.irrTab, "Irrigation")
        self.display.addTab(self.nitroTab, "Nitrogen")
        
        # irrigation tab codes
        self.soilwater_df = None
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

        # make plots vertically smaller
           
        
        self.irrOptionlabel = QLabel("Run Simulation with Irrigation")
        self.irrOption = read_irrOption()      
        self.runButton = QPushButton()

        # create simStatus here
        self.simStatus = QLabel("")
        self.simStatus.setWordWrap(True)
        self.runButton.setText("Run")       
        self.buttonreset = QPushButton("Reset")       
        self.inSeasonirr = [0, 1, 2, 3]
        self.runButton.clicked.connect(lambda: self.RunSimulationIrr(self.inSeasonirr))
        self.buttonreset.clicked.connect(self.reset)   
        self.comButtonlabel = QLabel("Yield Comparison")
        self.comStatus = QLabel("")
        self.comStatus.setWordWrap(True)
        self.comButton = QPushButton()
        self.comButton.setText("Compare")
        self.comButton.clicked.connect(lambda: self.CompareSimulation(self.newsimulationID))

        self.outputlabel = QLabel("Simulation Details")   
        self.genInfoBoxSumLabel1 = QLabel()
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
        self.vl1.addWidget(self.helpcheckbox)
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vl1.setContentsMargins(0,0,0,0)
        self.vl1.addStretch(1)        

        self.output = QVBoxLayout()
        self.output.addWidget(self.outputlabel)
        self.output.setAlignment(self.outputlabel, Qt.AlignTop)
        self.output.addWidget( self.genInfoBoxSumLabel1)
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
        self.vl2.addLayout(self.soilwatergrid, 1,0)
        self.vl2.addLayout(self.vl3, 1,1)
    
        self.hl2 = QHBoxLayout() 
        self.hl2.addWidget(self.irrOptionlabel)
        self.hl2.addWidget(self.runButton)
        self.hl2.addWidget(self.buttonreset)
        self.hl2.addWidget(self.simStatus)   
        
        self.hl4 = QHBoxLayout() 
        self.hl4.addWidget(self.comButtonlabel)
        self.hl4.addWidget(self.comButton)
        self.hl4.addWidget(self.comStatus)
        
        self.vl2.addLayout(self.hl2, 2,0)
        self.vl2.addLayout(self.hl4, 4,0)
        self.irrTab.setLayout(self.vl2)  
        self.mainlayout1.addLayout(self.vl1)  
        self.mainlayout1.addWidget(self.display)
        self.setLayout(self.mainlayout1)
        
        # Nitrogen tab codes
        self.genInfoBoxSumLabel2 = QLabel()
            
        self.maxNlabel = QLabel("Max Nitrogen Limit")
        self.maxNlabeledit = QLineEdit()
        
        self.maxNlabeladd = QPushButton("Apply")
        self.maxNlabeladd.clicked.connect(self.maxAllowedN)
        
        self.numAppllabel = QLabel("Nitrogen Applied")
        self.numAppllabeledit = QLineEdit()

        # Set the width for the edit boxes
        self.maxNlabeledit.setFixedWidth(150)  # Width of 150 pixels
        self.numAppllabeledit.setFixedWidth(150)  # Width of 150 pixels
        
        self.output2 = QVBoxLayout()
        self.output2.addWidget(self.outputlabel)
        self.output2.setAlignment(self.outputlabel, Qt.AlignTop)
        self.output2.addWidget( self.genInfoBoxSumLabel2)
        self.output2.addStretch()
        
        self.nitroTab.fig1 = plt.figure(figsize=(5,5))
        self.nitroTab.canvas1 = FigureCanvas(self.nitroTab.fig1)   
        self.nitroTab.fig2 = plt.figure(figsize=(5,5))
        self.nitroTab.canvas2 = FigureCanvas(self.nitroTab.fig2)         
        self.nitroTab.fig3 = plt.figure(figsize=(5,5))
        self.nitroTab.canvas3 = FigureCanvas(self.nitroTab.fig3) 

       # for c in (self.nitroTab.canvas1,
      #          self.nitroTab.canvas1,
      #          self.nitroTab.canvas3):
        #    c.setMaximumHeight(220)  
      
        
        self.nitroPlotsgrid = QHBoxLayout()
        self.nitroPlotsgrid.addWidget( self.nitroTab.canvas1) 
        self.nitroPlotsgrid.addWidget( self.nitroTab.canvas2) 
        self.nitroPlotsgrid.addWidget( self.nitroTab.canvas3) 
        
        
        self.vl3n = QVBoxLayout()
        self.vl3n.addLayout(self.output2)
        self.vl3n.addLayout(self.nitroPlotsgrid)
       
      ##  self.hbox.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))  # Spacer to take remaining space

        self.runN_button = QPushButton("Run")
        self.runN_button.clicked.connect(self.on_full_season_clicked)
        self.runN_buttonlabel = QLabel("Originally Planned (For Full Season)")

        # Table widget setup
        self.table = QTableWidget()
        self.table.setColumnCount(2) 
        self.table.setHorizontalHeaderLabels(["Date", "Amount"])
        self.table.cellDoubleClicked.connect(self.open_calendar_for_date)

        # Button setup
        self.button_layout = QHBoxLayout()
        self.add_label = QLabel("Add In-Season N")
        self.button_layout.addWidget(self.add_label)

        self.add_button = QPushButton("Add Row")
        self.add_button.clicked.connect(self.add_row)
        self.button_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("Update")
        self.button_layout.addWidget(self.update_button)
        self.update_button.clicked.connect(self.update_n_applied)

        self.delete_button = QPushButton("Delete")
        self.button_layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.delete_selected_applied_n)

        self.runNInSeason_button = QPushButton("Modified Run")
        self.button_layout.addWidget(self.runNInSeason_button)
        self.runNInSeason_button.clicked.connect(self.run_inseason_after_update)

        self.outputDetailslabelN = QLabel()
        self.outputDetailslabelN_mod = QLabel()
        

        # --- DISABLE NITROGEN CONTROLS WHILE RUNNING ---
        # Always disable before starting a run; they will be re-enabled on NFullSimFinished.
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.runNInSeason_button.setEnabled(False)
  
       
              
        self.mainlayout2 = QGridLayout()

        self.mainlayout2.addLayout(self.vl3n, 0, 0, 5, 1)

        self.mainlayout2.addWidget(self.maxNlabel, 0, 1)
        self.mainlayout2.addWidget(self.maxNlabeledit, 0,2)
        self.mainlayout2.addWidget(self.maxNlabeladd, 0,3)

        self.mainlayout2.addWidget(self.numAppllabel, 1,1)
        self.mainlayout2.addWidget(self.numAppllabeledit, 1, 2)
        
        self.mainlayout2.addWidget(self.runN_buttonlabel,2,1)
        self.mainlayout2.addWidget(self.runN_button,2,2)

        self.mainlayout2.addLayout(self.button_layout, 3,1,1,3)

        self.mainlayout2.addWidget(self.table, 4,1,1,2)
        
        self.mainlayout2.addWidget(self.outputDetailslabelN, 5, 1,1,2)
        self.mainlayout2.addWidget(self.outputDetailslabelN_mod, 6, 1,1,2)
        self.nitroTab.setLayout(self.mainlayout2)

        # tune row stretch so the table uses more height than the plots
       # self.mainlayout2.setRowStretch(0, 0)  # header row
      #  self.mainlayout2.setRowStretch(1, 0)
      #  self.mainlayout2.setRowStretch(2, 0)
      #  self.mainlayout2.setRowStretch(3, 2)  # table row gets more space
      #  self.mainlayout2.setRowStretch(4, 0)
      #  self.mainlayout2.setRowStretch(5, 0)
    
    def reset(self):
        plt.ion()    
        self.figureCanvas1.figure.clf()
        self.figureCanvas2.figure.clf()
        self.figureCanvas3.figure.clf()
        self.figureCanvas4.figure.clf()
        # reset text labels (do NOT recreate QLabel instances)
        self.outputlabel.setText("")
        self.genInfoBoxSumLabel1.setText("")
        self.outputIrriglabel.setText("")
        self.outputDetailslabel0.setText("")
        self.outputDetailslabel1.setText("")
        self.outputDetailslabel2.setText("")
        self.outputDetailslabel3.setText("")
        self.outputIrriglabel.setText("")

    def reset_nitro(self):
        """
        Reset only the Nitrogen sub-tab UI:
         - clear nitro figures and canvases
         - clear nitro input boxes and summary label
         - clear the nitro table and insert a single blank row (empty Date and Amount)
        """
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtCore import QDate

        # Clear nitro figures
        try:
            for fig_attr, canvas_attr in (('fig1', 'canvas1'), ('fig2', 'canvas2'), ('fig3', 'canvas3')):
                fig = getattr(self.nitroTab, fig_attr, None)
                canvas = getattr(self.nitroTab, canvas_attr, None)
                if fig is not None:
                    try:
                        fig.clf()
                    except Exception:
                        pass
                if canvas is not None:
                    try:
                        canvas.draw()
                    except Exception:
                        pass
        except Exception:
            pass

        # Clear nitro input fields and summary
        try:
            if hasattr(self, 'maxNlabeledit'):
                self.maxNlabeledit.clear()
            if hasattr(self, 'numAppllabeledit'):
                self.numAppllabeledit.clear()
            if hasattr(self, 'genInfoBoxSumLabel2'):
                self.genInfoBoxSumLabel2.setText("")
        except Exception:
            pass

        # Clear nitrogen table and add single BLANK row (no default date)
        try:
            # remove all rows
            while self.table.rowCount() > 0:
                self.table.removeRow(0)
            # clear any selection/focus so the UI looks reset
            try:
                self.table.clearSelection()
                self.table.setCurrentCell(-1, -1)
            except Exception:
                pass
        except Exception:
            pass
        self.outputDetailslabelN.setText("")
        self.outputDetailslabelN_mod.setText("")
 
    def make_connection(self):
     #   exsys_object.exsystemsig.connect(self.populate)
       # exsys_object.exsystemsigN.connect(self.populate)
        from TabbedDialog.SeasonalTab import signal_instance
        signal_instance.exsystemsig.connect(self.populate) 
        self.allSimsFinished.connect(self.drawWater)
        self.NFullSimFinished.connect(self.on_click_nitroTab)

    # Both Irrigation and Nitrogen Tabs
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

    #    self.result1 = [self.sitename, self.crop, fieldpath, expSystem_flag]
        

        self.soilwater_df = []
        self.soilwater_df= readSoilWater(self.prevsimulationID, self.crop)        
        self.last_soilwater = self.soilwater_df.iloc[-1:]       
        self.soilwater_content = float(self.last_soilwater['ThetaAvail'].values[0] )
        self.needed_water = float(1.000-self.soilwater_content)  
        
         # Ensure sizes sum to 1
        total = self.soilwater_content + self.needed_water
        if not np.isclose(total, 1.0):
            print("Sizes do not sum to 1")
            return       
        labels = ['Soil Water', 'Soil Water Deficit']
        sizes = [round(self.soilwater_content, 3), round(self.needed_water, 3)]
        # Check if sizes contain valid data
        if sizes and all(isinstance(size, (int, float)) for size in sizes):
            ax = self.figure1.add_subplot(111)
            #ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90
            )
            ax.set_title("No Irrigation")
            ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1.05, 0.5), borderaxespad=0.)
            self.figureCanvas1.draw()
            # Ensure the plot is displayed
        else:
            print("Invalid data for pie chart")
    
        
        inseasonDate = self.last_soilwater['Date_Time']
        inseasonDate = inseasonDate.values[0]
        input_datetime = datetime.strptime(inseasonDate, '%Y-%m-%d %H:%M:%S')   
        input_datetime += timedelta(1)
        formatted_inseasonDate = input_datetime.strftime('%m/%d/%Y')

        self.simSummaryGen = "<br>" + " " + "<b>Site: </b>" + self.sitename + "  " 
        self.simSummaryGen += "<b>Soil: </b>" + self.soilname + "  " 
        self.simSummaryGen += "<b>Weather: </b>" + self.weather  #self.stationtypename 
        self.simSummaryGen += "<br>" + " " + "<b>Crop: </b>" + self.crop + "  " 
        self.simSummaryGen += "<b>Experiment: </b>" + self.experimentname + "  " 
        self.simSummaryGen += "<b>Treatment: </b>" + self.treatmentname
        self.simSummaryGen += "<br><b>In-Season Date:  </b>" + formatted_inseasonDate
        self.genInfoBoxSumLabel1.setText(self.simSummaryGen)
        self.genInfoBoxSumLabel2.setText(self.simSummaryGen)
        self.on_click_nitroTab(use_previous=True)
        
    
     #Return InSeadata
    def selInSeadate(self,):
        conn, c = openDB('crop.db')
        if c:
            c1 = c.execute("SELECT inSeaDate FROM inSeaIrri ORDER BY ID DESC LIMIT 1")
            c1_row = c1.fetchone()
            conn.close()
        linSeaDate = c1_row[0]
        return linSeaDate

    # Irrigation Schedule
    def RunSimulationIrr(self,inSeasonirr):   
        # show busy indicator
     #  self._start_busy("Irrigation simulation running")
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

        #Check the .man file in the self.prevsimulationID for in-season date irrigation application
        tempfolder = os.path.join(runDir, str(self.prevsimulationID))
        irr_file = os.path.join(tempfolder, self.sitename + '.irr')
        try:
            in_season = self.selInSeadate()               # 'YYYY-MM-DD'
            in_season_dt = datetime.strptime(in_season, "%Y-%m-%d")
            in_season_str = in_season_dt.strftime("%m/%d/%Y")  # 'MM/DD/YYYY'

            any_match = False
            with open(irr_file, 'r') as f:
                for line in f:
                    # look for a date in quotes, e.g. '07/05/2014'
                    m = re.search(r"'(\d{2}/\d{2}/\d{4})'", line)
                    if not m:
                        continue
                    date_str = m.group(1)  # MM/DD/YYYY
                    if date_str == in_season_str:
                        any_match = True
                        break

            if any_match:
              # print("yes: in‑season date", in_season_str, "found in", irr_file)
                QMessageBox.information(self, "Success", f"Planned Irrigation on this day has been removed.")
           #else:
           #    print("no: in‑season date", in_season_str, "not found in", irr_file)
        except Exception as e:
            print("RunSimulationIrr: could not check .irr file for in‑season date:", e)

        
        self.newsimulationID = self.prevsimulationID + 1        
        self.prepareandexecuteExpSys(self.newsimulationID, self.result, inSeasonirr) 

       
    
   
     # For Irrigation Tab   
    def prepareandexecuteExpSys(self,simulation_name,result, inSeasonirr):
        """
        this will create input files, and execute both exe's
        """

        self.simulation_names = [simulation_name + i for i in range(4)]
        tempDirs = [tempDir0, tempDir1, tempDir2, tempDir3]
        field_paths = tempDirs
        str_field_paths = [str(tempDir) for tempDir in tempDirs]

        # Assign individual variables if needed
        sim0, sim1, sim2, sim3 = self.simulation_names
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
        src_file= storeDir + '\\Water.DAT'
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

        self.inSeasonirrs = [inSeasonirr[0], inSeasonirr[1], inSeasonirr[2], inSeasonirr[3]]
        rowSpacings = []
        rootWeightPerSlabs = []
        cultivars = []
        irrs = []

        for str_field_path, inSeasonirr in zip(str_field_paths, self.inSeasonirrs):
            rowSpacing, rootWeightPerSlab, cultivar, irr = self.WriteIni(self.sitename, str_field_path, str(waterStressFlag), str(nitroStressFlag), str(inSeasonirr), self.linSeaDate)
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
        hourlyFlag = 0
        WriteTimeFileData(self.treatmentname, self.experimentname, self.crop, self.stationtypename, hourlyFlag, self.sitename, str_field_path0, hourly_flag, 0)
        src_file = field_paths[0] + '\\' + self.sitename + '.tim'
        dest_files = [f'{field_paths[i]}\\{self.sitename}.tim' for i in range(1, 4)]

        for dest_file in dest_files:
            copyFile(src_file, dest_file)

      
        o_t_exid = getTreatmentID(self.treatmentname,self.experimentname,self.crop)
        irrType = "Sprinkler"       
        surfResType =[]       
        for str_field_path, rowSpacing, rootWeightPerSlab, in zip(str_field_paths, rowSpacings, rootWeightPerSlabs):
            WriteNitData(self.soilname, self.sitename, str_field_path, rowSpacing)
            self.WriteLayerGas(self.soilname,self.sitename,str_field_path,rowSpacing,rootWeightPerSlab)
            surfResType_var=WriteManagement(self.crop,self.experimentname,self.treatmentname,self.sitename,str_field_path,rowSpacing, up_to_date=None)  
            surfResType.append(surfResType_var)
            WriteMulchGeo(str_field_path,surfResType_var)

            

        for sim, irr, str_field_path in zip(self.simulation_names, irrs, str_field_paths):
            WriteIrrigationExpSys(self.sitename,str_field_path,irrType, sim, o_t_exid, irr)
            

        

        for str_field_path in zip(str_field_paths):
            WriteRunFile(self.crop,self.soilname,self.sitename,cultivar,str_field_path[0],self.stationtypename)          
           
        self.path0 = str_field_path0
        self.path1 = str_field_path1
        self.path2 = str_field_path2
        self.path3 = str_field_path3
        
        self.simQueue = list(zip(self.simulation_names, self.inSeasonirrs))
       # self.simIndex = 0  # Optional: track current position

        self.controller.totalSimCountES = len(self.simQueue) # Set total count
        self.controller.completedSimCountES = 0 # Reset completed count
        print(f"Total simulations to run: {self.controller.totalSimCountES}")

        # Clear existing workers before starting a new batch
        self.activeSimWorkers = []

        for index, (sim_id, irr_value) in enumerate(self.simQueue):
          #  print(f"Preparing simulation {index}: sim_id = {sim_id}, irr_value = {irr_value}")
            # Ensure sim_id is a list if expected by SimulationWorkerES
            current_simulation_id = [sim_id] if isinstance(sim_id, int) else sim_id
            self.runPath(index, current_simulation_id)
        
             
        
    def drawWater(self):
        print("All simulations finished. Proceeding to draw water.")
        exid = read_experimentDB_id(self.crop, self.experiment)
        tid = read_treatmentDB_id(exid, self.treatment)
        plantDensity = getPlantDensity(tid)
    
        for _, (inSeasonirr_counter, _) in enumerate(zip(self.inSeasonirrs, self.simulation_names)):        
            filename = runDir + "\\" + "temp" + str(inSeasonirr_counter) + "\\" + self.sitename + ".g01"
         #   print("Runname: ", filename)
    
            if self.crop == "potato":
                potato_df =   pd.read_csv(filename, usecols = ['tuberDM'])
                last_ptato_df = potato_df.tail(1)      
                agroDataTuple = last_ptato_df['tuberDM']
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                
            elif self.crop == "soybean":
                soy_df =   pd.read_csv(filename, usecols = ['    seedDM'])
                last_soy_df = soy_df.tail(1) 
                agroDataTuple = last_soy_df[ '    seedDM']
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                       
                
            elif self.crop == "maize":                        
                corn_df = pd.read_csv(filename) #, usecols = ['earDM']) #, 'date', 'Note     '])
               # last_corn_df = corn_df.tail(1)    
                last_corn = corn_df['earDM'].tail(1) 
                agroDataTuple = last_corn * 0.86   
                self.Yield = agroDataTuple.iloc[0]*plantDensity*10
            #    print(last_corn,agroDataTuple)
                
            elif self.crop == "cotton":
                cotton_df =   pd.read_csv(filename)  
                last_cotton_df = cotton_df.tail(1) 
                agroDataTuple = last_cotton_df['       Yield']
                self.Yield = agroDataTuple.iloc[0]
                       
            else:
                pass	
      
           
       #     print(formatted_date)
            # use in-season date itself
          # date = pd.to_datetime(self.linSeaDate, format="%Y-%m-%d")
         #  formatted_date = date.strftime("%m/%d/%Y")
            date_object = datetime.strptime(self.linSeaDate, "%Y-%m-%d")
            new_date = date_object+ timedelta(days=1)
            formatted_date = new_date.strftime("%m/%d/%Y") 

            if inSeasonirr_counter == 0:   
                self.yld0 = self.Yield
                self.simOutput0 = "Yield (Irrigation 0 inch): " + str(round(self.yld0))  + " kg/ha"   
                self.outputDetailslabel0.setText(self.simOutput0)           
                expSysOutput(self.simulation_names[0], inSeasonirr_counter, self.Yield)
            
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
                expSysOutput(self.simulation_names[1], inSeasonirr_counter, self.Yield)
                 
            elif inSeasonirr_counter == 2:
                str_field_path2 = str(tempDir2)
                csv_file2 = str_field_path2 + "\\" + self.sitename + "." + 'G05'
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
                expSysOutput(self.simulation_names[2], inSeasonirr_counter, self.Yield)
            
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
                expSysOutput(self.simulation_names[3], inSeasonirr_counter, self.Yield)
       #    self._stop_busy("Irrigation simulation finished")
    
     # For Irrigation Tab            
    
     
    def runPath(self, index, simulation_name):
        path_attr = f'path{index}'
        if not hasattr(self, path_attr):
            print(f"Error: {path_attr} not found for simulation index {index}. Skipping.")
            return

        simulation_path = getattr(self, path_attr)
          
      #  print(f"Run {index} starts")
        result = [self.sitename, self.crop, simulation_path, True]
        
        layerdest_file = simulation_path + "\\" + self.sitename + ".lyr"
        createsoil_opfile = self.soilname
        grid_name = self.sitename

      
        try:
            print(f"Running createsoilexe in {simulation_path}...")
            # Use a list for command, and set cwd explicitly
            pp = subprocess.Popen([createsoilexe, layerdest_file, "/GN", grid_name, "/SN", createsoil_opfile],
                                  cwd=simulation_path,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True)
            stdout, stderr = pp.communicate() # Wait for it to finish and get output
            if pp.returncode != 0:
                print(f"createsoilexe failed with code {pp.returncode}. STDOUT: {stdout} STDERR: {stderr}")
                self.simStatus.setText(f"<b>Error creating soil file for sim {simulation_name}:</b> {stderr}")
                return # Stop if soil creation fails
            else:
                print(f"createsoilexe completed for {simulation_path}. Output: {stdout}")

        except Exception as e:
            print(f"Exception running createsoilexe: {e}")
            self.simStatus.setText(f"<b>Error running soil creator:</b> {e}")
            return
        
      #  unique_suffix = str(simulation_name[0])
      #  sitename = f"BEOU_{unique_suffix}"
      #  runname = os.path.join(simulation_path, f"Run{self.sitename}.dat")
        



        runname = os.path.join(simulation_path, f"Run{self.sitename}.dat")

        self.simStatus.setText("")
        self.simStatus.repaint()

        # Pass the SINGLE controller instance
        self.controller.launch(self.crop, runname, result, self.simStatus, simulation_name, self)
        print(f"controller.launch() called for simulation {index}")


        

     # For Irrigation Tab          
    def WriteIni(self,field_name,field_path, waterStressFlag,nitroStressFlag, inSeairr, linSeaDate):
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

        inSeaDate_obj = datetime.strptime(linSeaDate, '%Y-%m-%d')
        formatted_linSeaDate = inSeaDate_obj.strftime('%m/%d/%Y') 

        formatted_inSeasonirr = int(inSeairr)*2.54
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
                # End date should be greater than sowing date
                if lcropname == "fallow":
                    EndDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=365)).strftime('%m/%d/%Y')
            
        site = self.result['site'] 
        lsite = site.iloc[0]
        soil = self.result['soil']  
        lsoil = soil.iloc[0]
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
                popSlab = RowSP/100 * 0.5 * 0.01 * pop  
                rootWeightPerSlab = seedpieceMass * 0.25 * popSlab
            elif lcropname == "soybean":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Sowing          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                popSlab = RowSP/100 * eomult * 0.01 * pop
                rootWeightPerSlab = 0.0275 * popSlab
            elif lcropname == "cotton":
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

        return RowSP, rootWeightPerSlab, cultivar, self.irrigationExpSys


     # For Irrigation Tab
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
   
     # For Irrigation Tab
    def CompareSimulation(self, id): 
        
       # yieldlist = []        
        yieldlist = [self.yld0, self.yld1, self.yld2, self.yld3]      
        xlist = [0, 1, 2, 3] 
        ylist = [y for y in yieldlist] 

        bar_width = 0.6
        # Center bars by shifting x positions left by half the bar width
        x_centered = [x - bar_width / 2 for x in xlist]
        bargraph = pg.BarGraphItem(x=x_centered, height=ylist, width=bar_width, brushes=['m', 'y', 'g', 'c'])        
        self.plot.clear()   
        self.plot.addItem(bargraph)
        self.plot.getAxis('bottom').setLabel('Irrigation (inch)')
        self.plot.getAxis('left').setLabel('Yield (kg/ha)')
       # self.plot.getAxis('left').setRange(min=0)
   
     # For Irrigation Tab
    def output_yield(self,id):

        exid = read_experimentDB_id(self.crop,self.experimentname)
        tid = read_treatmentDB_id(exid,self.treatmentname)
        plantDensity = getPlantDensity(tid)
        
        operationList = read_operationsDB_id(tid)
        
        for ii,jj in enumerate(operationList):
            if jj[1] == 'Harvest':                            
              #  HarvestDate=jj[2] 
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
    

        
    ##############################################################################
    # Nitrogen Schedule    
    
    
    '''   
    # Save the maxAllowedN value to dB
    def maxAllowedN(self):        
        allowedN = self.maxNlabeledit.text()
        lseasondate = self.selInSeadate()
        maxAllowedNdB(self.crop, self.experimentname, self.treatmentname, allowedN)
        appliedN = findNAppldB(self.crop, self.experimentname, self.treatmentname, lseasondate)
        
        self.numAppllabeledit.setText(str(appliedN))
    '''    
        # Nitrogen Tab
    
    def add_row(self):
        # Add a new row dynamically
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Insert default values: Today's date and empty amount
       # date_item = QTableWidgetItem(QDate.currentDate().toString("yyyy-MM-dd"))  # Default: current date
        linSeaDate = self.selInSeadate() 
        linSeaDate_obj = QDate.fromString(linSeaDate, "yyyy-MM-dd")     
        date_item = QTableWidgetItem(linSeaDate_obj.toString('MM/dd/yyyy'))  #lseasondate.toString("yyyy-MM-dd"))
        amount_item = QTableWidgetItem("")  # Blank amount cell
        self.table.setItem(row_position, 0, date_item)
        amount_item.setFlags(amount_item.flags() | Qt.ItemIsEditable)
        self.table.setItem(row_position, 1, amount_item) 
        self.linsea_date = linSeaDate
        return self.linsea_date

    # Add this method inside the ExpertSys_Widget class (paste near other methods like add_row/update_n_applied)
    def open_calendar_for_date(self, row, column):
        """
        Open a small dialog with a QCalendarWidget to pick a date and write it to the
        Date column (column 0) of the table. Triggered on double-click.
        """
        # Only act on the Date column
        if column != 0:
            return

        # Read existing value (if any) and try to set the calendar to it
        current_item = self.table.item(row, column)
        current_text = current_item.text() if current_item else ""

        dlg = QDialog(self)
        dlg.setWindowTitle("Select date")
        layout = QVBoxLayout(dlg)

        cal = QCalendarWidget(dlg)
        cal.setGridVisible(True)

        # Try common formats: MM/dd/yyyy, yyyy-MM-dd
        qdate = None
        if current_text:
            qdate = QDate.fromString(current_text, "MM/dd/yyyy")
            if not qdate.isValid():
                qdate = QDate.fromString(current_text, "yyyy-MM-dd")
        if qdate and qdate.isValid():
            cal.setSelectedDate(qdate)

        layout.addWidget(cal)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() == QDialog.Accepted:
            sel = cal.selectedDate()
            date_str = sel.toString("MM/dd/yyyy")
            # Ensure cell exists and is editable
            self.table.setItem(row, column, QTableWidgetItem(date_str))

    
    def maxAllowedN(self):
        allowedN = self.maxNlabeledit.text()
        lseasondate = self.selInSeadate()
        # prefer the previous simulation id if available, else the full-season newsimulationID
        sim_id = getattr(self, 'prevsimulationID', None) or getattr(self, 'newsimulationID', None)

        # Save with simulation context when available
        maxAllowedNdB(self.crop, self.experimentname, self.treatmentname, allowedN, simulation_id=sim_id)

        # Update displayed applied N
        appliedN = findNAppldB(self.crop, self.experimentname, self.treatmentname, lseasondate)
        self.numAppllabeledit.setText(str(appliedN))

        # Optional: log the stored allowedN (safely: compute ids first)
        try:
            exid = read_experimentDB_id(self.crop, self.experimentname)
            tid = read_treatmentDB_id(exid, self.treatmentname)
        except Exception:
            exid = None
            tid = None

        try:
            max_allowed = get_max_allowed_n(tid, exid, simulation_id=sim_id)
        except Exception:
            max_allowed = None
    #    print("  sim_id:", sim_id, "  max_allowed:", max_allowed)

    def on_full_season_clicked(self):
     
        # Then start the full season run
        self.RunSimulationN()
        # Enable 4 controls when Full Season Run is clicked
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.runNInSeason_button.setEnabled(True)
        
    
    def run_inseason_after_update(self):
        """
        Persist UI rows using in-season policy, set in-season run flag and start
        the in-season simulation.

        Policy:
         - Persist management up to in-season date and ES (table) for dates after in-season.
         - Mark self.use_inseason_flag so prepareandexecuteNitro will generate inputs using
           management up to in-season date.
        """
        # Suppress interactive conflict prompts for the automated in-season run
        # and ensure any prior per-date override choices are preserved for the merge step.
        self.suppress_conflict_prompts = True

        # Persist UI rows with in-season policy (validation happens there) — no prompts
        self.update_n_applied(mode='Modified', notify=False)

        # Mark upcoming run as in-season so prepareandexecuteNitro uses the in-season cutoff
        self.use_inseason_flag = True
        # record last run mode for plotting/labeling
        self.last_run_mode = 'Modified'

        # Start in-season simulation
        try:
            self.RunSimulationN()
        finally:
            # Always clear suppression flag after starting the run
            try:
                delattr = setattr  # tiny local alias to avoid lint warnings
                if hasattr(self, 'suppress_conflict_prompts'):
                    del self.suppress_conflict_prompts
            except Exception:
                pass

            # Keep override_dates until prepareandexecuteNitro consumes them; if you want them cleared
            # immediately remove the next two lines (or clear them inside prepareandexecuteNitro after use).
            # We leave them for a short time so prepareandexecuteNitro can act on them.
    '''
    def _start_busy(self, message="Simulation running"):
        """Start the text-based running indicator in simStatus."""
        self._busy_tick = 0
        self.simStatus.setText(message)
        self._busy_timer.start(300)  # update every 300 ms

    def _stop_busy(self, message="Simulation finished"):
        """Stop the running indicator and set final message."""
        if self._busy_timer.isActive():
            self._busy_timer.stop()
        self.simStatus.setText(message)

    def _update_busy_indicator(self):
        """Animate dots in simStatus to look like a running wheel."""
        self._busy_tick = (self._busy_tick + 1) % 4
        dots = "." * self._busy_tick
        base = "Simulation running"
        self.simStatus.setText(f"{base}{dots}")        
    '''
    def RunSimulationN(self):    
        # show busy indicator
    #   self._start_busy("Nitrogen simulation running")
        """
        Start N simulation. Choose temp folder depending on run mode:
          - Full Season -> tempDirN
          - In-Season  -> tempDirISN
        """
        # pick working folder for this run
        run_temp = tempDirN if getattr(self, 'last_run_mode', None) != 'Modified' else tempDirISN

        # clean only the chosen temp folder
        temp_folder = QDir(run_temp)
        for file_info in temp_folder.entryInfoList():
            if file_info.isFile():
                temp_folder.remove(file_info.fileName())      
                
        # --- DISABLE NITROGEN CONTROLS WHILE RUNNING ---
        # Always disable before starting a run; they will be re-enabled on NFullSimFinished.
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.runNInSeason_button.setEnabled(False)
      #  self.runN_button.setEnabled(False) 

        # Compute new simulation id
        self.newsimulationID = self.prevsimulationID + 1

        # If this is a plain Full Season Run (no in-season flag set) ensure DB uses management-only
        if not getattr(self, 'use_inseason_flag', False):
            # mark last run mode for plotting/labeling
            self.last_run_mode = 'Planned'
            # Persist management-only across season (full run requirement)
            # Do this quietly (no prompt) because the UI Run button triggers the run
            self.update_n_applied(mode='Planned', notify=False)

        # prepare and execute simulation; prepareandexecuteNitro reads self.use_inseason_flag
        self.prepareandexecuteNitro(self.newsimulationID, self.result)

        # Clear in-season flag after starting run to avoid affecting later runs
        if getattr(self, 'use_inseason_flag', False):
            try:
                del self.use_inseason_flag
            except Exception:
                self.use_inseason_flag = False
      #  self.last_run_mode = 'full_manage'
     #   self.update_n_applied(mode='full_manage', notify=False)
             
 
    def prepareandexecuteNitro(self, newsimulationID, result):
        """
        Prepare input files and execute N simulation.

        Use tempISN when last_run_mode == 'inseason', otherwise tempDirN.
        """
        # pick working folder based on run mode
        field_path = self.fieldpath = (tempDirISN if getattr(self, 'last_run_mode', None) == 'Modified' else tempDirN)
        # ensure folder exists
        if not os.path.exists(field_path):
            os.makedirs(field_path, exist_ok=True)

        obj_N = Seasonal_Widget()
       # lcropname = result['soil']       
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
        
     
         # Copy water.dat file from store to runDir
        src_file = storeDir + '\\Water.DAT'
        dest_file = field_path+'\\WatMovParam.DAT'
        copyFile(src_file,dest_file) 
      

        waterfilecontent = []
        with open(dest_file, 'r') as read_file:
            waterfilecontent = read_file.readlines()
            
            
 #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
 
        sandcontent = WriteSoiData(self.soilname,self.sitename, field_path)
        if sandcontent > 75:
            with open(dest_file, 'w') as write_file:
                for line in waterfilecontent:
                        write_file.write(line.replace("-1.00000E+005", "-1.00000E+004"))  
                    
        #copy waterBound.dat file from store to runDir
        src_file= storeDir+'\\WaterBound.DAT'
        dest_file= field_path+'\\Water.dat'
        copyFile(src_file,dest_file)
        
       
        WriteBiologydefault(self.sitename, field_path)
        
         # Start
        #includes initial, management and fertilizer 
        rowSpacing, rootWeightPerSlab, cultivar = self.WriteIniNitro(field_path, self.sitename, str(waterStressFlag), str(nitroStressFlag)) 
        
        if cultivar != "fallow":
            WriteCropVariety(self.crop,cultivar,self.sitename, field_path)
        else:
            src_file= storeDir+'\\fallow.var'
            dest_file= field_path+'\\fallow.var'
            copyFile(src_file,dest_file)
            

      
        WriteDripIrrigationFile(self.sitename, field_path)
        
        linSeaDate = None
        

        hourly_flag, edate = WriteWeather(self.experimentname ,self.treatmentname ,self.stationtypename,self.weather,field_path,str_ltempVar,str_lrainVar,str_lCO2Var,linSeaDate)
    
        
        WriteSoluteFile(self.soilname,field_path)
        WriteGasFile(field_path)
        hourlyFlag = 0 #1 if self.step_hourly.isChecked() else 0
        
        WriteTimeFileData(self.treatmentname ,self.experimentname ,self.crop,self.stationtypename,hourlyFlag,self.sitename,field_path, hourly_flag,0)
        
        WriteNitData(self.soilname,self.sitename,field_path, rowSpacing)
        self.WriteLayerGas(self.soilname,self.sitename, field_path, rowSpacing,rootWeightPerSlab)
       # WriteSoiData(self.soilname,field_name,self.sitename)
        
        if getattr(self, 'last_run_mode', None) == 'Modified':
            try:
                linSeaDate = self.selInSeadate()   # returns YYYY-MM-DD
            except Exception:
                linSeaDate = None

       # Pass linSeaDate to WriteManagement so management events are cut off if in-season run
        surfResType=WriteManagement(self.crop,self.experimentname ,self.treatmentname ,self.sitename,field_path,rowSpacing, up_to_date=linSeaDate)

        # --- Merge Expert System N applications into the management file used by the model ---
        # Fetch management_map (if needed) and expert (UI) applications from DB
        try:
            exid = read_experimentDB_id(self.crop, self.experimentname)
            tid = read_treatmentDB_id(exid, self.treatmentname)
        except Exception:
            tid = None
            exid = None
        
        # management map up-to-inseason (what WriteManagement wrote into .man)
        try:
            mgmt_map_up = get_management_n_map(tid, up_to_date=linSeaDate) if linSeaDate else get_management_n_map(tid)
        except Exception:
            mgmt_map_up = {}

        # combined_map is what update_n_applied persisted (combined values)
        try:
            combined_map = get_nitrogen_applied_map(tid, up_to_date=None, t_exid=exid) or {}
        except Exception:
            combined_map = {}

        # Normalize keys -> datetime objects (skip malformed keys)
        def to_dt_map(m):
            out = {}
            for k, v in (m or {}).items():
                try:
                    # normalize key text (strip quotes/whitespace) then parse
                    ktext = str(k).strip().strip("'\"")
                    dt = pd.to_datetime(ktext, errors='coerce')
                    if pd.isna(dt):
                        continue

                    # normalize value text (strip quotes/commas) then coerce to numeric
                    vtext = str(v).strip().strip("'\"").replace(',', '')
                    num = pd.to_numeric(vtext, errors='coerce')
                    if pd.isna(num):
                        # skip non-numeric entries instead of raising
                        continue

                    out[dt.normalize()] = float(num)
                except Exception:
                    # skip any malformed entry silently
                    continue                  
            return out

      #  mgmt_dt = to_dt_map(mgmt_map_up)
       # comb_dt = to_dt_map(combined_map)

        # Build three management maps:
        #  - mgmt_all_dt: management for the whole season (used to recognize true management entries)
        #  - mgmt_dt (mgmt_up): management up-to-inseason (what Manage file contains for in-season runs)
        #  - comb_dt: combined values persisted in DB (what update_n_applied wrote)
        try:
            mgmt_all_map = get_management_n_map(tid) or {}
        except Exception:
            mgmt_all_map = {}
        mgmt_all_dt = to_dt_map(mgmt_all_map)
        mgmt_dt = to_dt_map(mgmt_map_up)   # management up to in-season (may exclude post-inseason mgmt)
        comb_dt = to_dt_map(combined_map)

        '''
        # Compute ES-only: combined - mgmt_up (clamped >=0)
        # But do NOT treat dates that are pure management (exist in mgmt_all) as ES.

        # Compute ES-only: combined - mgmt_up (clamped >=0)
        es_dt = {}
        insea_dt = pd.to_datetime(linSeaDate).normalize() if linSeaDate else None

        # Retrieve override dates to handle replacement logic correctly
        overrides = getattr(self, 'override_dates', set())

        for dt, comb_val in comb_dt.items():
            # If this date is a known management date (full-season), and the combined value equals the management amount,
            # then it's a management entry — skip it (even if it's after in-season).
            mg_all_val = mgmt_all_dt.get(dt, 0.0)
            if mg_all_val and abs(comb_val - mg_all_val) < 1e-8:
                # exact match to management — not an ES addition
                continue

            # Calculate expert-system contribution relative to management up-to-inseason
            mg_up_val = mgmt_dt.get(dt, 0.0)
            es_val = comb_val - mg_up_val

            # Only positive differences are ES additions
            if es_val <= 0:
                continue

            # For in-season runs, only include ES entries on/after the in-season date
            if linSeaDate:
                try:
                    insea_dt = pd.to_datetime(linSeaDate).normalize()
                    if dt >= insea_dt:
                        es_dt[dt] = es_val
                except Exception:
                    # fallback: include if parsing fails
                    es_dt[dt] = es_val
            else:
                es_dt[dt] = es_val
        '''

                # Compute ES-only: combined - mgmt_up (clamped >=0)
        es_dt = {}
        insea_dt = pd.to_datetime(linSeaDate).normalize() if linSeaDate else None

        # Retrieve override dates to handle replacement logic correctly
        overrides = getattr(self, 'override_dates', set())
        
        # Convert override dates to datetime for comparison
        override_dts = set()
        for od in overrides:
            try:
                od_dt = pd.to_datetime(od, errors='coerce')
                if not pd.isna(od_dt):
                    override_dts.add(od_dt.normalize())
            except Exception:
                pass

        for dt, comb_val in comb_dt.items():
            # If this date is in override_dates, the user chose to replace management with ES value
            # In this case, comb_val IS the ES value (not combined), so use it directly
            if dt in override_dts:
                # For override dates, the combined value in DB is the ES value only
                es_dt[dt] = comb_val
                print(f"DEBUG: Override date {dt.strftime('%Y-%m-%d')} -> ES value = {comb_val}")
                continue
            
            # If this date is a known management date (full-season), and the combined value equals the management amount,
            # then it's a management entry — skip it (even if it's after in-season).
            mg_all_val = mgmt_all_dt.get(dt, 0.0)
            if mg_all_val and abs(comb_val - mg_all_val) < 1e-8:
                # exact match to management — not an ES addition
                continue

            # Calculate expert-system contribution relative to management up-to-inseason
            mg_up_val = mgmt_dt.get(dt, 0.0)
            es_val = comb_val - mg_up_val

            # Only positive differences are ES additions
            if es_val <= 0:
                continue

            # For in-season runs, only include ES entries on/after the in-season date
            if linSeaDate:
                try:
                    insea_dt = pd.to_datetime(linSeaDate).normalize()
                    if dt >= insea_dt:
                        es_dt[dt] = es_val
                except Exception:
                    # fallback: include if parsing fails
                    es_dt[dt] = es_val
            else:
                es_dt[dt] = es_val

        # Count the number of Applications of N in ES
        # --- count ES entries (insert right after es_dt is populated) ---
        try:
            # total number of ES date entries
            es_count = len(es_dt)

            # number of ES entries with positive amount (defensive: coerce to float)
            es_positive_count = sum(1 for v in es_dt.values() if (lambda x: float(x) if x is not None else 0.0)(v) > 0.0)

            # optional debug/log
   #         print(f"ES entries total={es_count}, positive={es_positive_count}")
        except Exception:
            es_count = 0
            es_positive_count = 0

        # Scale Expert System Nitrogen Value
        factor = 100*(float(rowSpacing)/2)/10000

        original_ES_Nlist = sorted([(d.strftime('%Y-%m-%d'), v) for d, v in es_dt.items()])
        scaled_ES_Nlist = sorted([(d.strftime('%Y-%m-%d'), v, float(v) * factor) for d, v in es_dt.items()])

        # DEBUG: show what we'll write
     #   try:
     #       print("MGMT_UP (dates):", sorted([(d.strftime('%Y-%m-%d'), v) for d, v in mgmt_dt.items()]))
     #       print("COMBINED (dates):", sorted([(d.strftime('%Y-%m-%d'), v) for d, v in comb_dt.items()]))
      #      print("ES_ONLY (dates to append):", original_ES_Nlist)  #sorted([(d.strftime('%Y-%m-%d'), v) for d, v in es_dt.items()]))
      #      print("Scaled ES_ONLY (dates to append):", scaled_ES_Nlist)  #sorted([(d.strftime('%Y-%m-%d'), v) for d, v in scaled_ES_Nlist.items()]))
      #  except Exception:
      #      pass
        
      

        # Compose .man filename
        man_file = os.path.join(field_path, f"{self.sitename}.man")

        # Read existing file if present
        if os.path.exists(man_file):
            with open(man_file, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()

                        
            # If this is an in-season run, remove management lines dated after in‑season date
            if linSeaDate:
                try:
                    insea_dt = pd.to_datetime(linSeaDate).normalize()
                    filtered = []
                    # use re.search and accept optional surrounding single quotes
                    date_rx = re.compile(r"'?(\d{1,2}/\d{1,2}/\d{4})'?")
                    in_fert_section = True

                    # Get override_dates to remove management lines for overridden dates
                    overrides = getattr(self, 'override_dates', set())
                    # Normalize override dates to MM/DD/YYYY format for comparison
                    override_dates_mmddyyyy = set()
                    for od in overrides:
                        try:
                            od_dt = pd.to_datetime(od, errors='coerce')
                            if not pd.isna(od_dt):
                                override_dates_mmddyyyy.add(od_dt.strftime("%m/%d/%Y"))
                        except Exception:
                            pass

                    for ln in lines:
                        # once we pass into PGR / Residue / Tillage blocks, keep lines as-is
                        if re.match(r'^\s*\[(PGR|Residue|Tillage)\]', ln, re.IGNORECASE):
                            in_fert_section = False

                        if in_fert_section:
                            m = date_rx.search(ln)
                            if m:
                                try:
                                    date_str = m.group(1)  # MM/DD/YYYY
                                    ln_dt = pd.to_datetime(date_str, format='%m/%d/%Y', errors='coerce')
                                    if not pd.isna(ln_dt):
                                        # Remove line if date is after in-season cutoff
                                        if ln_dt.normalize() > insea_dt:
                                            continue
                                        # Remove line if date is in override_dates (user chose to replace)
                                        if date_str in override_dates_mmddyyyy:
                                            print(f"DEBUG: Removing management line for override date {date_str}")
                                            continue
                                except Exception:
                                    # if parsing fails, keep the line
                                    pass
                        filtered.append(ln)
                    lines = filtered
                except Exception:
                    # if anything goes wrong with filtering, fall back to original file contents
                    pass

            # discover dates already present in file to avoid duplicates (store as normalized strings)
            existing_dates = set()
            date_rx = re.compile(r"'?(\d{1,2}/\d{1,2}/\d{4})'?")
            for ln in lines:
                m = date_rx.search(ln)
                if m:
                    try:
                        iso = pd.to_datetime(m.group(1), format='%m/%d/%Y', errors='coerce')
                        if not pd.isna(iso):
                            existing_dates.add(iso.normalize().strftime('%Y-%m-%d'))
                    except Exception:
                        continue
        else:
            # If file missing, start from WriteManagement content if available
            lines = []
            existing_dates = set()
            for d, v in sorted(mgmt_dt.items()):
                ds = d.strftime("%m/%d/%Y")
                lines.append(f"'{ds}'    {v:.2f}\n")
                existing_dates.add(d.strftime('%Y-%m-%d'))
        

        # Build ES lines skipping duplicates (and update existing amount if needed)
        es_lines = []
        # map iso -> scaled amount for convenience (downstream code uses es_map)
        es_map = {dt.strftime('%Y-%m-%d'): float(v)*factor for dt, v in es_dt.items()}

        # Debug: show es_map and existing_dates
       # DEBUG: show .man lines & es_map before trying to update existing lines
   #     try:
         #   print("DEBUG: es_map:", sorted(es_map.items()))
          #  print("DEBUG: existing_dates:", sorted(list(existing_dates)))
         #   # show a few .man lines around any matching dates for quick inspection
       #     for iso_key, _ in sorted(es_map.items()):
         #       ds = pd.to_datetime(iso_key).strftime("%m/%d/%Y")
          #      matches = [ (i, ln.rstrip()) for i, ln in enumerate(lines) if ds in ln ]
           #     if matches:
             #       print(f"DEBUG: lines containing {ds}:")
            #        for i, ln in matches:
             #           print(f"  line {i}: {ln}")
       # except Exception:
         #   pass

        
        # If the .man already contains a line with the same date, update the numeric amount in-place.
        # Otherwise prepare an insertion line.  Handle multiple ES rows reliably.
  #     date_token_rx_template = r"'?{ds}'?\s*([0-9]+(?:\.[0-9]+)?)"

        # Sort ES entries chronologically to ensure deterministic insertion order
        try:
            sorted_es_items = sorted(es_map.items(), key=lambda kv: pd.to_datetime(kv[0]))
        except Exception:
            sorted_es_items = list(es_map.items())

        updated_any = False
        es_insert_isos = []

        # Use a stricter date-presence test (word boundary around date) to avoid accidental substring matches
        # --- robust update of existing .man lines for ES dates ---
        try:
            for iso, amt in sorted_es_items:
                ds = pd.to_datetime(iso).strftime("%m/%d/%Y")
                found = False
                # match the date as a whole word with optional surrounding single quotes
                date_word_rx = re.compile(r"\b'?" + re.escape(ds) + r"'?\b")

                for idx, ln in enumerate(lines):
                    if not date_word_rx.search(ln):
                        continue
                    try:
                        # locate date occurrence and then search for the first numeric token AFTER the date
                        mdate = date_word_rx.search(ln)
                        start_after = mdate.end()
                        tail = ln[start_after:]
                        # find first number (integer or float) after the date
                        num_rx = re.compile(r"([+-]?\d+(?:\.\d+)?)")
                        mnum = num_rx.search(tail)
                        if mnum:
                            # replace only the first numeric occurrence after the date
                            before = ln[: start_after + mnum.start()]
                            after = tail[mnum.end():]
                            new_ln = before + f"{amt:.2f}" + after
                            if new_ln != ln:
                                lines[idx] = new_ln
                                updated_any = True
                                print(f"DEBUG: Updated line for {ds} with amount {amt:.6f}")
                            found = True
                            break
                        else:
                            # No numeric token found after the date — insert the amount right after the date
                            insert_text = f"    {amt:.6f}    "
                            new_ln = ln[:start_after] + insert_text + ln[start_after:]
                            lines[idx] = new_ln
                            updated_any = True
                            found = True
                            break
                    except Exception as e:
                        print("DEBUG update_line exception:", e)
                        continue

                if not found:
                    es_insert_isos.append(iso)
        except Exception as e:
            print("DEBUG ES update loop failed:", e)
                # collect missing ISOs; insertion done after loop to avoid modifying 'lines' while iterating
              # if iso not in es_insert_isos:
               #    es_insert_isos.append(iso)

        # Build ES lines for dates that were not present in file
        es_lines_to_insert = []
        for iso in es_insert_isos:
            ds = pd.to_datetime(iso).strftime("%m/%d/%Y")
            es_lines_to_insert.append(
                f"'{ds}' %-14.6f%-14.6f%-14.6f%-14.6f%-14.6f%-14.6f\n" % (
                    es_map[iso], 5.0, 0.0, 0.0, 0.0, 0.0
                )
            )

        # Insert ES lines in the correct place, depending on crop:
        #   - non-cotton: before [Residue]
        #   - cotton: before [PGR] if present; otherwise before [Residue]; otherwise at end.
        if es_lines_to_insert:
            if self.crop.lower() != 'cotton':
                residue_idx = None
                for i, ln in enumerate(lines):
                    if re.match(r'^\s*\[Residue\]', ln, re.IGNORECASE):
                        residue_idx = i
                        break
                if residue_idx is None:
                    lines.extend(es_lines_to_insert)
                else:
                    lines[residue_idx:residue_idx] = es_lines_to_insert
            else:
                pgr_idx = None
                residue_idx = None
                for i, ln in enumerate(lines):
                    if pgr_idx is None and re.match(r'^\s*\[PGR\]', ln, re.IGNORECASE):
                        pgr_idx = i
                    if residue_idx is None and re.match(r'^\s*\[Residue\]', ln, re.IGNORECASE):
                        residue_idx = i
                    if pgr_idx is not None and residue_idx is not None:
                        break

                insert_at = None
                if pgr_idx is not None:
                    insert_at = pgr_idx
                elif residue_idx is not None:
                    insert_at = residue_idx

                if insert_at is None:
                    lines.extend(es_lines_to_insert)
                else:
                    lines[insert_at:insert_at] = es_lines_to_insert

        # Final cleanup: remove any line with a date after the in-season cutoff
        # NOTE: This section was previously INSIDE the "if es_lines_to_insert:" block - MOVED OUT
        if linSeaDate:
            try:
                insea_dt = pd.to_datetime(linSeaDate).normalize()
                filtered_final = []
                # build set of management dates (iso) so we only remove management entries
                mgmt_iso_set = {d.strftime('%Y-%m-%d') for d in mgmt_dt.keys()}
                in_fert_section = True
                for ln in lines:
                    if re.match(r'^\s*\[(PGR|Residue|Tillage)\]', ln, re.IGNORECASE):
                        in_fert_section = False

                    if in_fert_section:
                        m = date_rx.search(ln)
                        if m:
                            try:
                                ln_dt = pd.to_datetime(m.group(1), format='%m/%d/%Y', errors='coerce')
                                if (not pd.isna(ln_dt)) and ln_dt.normalize() > insea_dt:
                                    # remove only if this date corresponds to an original management date
                                    if ln_dt.normalize().strftime('%Y-%m-%d') in mgmt_iso_set:
                                        continue
                            except Exception:
                                pass
                         
                    filtered_final.append(ln)
                lines = filtered_final
            except Exception:
                # if anything goes wrong, fall back to lines as-is
                pass

        # Inject ES-positive-count into .man descriptive/header lines before writing
        # NOTE: This was previously inside "if es_lines_to_insert:" - now runs always when linSeaDate is set
                # Inject ES-positive-count into .man descriptive/header lines before writing
        # NOTE: This was previously inside "if es_lines_to_insert:" - now runs always when linSeaDate is set
        try:
            descr_rx = re.compile(r'Number of Fertilizer applications.*mappl is in total mg N applied to grid.*', re.IGNORECASE | re.DOTALL)
            header_rx = re.compile(r'^\s*NumberFertApplications\b', re.IGNORECASE)
            num_line_rx = re.compile(r'^\s*(\d+)\s*$')

            # Count actual fertilizer application lines in the file (lines with dates in fertilizer section)
            # This is more accurate than trying to compute existing_napps + es_positive_count
            actual_app_count = 0
            in_fert_section = True
            date_rx_count = re.compile(r"'?\d{1,2}/\d{1,2}/\d{4}'?")
            for ln in lines:
                # Stop counting when we hit [Residue], [PGR], or [Tillage]
                if re.match(r'^\s*\[(PGR|Residue|Tillage)\]', ln, re.IGNORECASE):
                    in_fert_section = False
                if in_fert_section and date_rx_count.search(ln):
                    actual_app_count += 1

            # clamp to [0,25]
            total_apps = max(0, min(25, actual_app_count))

            # Find the position to insert/update the count
            insert_idx = None
            for i, ln in enumerate(lines):
                if descr_rx.search(ln):
                    # next non-empty line is expected to hold the numeric count
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    insert_idx = j
                    break

            # Fallback: look for NumberFertApplications header then numeric line
            if insert_idx is None:
                for i, ln in enumerate(lines):
                    if header_rx.match(ln):
                        j = i + 1
                        while j < len(lines) and lines[j].strip() == "":
                            j += 1
                        insert_idx = j
                        break

            # Insert or replace numeric line
            if insert_idx is None:
                # place near top after initial comments/blank lines
                idx = 0
                for i, ln in enumerate(lines):
                    if ln.strip() == "" or ln.strip().startswith(("#", ";", "//")):
                        continue
                    idx = i
                    break
                lines.insert(idx, f"{total_apps}\n")
            else:
                if insert_idx < len(lines) and num_line_rx.match(lines[insert_idx]):
                    lines[insert_idx] = f"{total_apps}\n"
                else:
                    # insert at the discovered position
                    lines.insert(insert_idx, f"{total_apps}\n")

        except Exception as e:
            print("DEBUG: failed to update NumberFertApplications numeric line:", e)

        # Write back - ALWAYS write the file after filtering/modifications
        try:
            with open(man_file, "w", encoding="utf-8") as fh:
                fh.writelines(lines)
            print(f"DEBUG: Wrote .man file with {len(lines)} lines")
        except Exception as e:
            print("Warning: could not write .man file:", e)

        # DEBUG: show what we wrote (first 40 lines)
        try:
            with open(man_file, "r", encoding="utf-8", errors="ignore") as fh:
                head = [ln.rstrip() for ln, _ in zip(fh, range(40))]
            print("WROTE .man head:\n", "\n".join(head))
        except Exception:
            pass



        '''
        # Build ES lines for dates that were not present in file
        es_lines_to_insert = []
        for iso in es_insert_isos:
            ds = pd.to_datetime(iso).strftime("%m/%d/%Y")
            es_lines_to_insert.append(
                f"'{ds}'    {es_map[iso]:.6f}     5.000000    0.000000    0.000000    0.000000  0.000000\n"
            )

        # Insert ES lines in the correct place, depending on crop:
        #   - non-cotton: before [Residue]
        #   - cotton: before [PGR] if present; otherwise before [Residue]; otherwise at end.
        if es_lines_to_insert:
            if self.crop.lower() != 'cotton':
                residue_idx = None
                for i, ln in enumerate(lines):
                    if re.match(r'^\s*\[Residue\]', ln, re.IGNORECASE):
                        residue_idx = i
                        break
                if residue_idx is None:
                    lines.extend(es_lines_to_insert)
                else:
                    lines[residue_idx:residue_idx] = es_lines_to_insert
            else:
                pgr_idx = None
                residue_idx = None
                for i, ln in enumerate(lines):
                    if pgr_idx is None and re.match(r'^\s*\[PGR\]', ln, re.IGNORECASE):
                        pgr_idx = i
                    if residue_idx is None and re.match(r'^\s*\[Residue\]', ln, re.IGNORECASE):
                        residue_idx = i
                    if pgr_idx is not None and residue_idx is not None:
                        break

                insert_at = None
                if pgr_idx is not None:
                    insert_at = pgr_idx
                elif residue_idx is not None:
                    insert_at = residue_idx

                if insert_at is None:
                    lines.extend(es_lines_to_insert)
                else:
                    lines[insert_at:insert_at] = es_lines_to_insert


        
            # Final cleanup: remove any line with a date after the in-season cutoff
            if linSeaDate:
                try:
                    insea_dt = pd.to_datetime(linSeaDate).normalize()
                    filtered_final = []
                    # build set of management dates (iso) so we only remove management entries
                    mgmt_iso_set = {d.strftime('%Y-%m-%d') for d in mgmt_dt.keys()}
                    in_fert_section = True
                    for ln in lines:
                        if re.match(r'^\s*\[(PGR|Residue|Tillage)\]', ln, re.IGNORECASE):
                            in_fert_section = False

                        if in_fert_section:
                            m = date_rx.search(ln)
                            if m:
                                try:
                                    ln_dt = pd.to_datetime(m.group(1), format='%m/%d/%Y', errors='coerce')
                                    if (not pd.isna(ln_dt)) and ln_dt.normalize() > insea_dt:
                                        # remove only if this date corresponds to an original management date
                                       if ln_dt.normalize().strftime('%Y-%m-%d') in mgmt_iso_set:
                                        continue
                                except Exception:
                                    pass
                             
                        filtered_final.append(ln)
                    lines = filtered_final
                except Exception:
                    # if anything goes wrong, fall back to lines as-is
                    pass

            # Inject ES-positive-count into .man descriptive/header lines before writing
                        
            try:
                descr_rx = re.compile(r'Number of Fertilizer applications.*mappl is in total mg N applied to grid.*', re.IGNORECASE | re.DOTALL)
                header_rx = re.compile(r'^\s*NumberFertApplications\b', re.IGNORECASE)
                num_line_rx = re.compile(r'^\s*(\d+)\s*$')

                # 1) Try to find existing numeric line immediately after descriptive line
                existing_napps = None
                insert_idx = None

                for i, ln in enumerate(lines):
                    if descr_rx.search(ln):
                        # next non-empty line is expected to hold the numeric count
                        j = i + 1
                        while j < len(lines) and lines[j].strip() == "":
                            j += 1
                        insert_idx = j
                        if j < len(lines):
                            m = num_line_rx.match(lines[j])
                            if m:
                                existing_napps = int(m.group(1))
                        break

                # 2) Fallback: look for NumberFertApplications header then numeric line
                if existing_napps is None:
                    for i, ln in enumerate(lines):
                        if header_rx.match(ln):
                            j = i + 1
                            while j < len(lines) and lines[j].strip() == "":
                                j += 1
                            insert_idx = j
                            if j < len(lines):
                                m = num_line_rx.match(lines[j])
                                if m:
                                    existing_napps = int(m.group(1))
                            break

                # 3) Last fallback: derive existing count from mgmt_dt or existing_dates
                if existing_napps is None:
                    try:
                        existing_napps = len(mgmt_dt) if 'mgmt_dt' in locals() and mgmt_dt else len(existing_dates)
                    except Exception:
                        existing_napps = len(existing_dates)

                # Compute final total (existing management apps + ES positive entries)
                try:
                    total_apps = int(existing_napps) + int(es_positive_count)
                except Exception:
                    total_apps = int(es_positive_count or 0)

                # clamp to [0,25]
                total_apps = max(0, min(25, total_apps))

                # Insert or replace numeric line
                if insert_idx is None:
                    # place near top after initial comments/blank lines
                    idx = 0
                    for i, ln in enumerate(lines):
                        if ln.strip() == "" or ln.strip().startswith(("#", ";", "//")):
                            continue
                        idx = i
                        break
                    lines.insert(idx, f"{total_apps}\n")
                else:
                    if insert_idx < len(lines) and num_line_rx.match(lines[insert_idx]):
                        lines[insert_idx] = f"{total_apps}\n"
                    else:
                        # insert at the discovered position
                        lines.insert(insert_idx, f"{total_apps}\n")

                # keep descriptive [ES=..] token if present (debug)
          #      print(f"DEBUG: existing_napps={existing_napps}, es_positive_count={es_positive_count}, total_apps={total_apps}")
            except Exception as e:
                print("DEBUG: failed to update NumberFertApplications numeric line:", e)

            # Write back
            try:
                with open(man_file, "w", encoding="utf-8") as fh:
                    fh.writelines(lines)
            except Exception as e:
                print("Warning: could not write .man file:", e)

            # DEBUG: show what we wrote (first 40 lines)
            try:
                with open(man_file, "r", encoding="utf-8", errors="ignore") as fh:
                    head = [ln.rstrip() for ln, _ in zip(fh, range(40))]
                print("WROTE .man head:\n", "\n".join(head))
            except Exception:
                pass

      #  except Exception as e:
       #     print("Warning: could not merge ES N into .man file (insert-before-Residue):", e)
        '''
        

        irrType = irrigationInfo(self.crop,self.experimentname ,self.treatmentname )
     #   print(irrType)

        WriteMulchGeo(field_path,surfResType)
        o_t_exid = getTreatmentID(self.treatmentname ,self.experimentname ,self.crop)

        WriteIrrigation(self.sitename, field_path, newsimulationID, o_t_exid)

        WriteRunFile(self.crop,self.soilname,self.sitename, cultivar,field_path,self.stationtypename)     


        
        src_file= field_path +"\\"+self.sitename+".lyr"                    
        layerdest_file= field_path +"\\" + self.sitename+".lyr"
        createsoil_opfile= self.soilname
        grid_name = self.sitename

        pp = subprocess.Popen([createsoilexe,layerdest_file,"/GN",grid_name,"/SN",createsoil_opfile],cwd=self.fieldpath)
        while pp.poll() is None:
            time.sleep(1)            

        runname = self.fieldpath+"\\Run"+self.sitename+".dat"       
        edate = edate + timedelta(days=22)
        self.simStatus.setText("")
        self.simStatus.repaint()
        os.chdir(self.fieldpath)
      
        result1 = [self.sitename,self.crop, field_path, True]

        controller = Controller()
               
   #     print("DEBUG N run: crop=", self.crop,
    #          "sitename=", self.sitename,
     #         "field_path=", field_path,
     #         "expected_g01=", os.path.join(field_path, f"{self.sitename}.g01"))
        controller.launch(self.crop, runname, result1, self.simStatus, newsimulationID, self)
       #controller.launch(self.crop, runname, result1, self.simStatus, newsimulationID, self)


    def _compute_days_after_planting(self, df):
        """
        Return integer 'days after planting' for each row in df based on Sowing (or Simulation Start)
        for this crop/experiment/treatment. Falls back to df['Date'].min() if needed.
        """
        # df['Date'] must be datetime64[ns]
        sowing_str = read_operation_timeDB2(
            "Sowing",
            self.treatmentname,
            self.experimentname,
            self.crop
        )
        if sowing_str:
            origin = pd.to_datetime(sowing_str, format="%m/%d/%Y", errors="coerce")
        else:
            sim_start_str = read_operation_timeDB2(
                "Simulation Start",
                self.treatmentname,
                self.experimentname,
                self.crop
            )
            origin = pd.to_datetime(sim_start_str, format="%m/%d/%Y", errors="coerce") if sim_start_str else df['Date'].min()

        if origin is None or pd.isna(origin):
            origin = df['Date'].min()

        origin = origin.normalize()
        # days since planting, then shift so first day is 1
        days0 = (df['Date'].dt.normalize() - origin).dt.days
      #  return (df['Date'].dt.normalize() - origin.normalize()).dt.days
        return days0 - days0.min() + 1

     # Show the N plots  
    def on_click_nitroTab(self, use_previous=False):
        
        # At the start of your application, or before any simulation run

        self.nitroTab.fig1.clf()
        self.nitroTab.fig2.clf()
        self.nitroTab.fig3.clf()

        locator = mdates.DayLocator(interval=50)
        formatter = mdates.DateFormatter('%m/%d')

        # Build list of simulation entries to plot:
        # - previous saved run (prevsimulationID) from runDir
        # - latest run (if present) from tempDirN / tempDirISN; allow both if both exist
        sim_entries = []
        # previous (historical) run (management-only)
#        print("self.prevsimulationID: ", self.prevsimulationID)
        if hasattr(self, 'prevsimulationID'):
            sim_entries.append({
                'sim_id': self.prevsimulationID,
                'label': ' Initial N ',
                'color': 'b',
                'path': os.path.join(runDir, str(self.prevsimulationID))
            })

        # latest run: check both possible temp folders (full and in-season) and add whichever exist
        if hasattr(self, 'newsimulationID'):
            # full-season temp
            full_path = tempDirN
            inseason_path = tempDirISN
            # prefer adding both if both have data
            g01_name = self.sitename + ".g01"
            full_g01 = os.path.join(full_path, g01_name)
            insea_g01 = os.path.join(inseason_path, g01_name)

            # If in-season was the last run, put that first (for legend/order)
            if getattr(self, 'last_run_mode', None) == 'Modified':
                if os.path.exists(insea_g01):
                    sim_entries.append({
                        'sim_id': self.newsimulationID,
                        'label': 'Modified',
                        'color': 'g',
                        'path': inseason_path
                    })
                if os.path.exists(full_g01):
                    sim_entries.append({
                        'sim_id': self.newsimulationID,
                        'label': 'Planned',# (management-only)',
                        'color': 'r',
                        'path': full_path
                    })
            else:
                # last run not inseason -> add full first
                if os.path.exists(full_g01):
                    sim_entries.append({
                        'sim_id': self.newsimulationID,
                        'label': 'Planned',#a (management-only)',
                        'color': 'r',
                        'path': full_path
                    })
                if os.path.exists(insea_g01):
                    sim_entries.append({
                        'sim_id': self.newsimulationID,
                        'label': 'Modified',
                        'color': 'g',
                        'path': inseason_path
                    })

        # debug: show what we will try to plot
    #    try:
     # #═      print("on_click_nitroTab: sim_entries=", [(e['sim_id'], e['label'], e['path']) for e in sim_entries])
      #  except Exception:
       #     pass

        # Prepare DB plotting dataframes for each entry
        try:
            exid = read_experimentDB_id(self.crop, self.experimentname)
            tid = read_treatmentDB_id(exid, self.treatmentname)
            plantDensity = getPlantDensity(tid)
        except Exception:
            tid = None
            plantDensity = 1

        dfs = []
        labels = []
        colors = []

        # helper to safely parse CSVs and normalize
        def _safe_read_and_normalize(massbi_file, g01_file, g05_file):
            # return tuple of dataframes (dfN, df_NUp, df_Ndem, df_NLeach) or None on failure
            try:
                if not (os.path.exists(massbi_file) and os.path.exists(g01_file) and os.path.exists(g05_file)):
                    return None

                # MassBI.out -> Date, Min_N
                dfN = pd.read_csv(massbi_file, dtype=str, engine='python', error_bad_lines=False, warn_bad_lines=False)
                # try to find 'Date' and 'Min_N' columns regardless of spaces in header
                dfN.columns = dfN.columns.str.strip()
                if 'Date' not in dfN.columns or 'Min_N' not in dfN.columns:
                    # try fuzzy match
                    date_col = next((c for c in dfN.columns if 'date' in c.lower()), None)
                    min_col = next((c for c in dfN.columns if 'min' in c.lower() and 'n' in c.lower()), None)
                    if date_col and min_col:
                        dfN = dfN[[date_col, min_col]]
                        dfN.columns = ['Date', 'Min_N']
                    else:
                        return None
                dfN = dfN[['Date', 'Min_N']].copy()
                dfN['Date'] = pd.to_datetime(dfN['Date'].astype(str).str.strip(), format='%m/%d/%Y', errors='coerce')
                dfN['Min_N'] = pd.to_numeric(dfN['Min_N'].astype(str).str.strip().replace('', '0'), errors='coerce')
                dfN = dfN.dropna(subset=['Date']).reset_index(drop=True)

                # g01 -> date, NUpt, N_Dem (headers may be trim-misaligned)
                df_g01 = pd.read_csv(g01_file, dtype=str, engine='python', error_bad_lines=False, warn_bad_lines=False)
                df_g01.columns = df_g01.columns.str.strip()
                # try to find column names
                date_col = next((c for c in df_g01.columns if 'date' in c.lower()), None)
                nupt_col = next((c for c in df_g01.columns if 'nupt' in c.lower()), None)
                ndem_col = next((c for c in df_g01.columns if 'n_dem' in c.lower() or 'n dem' in c.lower() or 'ndem' in c.lower()), None)
                if date_col is None:
                    return None
                df_g01 = df_g01[[date_col, nupt_col or df_g01.columns[1], ndem_col or df_g01.columns[2]]].copy()
                df_g01.columns = ['date', 'NUpt', 'N_Dem']


                df_g01['date'] = pd.to_datetime(df_g01['date'].astype(str).str.strip(), format='%m/%d/%Y', errors='coerce')
                df_g01['NUpt'] = pd.to_numeric(df_g01['NUpt'].astype(str).str.strip().replace('', '0'), errors='coerce').fillna(0) * plantDensity * 10
                df_g01['N_Dem'] = pd.to_numeric(df_g01['N_Dem'].astype(str).str.strip().replace('', '0'), errors='coerce').fillna(0) * plantDensity * 10
                df_g01 = df_g01.dropna(subset=['date']).reset_index(drop=True)

                # g05 -> Date, N_Leach
                
                # --- read raw first, then use header *positions* to select columns ---
                with open(g05_file, "r", encoding="utf-8", errors="ignore") as f:
                    header_line = f.readline().strip()

                # split header line by comma or whitespace
                if "," in header_line:
                    raw_cols = [h.strip() for h in header_line.split(",")]
                    sep = ","
                else:
                    raw_cols = header_line.split()
                    sep = r"\s+"

                def _norm_col(c):
                    return re.sub(r"[^a-z0-9]", "", str(c).lower())

                # find index of date and leach headers from header *names*
                idx_date = None
                idx_leach = None
                for i, h in enumerate(raw_cols):
                    n = _norm_col(h)
                    if idx_date is None and "date" in n:
                        idx_date = i
                    if idx_leach is None and ("leach" in n or "leached" in n or "drain" in n or "loss" in n):
                        idx_leach = i
                    if idx_date is not None and idx_leach is not None:
                        break

                if idx_date is None or idx_leach is None:
                    return None  # can't locate required headers

                # now read the whole file with the detected separator
                df_NLeach = pd.read_csv(g05_file, sep=sep, engine="python", header=0, dtype=str)
                # make sure columns list matches header_line tokenization
                # if pandas inferred a different number of columns, fall back to using .values
                values = df_NLeach.values

                # guard against short rows
                if values.shape[1] <= max(idx_date, idx_leach):
                    return None

                # build clean DataFrame using the *positions* we found
                dates_raw = values[:, idx_date]
                leach_raw = values[:, idx_leach]

                df_NLeach = pd.DataFrame({"Date": dates_raw, "N_Leach": leach_raw})
                df_NLeach["Date"] = pd.to_datetime(
                    df_NLeach["Date"].astype(str).str.strip(),
                    format="%m/%d/%Y",
                    errors="coerce",
                )
                df_NLeach["N_Leach"] = pd.to_numeric(
                    df_NLeach["N_Leach"].astype(str).str.strip().replace("", "0"),
                    errors="coerce",
                ).fillna(0)
                df_NLeach = df_NLeach.dropna(subset=["Date"]).reset_index(drop=True)

                return dfN, df_g01, df_NLeach
            except Exception as e:
       #         print("DEBUG reading nitro files error:", e)
                return None

        # For each simulation entry, try to read files, save DB rows used by plotting and then fetch for plotting
        for entry in sim_entries:
            sim_id = entry['sim_id']
            entry_path = entry['path']
            massbi_file = os.path.join(entry_path, 'MassBI.out')
            g01_File = os.path.join(entry_path, self.sitename + ".g01")
            g05_File = os.path.join(entry_path, self.sitename + ".g05")

            parsed = _safe_read_and_normalize(massbi_file, g01_File, g05_File)
            if parsed is None:
             #   print(f"No data available or parse failed for simulation {sim_id} at {entry_path}. Skipping.")
                continue

            dfN, df_g01, df_NLeach = parsed

            # build df_NUp/N_Dem frames keyed by normalized date
            df_NUp = df_g01[['date', 'NUpt']].copy()
            df_NUp.rename(columns={'date': 'Date'}, inplace=True)
            df_Ndem = df_g01[['date', 'N_Dem']].copy()
            df_Ndem.rename(columns={'date': 'Date'}, inplace=True)

            # Save into temp DB table for plotting (consistent logic)
            # save_simulation_data should be idempotent for a given (sim_id, date)
            for idx, row in dfN.iterrows():
                date = row['Date']
                date_iso = date.strftime('%Y-%m-%d')
                min_n = row['Min_N'] if not pd.isna(row['Min_N']) else None
                nupt_vals = df_NUp.loc[df_NUp['Date'] == date, 'NUpt']
                nupt = nupt_vals.values[0] if not nupt_vals.empty else None
                nd_vals = df_Ndem.loc[df_Ndem['Date'] == date, 'N_Dem']
                n_dem = nd_vals.values[0] if not nd_vals.empty else None
                leak_vals = df_NLeach.loc[df_NLeach['Date'] == date, 'N_Leach']
                n_leach = leak_vals.values[0] if not leak_vals.empty else None
                # safe-save (no user prompt here)
                try:
                    save_simulation_data(sim_id, date_iso, min_n, nupt, n_dem, n_leach)
                except Exception as e:
                    print("DEBUG save_simulation_data failed:", e)

            # fetch from DB for plotting
            try:
                conn, c = openDB('cropOutput.db')
                query = """
                    SELECT Date, Min_N, NUpt, N_Dem, N_Leach
                    FROM N_simulation_ES
                    WHERE Simulation_id = ?
                    ORDER BY Date
                """
                df_plot = pd.read_sql_query(query, conn, params=(sim_id,))
                df_plot['Date'] = pd.to_datetime(df_plot['Date'])
                conn.close()
            except Exception as e:
                print("DEBUG fetch plot data failed:", e)
                continue

            # If this is the previous (historical) run, trim to in-season cutoff so
            # "Historical (management)" only covers dates <= in-season date.
            entry_label = entry['label']
            if hasattr(self, 'prevsimulationID') and sim_id == self.prevsimulationID:
                try:
                    insea = self.selInSeadate()
                    if insea:
                        insea_dt = pd.to_datetime(insea)
                        df_plot = df_plot[df_plot['Date'] <= insea_dt]
                        entry_label = f"{entry_label}" #" {insea_dt.strftime('%m/%d')}"
                except Exception:
                    pass

            dfs.append(df_plot)
            labels.append(entry_label)
            colors.append(entry['color'])

            # If this was the initial (previous) run, remove the source files now that data saved to DB.
            # This prevents the initial raw files from persisting when we plot full-season / in-season runs.
            
            try:
                if 'Initial' in entry_label:
                    for fpath in (massbi_file, g01_File, g05_File):
                        try:
                            if os.path.exists(fpath):
                                os.remove(fpath)
                                print(f"Removed initial file: {fpath}")
                        except Exception as ex:
                            # log and continue; don't abort plotting if removal fails
                            print(f"Warning: could not remove {fpath}: {ex}")
            except Exception:
                pass
            
        '''
        # --- Plot Min_N, NUpt/N_Dem and N_Leach using integer x-axis (1,2,3...) instead of dates ---
        # Map all dates to integers where the earliest date becomes 1 and subsequent days increment by 1.
        # Compute global minimum date across available dfs
        global_min = None
        for df in dfs:
            if df is None or df.empty:
                continue
            try:
                dt_min = df['Date'].min()
                if pd.isna(dt_min):
                    continue
                if global_min is None or dt_min < global_min:
                    global_min = dt_min
            except Exception:
                continue

        if global_min is None:
            # nothing to plot
            return
        '''
                # --- Determine application dates from DB (build mgmt/ES maps once, draw per simulation entry) ---
        try:
            combined_map = get_nitrogen_applied_map(tid, up_to_date=None, t_exid=exid) or {}
            insea = None
            try:
                insea = self.selInSeadate()  # YYYY-MM-DD or None
            except Exception:
                insea = None

            mgmt_map_up = get_management_n_map(tid, up_to_date=insea) if tid is not None else {}
            mgmt_all_map = get_management_n_map(tid) or {}

            def _to_dt_map(m):
                out = {}
                for k, v in (m or {}).items():
                    try:
                        if v is None:
                            continue
                        vnum = float(str(v).replace(',', '').strip())
                        if vnum == 0:
                            continue
                        dt = pd.to_datetime(str(k).strip(), errors='coerce')
                        if pd.isna(dt):
                            continue
                        out[dt.normalize()] = float(vnum)
                    except Exception:
                        continue
                return out

            comb_dt = _to_dt_map(combined_map)
            mgmt_up_dt = _to_dt_map(mgmt_map_up)     # management <= in-season (because of up_to_date)
            mgmt_all_dt = _to_dt_map(mgmt_all_map)  # full-season management

            # honor override choices recorded by update_n_applied: if user chose "No" (override)
            # remove the management entry(ies) so ES insertion will replace them.
            try:
                overrides = set(getattr(self, 'override_dates', set()))
                removed_isos = []
                for iso in list(overrides):
                    try:
                        dt = pd.to_datetime(iso, errors='coerce')
                        if pd.isna(dt):
                            continue
                        ndt = dt.normalize()
                        # remove datetime-keyed management entries
                        try:
                            if ndt in mgmt_up_dt:
                                mgmt_up_dt.pop(ndt, None)
                                removed_isos.append(iso)
                            if ndt in mgmt_all_dt:
                                mgmt_all_dt.pop(ndt, None)
                        except Exception:
                            # defensive: ignore pop errors
                            pass
                        # also remove string-keyed originals if available
                        try:
                            if isinstance(mgmt_map_up, dict) and iso in mgmt_map_up:
                                mgmt_map_up.pop(iso, None)
                            if isinstance(mgmt_all_map, dict) and iso in mgmt_all_map:
                                mgmt_all_map.pop(iso, None)
                        except Exception:
                            pass
                    except Exception:
                        continue
                # consume/clear only the overrides we removed so they don't persist longer than needed
                try:
                    for iso in removed_isos:
                        self.override_dates.discard(iso)
                except Exception:
                    pass
            except Exception:
                pass

            

            # ES (expert) dates: positive difference between combined and mgmt_up, include only in-season ES contributions
            es_dt = {}
            insea_dt = pd.to_datetime(insea).normalize() if insea else None
            for dt, comb_val in comb_dt.items():
                # Skip pure-management dates (exact match to full-season management)
                mg_all_val = mgmt_all_dt.get(dt, 0.0)
                if mg_all_val and abs(comb_val - mg_all_val) < 1e-8:
                    continue

                mg_up_val = mgmt_up_dt.get(dt, 0.0)
                es_val = comb_val - mg_up_val
                if es_val <= 0:
                    continue

                # Only include ES additions that are in-season (or include all if no in-season cutoff)
                if insea_dt is None or dt >= insea_dt:
                    es_dt[dt] = es_val

            # linewidth for application markers
            n_app_linewidth = 3.0
        except Exception:
            comb_dt = {}
            mgmt_up_dt = {}
            mgmt_all_dt = {}
            es_dt = {}
            n_app_linewidth = 3.0

        # --- Plot Min_N ---
        ax1 = self.nitroTab.fig1.add_subplot(111)
        all_x_min = []
        all_x_max = []
        lines = []

        # ensure the plotted-any flag exists
        plotted_any_ax1 = False

        # iterate sim_entries in the same order as dfs; draw lines per entry using the appropriate source
        for entry, df, label, color in zip(sim_entries, dfs, labels, colors):
            if df is None or df.empty:
                continue
            # ensure numeric columns exist and coerce
            for col in ('Min_N', 'NUpt', 'N_Dem', 'N_Leach'):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # convert dates to integer sequence starting at 1 relative to global_min
          #  x = (df['Date'].dt.normalize() - global_min.normalize()).dt.days + 1
                        # Days After Planting, based on Sowing/Simulation Start
            x = self._compute_days_after_planting(df)
            line, = ax1.plot(x, df['Min_N'], label=label, color=color, zorder=3)
            lines.append(line)
            all_x_min.append(int(x.min()))
            all_x_max.append(int(x.max()))

             # Draw vertical application markers ONLY for In-Season entries
            try:
                if 'Modified' not in entry.get('label', ''):
                    continue  # skip markers for Historical and Full Season plots

                start_dt = df['Date'].dt.normalize().min()
                end_dt = df['Date'].dt.normalize().max()
                candidate_dates = set(mgmt_up_dt.keys()) | set(es_dt.keys())
                plot_dates = [d for d in candidate_dates if (d >= start_dt and d <= end_dt)]

                for dt in sorted(plot_dates):
                    try:
                      #  xval = int((dt - global_min.normalize()).days + 1)
                        origin = df['Date'].min()
                        xval = int((dt.normalize() - origin.normalize()).days)
                    except Exception:
                        continue
                    ax_min = min(all_x_min) - 1 if all_x_min else -1e9
                    ax_max = max(all_x_max) + 1 if all_x_max else 1e9
                    if xval < ax_min or xval > ax_max:
                        continue
                    ax1.axvline(x=xval, color='0.4', linestyle=':', linewidth=n_app_linewidth, zorder=1)
                    plotted_any_ax1 = True
            except Exception:
                pass

       
        # no legend for fig1
        try:
            if ax1.legend_ is not None:
                ax1.legend_.remove()
        except Exception:
            pass

       
        ax1.set_xlabel('Days After Planting')
        ax1.set_ylabel('Min_N (kg/ha)')
        ax1.set_title('Mineral N')
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax1.grid(True, linestyle='--', linewidth=0.7, alpha=0.6)
        try:
            if all_x_min and all_x_max:
                ax1.set_xlim(min(all_x_min) - 1, max(all_x_max) + 1)
            ax1.relim(); ax1.autoscale_view()
        except Exception:
            pass
        self.nitroTab.canvas1.draw()

        # --- Plot NUpt/N_Dem --- (same per-entry line logic)
        ax2 = self.nitroTab.fig2.add_subplot(111)
        all_x_min = []
        all_x_max = []
        lines = []

        # ensure the plotted-any flag exists
        plotted_any_ax2 = False

        # iterate sim_entries in the same order as dfs; draw lines per entry using the appropriate source
        for entry, df, label, color in zip(sim_entries, dfs, labels, colors):
            if df is None or df.empty:
                continue
            # ensure numeric columns exist and coerce
            for col in ('Min_N', 'NUpt', 'N_Dem', 'N_Leach'):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

          #  x = (df['Date'].dt.normalize() - global_min.normalize()).dt.days + 1
                      # Days After Planting, based on Sowing/Simulation Start
            x = self._compute_days_after_planting(df)
            line1, = ax2.plot(x, df['NUpt'], linestyle='-', color=color, label=f"Uptk ({label})", zorder=3)
            line2, = ax2.plot(x, df['N_Dem'], linestyle='--', color=color, label=f"Dmd ({label})", zorder=3)
            lines.append(line1)
            lines.append(line2)
            all_x_min.append(int(x.min()))
            all_x_max.append(int(x.max()))

            # draw app dates for this entry
            try:
                if 'Modified' not in entry.get('label', ''):
                    continue  # skip markers for Historical and Full Season plots

                start_dt = df['Date'].dt.normalize().min()
                end_dt = df['Date'].dt.normalize().max()
                candidate_dates = set(mgmt_up_dt.keys()) | set(es_dt.keys())
                plot_dates = [d for d in candidate_dates if (d >= start_dt and d <= end_dt)]

                for dt in sorted(plot_dates):
                    try:
                      #  xval = int((dt - global_min.normalize()).days + 1)
                        origin = df['Date'].min()
                        xval = int((dt.normalize() - origin.normalize()).days)
                    except Exception:
                        continue
                    ax_min = min(all_x_min) - 1 if all_x_min else -1e9
                    ax_max = max(all_x_max) + 1 if all_x_max else 1e9
                    if xval < ax_min or xval > ax_max:
                        continue
                    ax2.axvline(x=xval, color='0.4', linestyle=':', linewidth=n_app_linewidth, zorder=1)
                    plotted_any_ax2 = True
            except Exception:
                pass

        # add proxy legend if needed
        try:
            handles, labels_ = ax2.get_legend_handles_labels()
            if handles:
                ax2.legend(handles, labels_)

            if plotted_any_ax2:
                handles, labels_ = ax2.get_legend_handles_labels()
                if 'N applications' not in labels_:
                    proxy = Line2D([0], [0], color='0.4', linestyle=':', linewidth=n_app_linewidth)
                    handles.append(proxy)
                    labels_.append('N applications')
                    ax2.legend(handles, labels_)
        except Exception:
            pass

        ax2.set_xlabel('Days After Planting')
        ax2.set_ylabel('NUpt (kg/ha) and N_Dem (kg/ha)')
        ax2.set_title("N Uptake & Demand")
        ax2.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax2.grid(True, linestyle='--', linewidth=0.7, alpha=0.6)
        try:
            if all_x_min and all_x_max:
                ax2.set_xlim(min(all_x_min) - 1, max(all_x_max) + 1)
            ax2.relim(); ax2.autoscale_view()
        except Exception:
            pass
        self.nitroTab.canvas2.draw()

        # --- Plot N_Leach --- (same per-entry line logic)
        ax3 = self.nitroTab.fig3.add_subplot(111)
        all_x_min = []
        all_x_max = []
        lines = []

        # ensure the plotted-any flag exists
        plotted_any_ax3 = False
        for entry, df, label, color in zip(sim_entries, dfs, labels, colors):
            if df is None or df.empty:
                continue
             #ensure numeric columns exist and coerce
            for col in ('Min_N', 'NUpt', 'N_Dem', 'N_Leach'):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            #x = (df['Date'].dt.normalize() - global_min.normalize()).dt.days + 1
                        # Days After Planting, based on Sowing/Simulation Start
            x = self._compute_days_after_planting(df)
            line,  = ax3.plot(x, df['N_Leach'], label=label, color=color, zorder=3)
            lines.append(line)
            all_x_min.append(int(x.min()))
            all_x_max.append(int(x.max()))

            # draw app dates for this entry
            try:
                if 'Modified' not in entry.get('label', ''):
                    continue  # skip markers for Historical and Full Season plots

                start_dt = df['Date'].dt.normalize().min()
                end_dt = df['Date'].dt.normalize().max()
                candidate_dates = set(mgmt_up_dt.keys()) | set(es_dt.keys())
                plot_dates = [d for d in candidate_dates if (d >= start_dt and d <= end_dt)]

                for dt in sorted(plot_dates):
                    try:
                     #   xval = int((dt - global_min.normalize()).days + 1)
                        origin = df['Date'].min()
                        xval = int((dt.normalize() - origin.normalize()).days)
                    except Exception:
                        continue
                    ax_min = min(all_x_min) - 1 if all_x_min else -1e9
                    ax_max = max(all_x_max) + 1 if all_x_max else 1e9
                    if xval < ax_min or xval > ax_max:
                        continue
                    ax3.axvline(x=xval, color='0.4', linestyle=':', linewidth=n_app_linewidth, zorder=1)
                    plotted_any_ax3 = True
            except Exception:
                pass

        # no legend for fig3
        try:
            if ax3.legend_ is not None:
                ax3.legend_.remove()
        except Exception:
            pass

        ax3.set_xlabel('Days After Planting')
        ax3.set_ylabel('N_Leach (kg/ha)')
        ax3.set_title('Leached N')
        ax3.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax3.grid(True, linestyle='--', linewidth=0.7, alpha=0.6)
        try:
            if all_x_min and all_x_max:
                ax3.set_xlim(min(all_x_min) - 1, max(all_x_max) + 1)
            ax3.relim(); ax3.autoscale_view()
        except Exception:
            pass
        self.nitroTab.canvas3.draw()
                
        # --- Pick folder for yield reading  ---
        N_Folder = None
        try:
            run_mode = getattr(self, 'last_run_mode', None)
        #    print(f"[on_click_nitroTab] use_previous={use_previous}, last_run_mode={run_mode}, "
          #        f"has newsimulationID={hasattr(self, 'newsimulationID')}")

            # 1) If we have no new simulation, this is truly the Initial-only plot -> skip yield
            if not hasattr(self, 'newsimulationID'):
                print("[on_click_nitroTab] No newsimulationID -> skipping readYieldN (Initial N only)")
            else:
                # 2) We *do* have a new run; choose folder by last_run_mode, ignore use_previous
                if run_mode == 'Modified':
                    N_Folder = tempDirISN
                elif run_mode == 'Planned':
                    N_Folder = tempDirN
                else:
                    pass

                # Only call readYieldN if the expected g01 file exists
                g01_path = os.path.join(N_Folder, f"{self.sitename}.g01")
                if os.path.exists(g01_path):
                    print(f"[on_click_nitroTab] Reading yield from {g01_path}")
                    self.readYieldN(N_Folder, run_mode)
                else:
                    print(f"[on_click_nitroTab] g01 not found at {g01_path}; skipping readYieldN")
        except Exception as e:
            print("readYieldN() failed:", e)
        
        # ---------------------------------------------------------
        # Enable Nitrogen controls ONLY when a NEW full-season run
        # has just finished (i.e., this call comes from NFullSimFinished),
        # not when plotting the initial/previous run from populate().
        # full-season done => stop busy and re-enable buttons
        # ---------------------------------------------------------
       #self._stop_busy("Nitrogen simulation finished")
        if (not use_previous) and getattr(self, 'last_run_mode', None) == 'Planned' and N_Folder == tempDirN:
            # Full Season N run just completed
            self.add_button.setEnabled(True)
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.runNInSeason_button.setEnabled(True)
            self.runN_button.setEnabled(True)
        else:
            # For initial/previous run, or for in-season plots:
            # keep whatever disabled state is currently set.
            pass

        
   
      
    
    def WriteIniNitro(self,field_path, field_name,waterStressFlag,nitroStressFlag):
        '''
        Get data from operation, soil_long
        '''
        print(field_path, field_name,waterStressFlag,nitroStressFlag)
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

        for ii,jj in enumerate(operationList):
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
                # End date should be greater than sowing date
                if lcropname == "fallow":
                    EndDate = (pd.to_datetime(jj[2]) + pd.DateOffset(days=365)).strftime('%m/%d/%Y')
            
        site = self.result['site'] 
        lsite = site.iloc[0]
        soil = self.result['soil']  
        lsoil = soil.iloc[0]
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
                popSlab = RowSP/100 * 0.5 * 0.01 * pop  
                rootWeightPerSlab = seedpieceMass * 0.25 * popSlab
            elif lcropname == "soybean":
                fout<<"AutoIrrigate"<<"\n"
                fout<<'%d' %(autoirrigation)<<"\n"
                fout<<"Sowing          Emergence          End	TimeStep(m)"<<"\n"
                fout<<"'%-10s'  '%-10s'  '%-10s'  %d" %(SowingDate,EmergenceDate, EndDate,60)<<"\n"
                popSlab = RowSP/100 * eomult * 0.01 * pop
                rootWeightPerSlab = 0.0275 * popSlab
            elif lcropname == "cotton":
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

    
    def delete_selected_applied_n(self):
        """
        Delete selected Applied N rows from the UI table and DB, then update the Nitrogen Applied display.
        - Deletes DB rows via delete_n_applied(tid, t_exid, date_iso, askUserFlag=False).
        - Removes corresponding rows from the QTableWidget (descending order to avoid index shift).
        - Refreshes displayed total using sum_n_applied_until_date(...).
        """
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            messageUser("Select one or more rows to delete.")
            return

        # resolve ids
        try:
            exid = read_experimentDB_id(self.crop, self.experimentname)
            tid = read_treatmentDB_id(exid, self.treatmentname)
        except Exception as e:
            messageUser("Unable to determine experiment/treatment: " + str(e))
            return
        if tid is None:
            messageUser("Missing treatment id.")
            return

        # collect unique row indices (descending order)
        rows = sorted({idx.row() for idx in sel}, reverse=True)
        if not rows:
            messageUser("No rows selected.")
            return

        deleted = 0
        errors = []
        for r in rows:
            item_date = self.table.item(r, 0)
            if not item_date or not item_date.text().strip():
                errors.append(f"row {r+1}: empty date")
                continue
            date_str = item_date.text().strip()
            parsed = None
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    parsed = pd.to_datetime(date_str, format=fmt)
                    break
                except Exception:
                    parsed = None
            if parsed is None:
                try:
                    parsed = pd.to_datetime(date_str)
                except Exception:
                    parsed = None
            if parsed is None:
                errors.append(f"row {r+1}: bad date '{date_str}'")
                continue
            date_iso = parsed.strftime("%Y-%m-%d")

            # Delete DB entry (no per-row confirmation here)
            ok = delete_n_applied(tid, exid, date_iso, askUserFlag=False)
            if ok:
                try:
                    self.table.removeRow(r)
                except Exception as e:
                    # row removal failed but DB entry deleted — report
                    errors.append(f"{date_iso} (UI remove error)")
                    print("UI removeRow error:", e)
                deleted += 1
            else:
                errors.append(date_iso)

        # Refresh displayed applied N up to in-season date
        try:
            insea_date = self.selInSeadate()
            if insea_date:
                total_applied = sum_n_applied_until_date(tid, insea_date)
            else:
                # fallback: sum all entries (use very large date)
                total_applied = sum_n_applied_until_date(tid, "9999-12-31")
          #  self.numAppllabeledit.setText(str(total_applied))
        except Exception:
            pass

        msg = f"Deleted {deleted} record(s)."
        if errors:
            msg += " Errors: " + ", ".join(errors[:6])
        messageUser(msg)

    
    def update_n_applied(self, mode='merge', notify=True):
        from PyQt5.QtWidgets import QMessageBox, QApplication, QLineEdit

        try:
            exid = read_experimentDB_id(self.crop, self.experimentname)
            tid = read_treatmentDB_id(exid, self.treatmentname)
        except Exception as e:
            if notify:
                messageUser("Unable to determine experiment/treatment: " + str(e))
            return 0, [str(e)]

        if not tid or exid is None:
            if notify:
                messageUser("Missing treatment or experiment id.")
            return 0, ["Missing IDs"]

        
        # Commit any active editor: clear focus + close persistent editors (ensure cell edits are written)
        try:
            fw = QApplication.focusWidget()
            if isinstance(fw, QLineEdit):
                fw.clearFocus()
            QApplication.processEvents()

            model = self.table.model()
            # Close any persistent editors by QModelIndex so the item text is committed to the model
            for r in range(self.table.rowCount()):
                for c in range(self.table.columnCount()):
                    try:
                        idx = model.index(r, c)
                        if self.table.isPersistentEditorOpen(idx):
                            self.table.closePersistentEditor(idx)
                    except Exception:
                        # ignore index/editor closure errors on some Qt builds
                        pass

            # Extra guard: clear table focus to force any remaining editor to commit
            try:
                self.table.clearFocus()
            except Exception:
                pass
            QApplication.processEvents()
        except Exception:
            pass

        rows = self.table.rowCount()
        try:
            insea_date = self.selInSeadate()
            insea_dt = pd.to_datetime(insea_date).normalize() if insea_date else None
            insea_iso = insea_dt.strftime("%Y-%m-%d") if insea_dt is not None else None
        except Exception:
            insea_date = None
            insea_dt = None
            insea_iso = None

        try:
            mgmt_map_all = get_management_n_map(tid) or {}
            mgmt_map_up = get_management_n_map(tid, up_to_date=insea_date) if insea_date else mgmt_map_all
        except Exception:
            mgmt_map_all = {}
            mgmt_map_up = {}

        # Normalize management keys to ISO 'YYYY-MM-DD' strings for reliable comparisons
        def _normalize_map_keys(m):
            out = {}
            for k, v in (m or {}).items():
                try:
                    dt = pd.to_datetime(str(k).strip(), errors='coerce')
                    if pd.isna(dt):
                        continue
                    out[dt.strftime('%Y-%m-%d')] = v
                except Exception:
                    continue
            return out

        mgmt_map_all_iso = _normalize_map_keys(mgmt_map_all)
        mgmt_map_up_iso = _normalize_map_keys(mgmt_map_up)

        # read existing combined map early so we can compare UI input vs DB (avoid prompting when nothing changed)
        try:
            existing_combined_all = get_nitrogen_applied_map(tid, up_to_date=None, t_exid=exid) or {}
        except Exception:
            existing_combined_all = {}

     #   print("existing_combined_all: ", existing_combined_all)
        existing_combined_iso = _normalize_map_keys(existing_combined_all)

      #  print("existing_combined_iso: ", existing_combined_iso)

        # parse UI table into aggregated date->amount map (ISO keys)
        table_map = {}
        parse_errors = []
        for r in range(rows):
            item_date = self.table.item(r, 0)
            item_amount = self.table.item(r, 1)
            if item_date is None or item_amount is None:
                continue
            date_str = item_date.text().strip()
            amount_str = item_amount.text().strip()
            if date_str == "" or amount_str == "":
                continue

            parsed = None
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    parsed = pd.to_datetime(date_str, format=fmt)
                    break
                except Exception:
                    parsed = None
            if parsed is None:
                try:
                    parsed = pd.to_datetime(date_str)
                except Exception:
                    parse_errors.append(f"Row {r+1}: bad date '{date_str}'")
                    continue

            try:
                date_iso = parsed.strftime("%Y-%m-%d")
            except Exception:
                parse_errors.append(f"Row {r+1}: could not format date '{date_str}'")
                continue

            try:
                n_app = float(amount_str.replace(",", ""))
            except Exception:
                parse_errors.append(f"Row {r+1}: bad amount '{amount_str}'")
                continue

            table_map[date_iso] = table_map.get(date_iso, 0.0) + n_app

            # DEBUG: show focus/editor and parsed table_map immediately after parsing UI table
            try:
                fw = QApplication.focusWidget()
           #     print("DEBUG: focus widget:", fw, "type:", type(fw))
                # show any QLineEdit children inside the table (active editors)
                editors = [c for c in self.table.findChildren(QLineEdit)]
             #   print("DEBUG: active editors found:", editors)
             #   print("DEBUG: parsed table_map:", table_map)
              #  print("DEBUG: rows, table.rowCount() =", rows, self.table.rowCount())
            except Exception as _:
                pass

        # conflict handling: only consider table dates that were actually added/changed (compare to DB)
        override_dates = set()
        skip_table_dates = set()
        try:
            if mode != 'Planned':
                for dt_iso in list(table_map.keys()):
                    # Only conflict on the in-season date itself AND only if the UI value differs from existing_combined (user changed/added)
                    if insea_iso and dt_iso == insea_iso and dt_iso in mgmt_map_all_iso:
                        # Prefer to compare UI value against scheduled management (mgmt_map_all_iso).
                        # If the UI value equals the scheduled mgmt value then there's nothing to prompt for.
                        # If the UI value differs from scheduled mgmt (even when DB already contains the same ES value),
                        # prompt the user to keep scheduled (Yes) or override (No).
                        try:
                            mgmt_val = float(mgmt_map_all_iso.get(dt_iso, 0.0))
                        except Exception:
                            mgmt_val = 0.0
                        try:
                            ui_val = float(table_map.get(dt_iso, 0.0))
                        except Exception:
                            ui_val = 0.0

                        # If UI equals scheduled management, treat as no change (skip)
                        if abs(ui_val - mgmt_val) < 1e-6:
                            skip_table_dates.add(dt_iso)
                            continue

                        # If prompts are suppressed (automated in-season run) keep planned by default
                        # If prompts are suppressed (automated in-season run), respect any explicit override
                        # the user made earlier (stored in self.override_dates). If no prior override
                        # exists, keep planned by default.
                        if getattr(self, 'suppress_conflict_prompts', False) and not notify:
                            try:
                                prior_overrides = getattr(self, 'override_dates', set())
                                if dt_iso in prior_overrides:
                                    # User previously chose "No" for this date — honor the override.
                                    override_dates.add(dt_iso)
                                    # ensure persisted override set contains this date (defensive)
                                    try:
                                        if not hasattr(self, 'override_dates'):
                                            self.override_dates = set()
                                        self.override_dates.add(dt_iso)
                                    except Exception:
                                        pass
                                    # do NOT skip the table date — let final_map include the UI value
                                else:
                                    # no prior override recorded — keep planned by default for automated runs
                                    skip_table_dates.add(dt_iso)
                                    continue
                            except Exception:
                                # In case of any error, default to keeping planned (safe)
                                skip_table_dates.add(dt_iso)
                                continue

                        if notify:
                            prompt = (
                                f"The In-Season date ({insea_dt.strftime('%Y-%m-%d')}) already has a scheduled N application.\n\n"
                                "Choose action:\n"
                                "Yes = Keep the scheduled (planned) application and ignore the added entry for that date.\n"
                                "No  = Add/override the scheduled application with the new value entered in the table."
                            )
                            reply = QMessageBox.question(self, "In-Season application conflict", prompt,
                                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                            if reply == QMessageBox.Yes:
                                # Keep planned: drop the UI entry for that date so mgmt value remains unchanged
                                skip_table_dates.add(dt_iso)
                            else:
                                # Add/override: mark this date to override management when building final_map
                                override_dates.add(dt_iso)
                                # persist override choice so prepareandexecuteNitro can remove mgmt line
                                try:
                                    if not hasattr(self, 'override_dates'):
                                        self.override_dates = set()
                                    self.override_dates.add(dt_iso)
                                except Exception:
                                    pass
                        else:
                            # automated call (notify==False) -> keep planned by default
                            skip_table_dates.add(dt_iso)
        except Exception:
            # non-critical: proceed without special handling if prompt fails
            pass

        # Remove skipped table dates from table_map so they don't get added
        for d in skip_table_dates:
            table_map.pop(d, None)

        # If user pressed Update without adding any rows (no ES/UI entries) warn and do nothing.
        # Allow 'full_manage' mode to proceed because that's intended to persist management-only state.
        if not table_map and mode != 'Planned':
            if notify:
                QMessageBox.warning(self, "No data to update", "No nitrogen application rows found in the table. Please Add Row and enter data before pressing Update.")
            return 0, ["No data"]

        if parse_errors and notify:
            messageUser("Some rows skipped: " + "; ".join(parse_errors[:5]))

        # full_manage cleanup (remove stale ES DB rows before writing mgmt-only)
        if mode == 'Planned':
            try:
                mgmt_keys = set(mgmt_map_all_iso.keys())
                existing_keys = set(_normalize_map_keys(existing_combined_all).keys())
                stale_es = existing_keys - mgmt_keys
                for d_iso in sorted(stale_es):
                    try:
                        delete_n_applied(tid, exid, d_iso, askUserFlag=False)
                    except Exception:
                        pass
            except Exception:
                pass
            # persist normalized mgmt_map_all_iso values
            final_map = {d_iso: float(v) for d_iso, v in mgmt_map_all_iso.items()}
        else:
            # build affected dates from normalized mgmt and table_map (both ISO keyed)
            affected_dates = set(existing_combined_iso.keys()) | set(mgmt_map_all_iso.keys()) | set(table_map.keys())
            final_map = {}
            for d_iso in sorted(affected_dates):
                # If user explicitly chose to override this date, do not add mgmt value.
                if d_iso in override_dates:
                    final_map[d_iso] = float(table_map.get(d_iso, 0.0))
                else:
                    mgmt_val = float(mgmt_map_all_iso.get(d_iso, 0.0))
                    table_val = float(table_map.get(d_iso, 0.0))
                    final_map[d_iso] = mgmt_val + table_val

        # --- max-N validation: compute mgmt_up_total + ES_from_inseason ---
        try:
            sim_id = getattr(self, 'prevsimulationID', None) or getattr(self, 'newsimulationID', None)
            max_allowed = get_max_allowed_n(tid, exid, simulation_id=sim_id)
            if max_allowed is not None:
                mgmt_up_total = 0.0
                for v in mgmt_map_up_iso.values():
                    try:
                        mgmt_up_total += float(v)
                    except Exception:
                        continue

                # compute ES only from UI table entries on/after in-season date (respect skip/override choices)
                es_from_insea = 0.0
                for d_iso, ui_val in (table_map or {}).items():
                    try:
                        d_dt = pd.to_datetime(d_iso).normalize()
                    except Exception:
                        d_dt = None
                    if (insea_dt is None) or (d_dt is not None and d_dt >= insea_dt):
                        try:
                            ui_f = float(ui_val)
                        except Exception:
                            ui_f = 0.0
                        if ui_f > 0:
                            es_from_insea += ui_f

                candidate_total = mgmt_up_total + es_from_insea
                try:
                    max_allowed_f = float(max_allowed)
                except Exception:
                    max_allowed_f = None

                if max_allowed_f is not None and candidate_total > max_allowed_f:
                    if not notify:
                        return 0, [f"max_exceeded_candidate: {candidate_total} > {max_allowed_f}"]
                    prompt = (f"Total N = management up-to-inseason ({mgmt_up_total:.2f} kg/ha) + "
                              f"ES from in-season ({es_from_insea:.2f} kg/ha) = {candidate_total:.2f} kg/ha.\n"
                              f"Allowed maximum is {max_allowed_f:.2f} kg/ha.\n\nProceed and save anyway?")
                    reply = QMessageBox.question(self, "Confirm N exceeds limit", prompt,
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return 0, [f"max_exceeded_candidate: {candidate_total} > {max_allowed_f}"]
        except Exception:
            pass
        # DEBUG: inspect maps right before DB persistence
       # try:
        #    print("DEBUG: table_map =", table_map)
         #   print("DEBUG: skip_table_dates =", sorted(list(skip_table_dates)))
          #  print("DEBUG: override_dates =", sorted(list(getattr(self, 'override_dates', set()))))
           # print("DEBUG: existing_combined_iso =", sorted(list(existing_combined_iso.keys())))
           # print("DEBUG: mgmt_map_all_iso =", sorted(list(mgmt_map_all_iso.keys())))
           # print("DEBUG: affected_dates =", sorted(list(affected_dates)))
          #  print("DEBUG: final_map (to persist) =", {k: float(v) for k, v in final_map.items()})
     #   except Exception as _:
        #    pass

        # Persist final_map into DB
        inserted = 0
        db_errors = []
        for date_iso in sorted(final_map.keys()):
            n_app = final_map.get(date_iso, 0.0)
            try:
                ok = insert_or_update_nitrogen_applied(tid, exid, date_iso, n_app)
            except Exception as e:
                ok = False
                db_errors.append((date_iso, str(e)))
            else:
                if not ok:
                    try:
                        ok2 = insert_or_update_nitrogen_applied(tid, exid, date_iso, n_app)
                    except Exception as e2:
                        ok2 = False
                        db_errors.append((date_iso, str(e2)))
                    if not ok2:
                        db_errors.append((date_iso, "insert_or_update returned False"))
                    ok = ok2
            if ok:
                inserted += 1
        if notify:
            # Use explicit QMessageBox types so the dialog icon/title matches intent
            if inserted > 0 and not db_errors:
                QMessageBox.information(self, "Success", f"Database has been successfully updated.")
            elif inserted > 0 and db_errors:
                # partial success — show warning with short error summary
                short = "; ".join([f"{d}: {err}" for d, err in db_errors[:6]])
                QMessageBox.warning(self, "Partial Success", f"Some errors: {short}")
            else:
                QMessageBox.information(self, "Info", "No records inserted.")

        return inserted, db_errors
        
        
    
    def readYieldN(self, N_Folder, run_mode):
       
        exid = read_experimentDB_id(self.crop, self.experimentname)
        tid = read_treatmentDB_id(exid, self.treatmentname)
        plantDensity = getPlantDensity(tid)
     
        filename = str(N_Folder) + "\\" + self.sitename + ".g01"

        if self.crop == "potato":
            potato_df =   pd.read_csv(filename, usecols = ['tuberDM'])
            last_ptato_df = potato_df.tail(1)      
            agroDataTuple = last_ptato_df['tuberDM']
            self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                
        elif self.crop == "soybean":
            soy_df =   pd.read_csv(filename) 
            soy_df.columns = [c.strip() for c in soy_df.columns]
            last_soy_df = soy_df['seedDM'].tail(1)
            agroDataTuple = last_soy_df
          #  print(plantDensity)
            self.Yield = agroDataTuple.iloc[0]*plantDensity*10	
                       
                
        elif self.crop == "maize":                        
            corn_df = pd.read_csv(filename) #, usecols = ['earDM']) #, 'date', 'Note     '])
            # last_corn_df = corn_df.tail(1)    
            last_corn = corn_df['earDM'].tail(1) 
            agroDataTuple = last_corn * 0.86   
            self.Yield = agroDataTuple.iloc[0]*plantDensity*10
                
        elif self.crop == "cotton":
            cotton_df =   pd.read_csv(filename)  
            last_cotton_df = cotton_df.tail(1) 
            agroDataTuple = last_cotton_df['       Yield']
            self.Yield = agroDataTuple.iloc[0]
                       
        else:
            pass	

      #  print("Yield is: ", self.Yield)
        if hasattr(self, 'newsimulationID') and run_mode == 'Planned':
            self.simOutputN0 = "Yield (Planned): " + str(round(self.Yield))  + " kg/ha"   
            self.outputDetailslabelN.setText(self.simOutputN0) 
        elif hasattr(self, 'newsimulationID') and run_mode == 'Modified':
            self.simOutputN1 = "Yield (Modified): " + str(round(self.Yield))  + " kg/ha"
            self.outputDetailslabelN_mod.setText(self.simOutputN1) 
        else:
            pass
         
