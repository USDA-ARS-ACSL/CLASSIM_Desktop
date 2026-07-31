import matplotlib
#matplotlib.use('TkAgg') #backend
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
from datetime import date, timedelta, datetime
from time import mktime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt  # <--- Added correct import for Qt constants
from PyQt5.QtWidgets import QWidget, QTabWidget, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QPushButton, \
                            QSpacerItem, QSizePolicy, QHeaderView, QRadioButton, QButtonGroup, QFrame, QFormLayout, QScrollArea, QCheckBox, \
                            QGridLayout, QGroupBox, QHeaderView,  QMenu, QAction, QTextEdit, QTreeWidgetItem # <--- Added missing classes
from CustomTool.custom1 import *
from CustomTool.UI import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from CustomTool.genDictOutput import *
#
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pandas.plotting import register_matplotlib_converters
from shutil import copyfile
register_matplotlib_converters()
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from PyQt5.QtGui import QPixmap

#global classimDir
#global runDir

classimDir = getClassimDir()
runDir = os.path.join(classimDir,'run')

'''
Contains 1 class.
1). Class Output_Widget is derived from Qwidget. It is initialed and called by Tabs.py -> class Tabs_Widget. It handles 
    all the features of OUTPUT Tab on the interface. It has signal slot mechanism. It does interact with the 
    DatabaseSys\Databasesupport.py for all the databases related task.
    Pretty generic and self explanotory methods. 
    Refer baseline classes at http://pyqt.sourceforge.net/Docs/PyQt5/QtWidgets.html#PyQt5-QtWidgets

    It has few extra imports like for ANIMATION support. Like JSAnimation for spatial and movie for G03 outputs. 
    PANDA dataframe for grid processes.
    It also has sub-tabs. Idea is to have G[0,1,2,3,4,5,6] output files shown in individual sub-tabs.

    We are also working idea of comparing 2 (or more) simulations. Currently focusing on G01,G03 outputs. But this 
    idea can easily be spread to cover other output types.
    Dr.Dennis is working on consolidating some of the other output files.
'''


class RotOutput_Widget(QWidget):
    # Add a signal    
    def __init__(self):
        super(RotOutput_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
     #   self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
     #   self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("output")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.tab_summary = QTextEdit("Choose rotation by checking from the list box.")                
        self.tab_summary.setReadOnly(True)        
        # no scroll bars
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)         
        self.tab_summary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum) # horizontal, vertical
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)      
        self.tab_summary.setMaximumHeight(40) # need it
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)
        self.faqtree.setVisible(False)

        urlLink="<a href=\"https://youtu.be/NahJuss_hlA\">Click here \
                to watch the Rotation Output Tab Video Tutorial</a><br>"
        self.rotationoutVidlabel=QLabel()
        self.rotationoutVidlabel.setOpenExternalLinks(True)
        self.rotationoutVidlabel.setText(urlLink)

        self.vl1 = QVBoxLayout()
        self.hl1 = QHBoxLayout()
        self.vl1.setAlignment(QtCore.Qt.AlignTop)        
        self.mainlayout1 = QGridLayout()
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vl1.setContentsMargins(0,0,0,0)
        self.vl1.setSpacing(1)
        self.vl1.addWidget(self.tab_summary)
        self.vl1.addWidget(self.rotationoutVidlabel)
        self.vl1.addWidget(self.helpcheckbox)

        self.table2 = QTableWidget()
        self.plotoutput = QPushButton("Select Rotation")
        self.deleteSim = QPushButton("Delete Rotation")

        self.buttonhlayout = QVBoxLayout()
        self.buttonhlayout.addWidget(self.plotoutput)
        self.buttonhlayout.addWidget(self.deleteSim)
        self.buttonhlayout.addStretch(1)

        self.display1 = QTabWidget()
        self.statistic_toollist = ['hourly', 'daily']

        # Table setup
        self.table2.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table2.setFixedHeight(150)                      # or whatever height you prefer
        self.table2.setSizePolicy(QSizePolicy.Expanding,
                                  QSizePolicy.Fixed)
        self.table2.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table2.setAlternatingRowColors(True)
        self.table2.verticalHeader().hide()

        self.error_tuplelist = []
        self.populate()

        headers = [
            'RotID', 'Site', 'Station Name', 'Weather', 'Soil',
            'SimID', 'Treatment', 'Start\nYear', 'End\nYear',
            'Water\nStress', 'Nitrogen\nStress', 'Temp\nVariance (oC)',
            'Rain\nVariance (%)', 'CO2\nVariance (ppm)'
        ]
        self.table2.setColumnCount(len(headers))
        self.table2.setHorizontalHeaderLabels(headers)

        header = self.table2.horizontalHeader()
        # Default: size to contents
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        # Let the “Treatment” column (index 6) stretch with the window
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        # Use its content width as a minimum so it never shrinks below that
        self.table2.resizeColumnsToContents()
        col6_width = header.sectionSize(6)
        

        self.plotoutput.clicked.connect(self.on_click_table_widget)
        self.deleteSim.clicked.connect(self.on_deletebuttonclick)

        self.hl1.addWidget(self.table2)
        self.hl1.addLayout(self.buttonhlayout)
        self.vl1.addLayout(self.hl1)
        self.vl1.addWidget(self.display1)
        self.vl1.addStretch(1)
        self.display1.setVisible(False)
        self.mainlayout1.addLayout(self.vl1,0,0)
        self.mainlayout1.setColumnStretch(0,3)
        self.mainlayout1.addWidget(self.faqtree,0,4)
        
        #add a scroll bar to window
        self.scrollArea = QtWidgets.QScrollArea() # self.centralWidget)
        self.scrollContent = QtWidgets.QWidget(self.scrollArea)
        self.scrollContent.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.scrollContent.setLayout(self.mainlayout1)
        self.scrollArea.setLayout(self.mainlayout1)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.scrollArea)
        self.setLayout(self.layout)

        # Set graphic background to white and foreground to black
        pg.setConfigOption('background','w')
        pg.setConfigOption('foreground','k')


    def make_connection(self,rotation_object):
        rotation_object.rotationUpSig.connect(self.populate)

    def populate(self):
        rlist = extract_pastrunsidDB(-99)
 
        # When setRowCount is set to 0, the table gets refreshed.
        self.table2.setRowCount(0)
        self.table2.setRowCount(len(rlist))
        self.table2.setColumnCount(14)
        self.table2.simGrp = QButtonGroup()
        for row1 in range(len(rlist)): 
            for col in range(len(rlist[row1])):
                if(row1 == 0 or rlist[row1][0] != rlist[row1-1][0]):
                    if col == 0:
                        radioitem = QRadioButton(str(rlist[row1][col]))
                        self.table2.simGrp.addButton(radioitem,col)
                        self.table2.setCellWidget(row1,col,radioitem)
                    else:
                        self.table2.setItem(row1,col,QTableWidgetItem(str(rlist[row1][col])))
                else:
                    if col < 5:
                        self.table2.setItem(row1,col,QTableWidgetItem())
                    else:
                        self.table2.setItem(row1,col,QTableWidgetItem(str(rlist[row1][col])))


    def on_click_plotPlantTab(self):
        LINECOLORS = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        checkedVar = []
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                for key, value in self.finalVarDescDict.items():
                    if checkbox.text() == value:
                         checkedVar.append(key)

        data_df = pd.DataFrame([])
        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            t1 = pd.DataFrame([])
            if self.cropArr[runNum] != "fallow":
                self.g01Tablename = "g01_" + self.cropArr[runNum]
                t1 = extract_cropOutputData(self.g01Tablename,self.simIDArr[runNum])
                tableID = self.g01Tablename + "_id"
                if self.cropArr[runNum] == "maize":
                    t1.drop(columns=[tableID,'jday','Note'], inplace=True)
                    t1 = t1.add_suffix('__mai')
                    t1.rename(columns={'Date_Time__mai':'Date_Time'}, inplace=True)
                    t1.loc[t1.SolRad__mai <= 0,'SolRad__mai'] = np.nan
                    t1['PFD__mai'] = (t1['PFD__mai']*3600)/1000000
                elif self.cropArr[runNum] == "potato":
                    t1.drop(columns=[tableID,'jday'], inplace=True)
                    t1 = t1.add_suffix('__pot')
                    t1.rename(columns={'Date_Time__pot':'Date_Time'}, inplace=True)
                    t1.loc[t1.SolRad__pot <= 0,'SolRad__pot'] = np.nan
                    t1['PFD__pot'] = (t1['PFD__pot']*3600)/1000000
                elif self.cropArr[runNum] == "soybean":
                    t1.drop(columns=[tableID,'jday'], inplace=True)
                    t1 = t1.add_suffix('__soy')
                    t1.rename(columns={'Date_Time__soy':'Date_Time'}, inplace=True)
                    t1.loc[t1.SolRad__soy <= 0,'SolRad__soy'] = np.nan
                    t1['PFD__soy'] = (t1['PFD__soy']*3600)/1000000
                elif self.cropArr[runNum] == "cotton":
                    t1.drop(columns=[tableID], inplace=True)
                    t1 = t1.add_suffix('__cot')
                    t1.rename(columns={'Date_Time__cot':'Date_Time'}, inplace=True)
                    t1.loc[t1.SRad__cot <= 0,'SRad__cot'] = np.nan
            data_df = data_df.append(t1,ignore_index=True) 

        new_df = data_df['Date_Time'].str.split(' ', n=1, expand=True)
        data_df['Date'] = new_df[0]
        data_df['Date'] = pd.to_datetime(data_df['Date'])
        for key in self.finalVarFuncDict:
            data_df[key] = pd.to_numeric(data_df[key],errors='coerce')
        data_df_grouped = data_df.groupby(['Date'], as_index=False).agg(self.finalVarFuncDict)
        data_df_grouped.rename(columns={'Date':'Date_Time'}, inplace=True)
        data_df_grp = data_df_grouped.set_index('Date_Time').resample('1D').asfreq().fillna(0)                     
        data_df_grp.reset_index(inplace=True)
        tmstampArray = np.array([row['Date_Time'].timestamp() for index, row in data_df_grp.iterrows()])

        self.plantGraphWidget.clear()
        self.plantGraphWidget.setLabel("bottom", "Date")
        self.plantGraphWidget.showGrid(x=True, y=True)
        self.legend = self.plantGraphWidget.addLegend()
        
        i = 0
        maxY = 0
        minY = 0
        for var in checkedVar:
            color = LINECOLORS[i]
            pen = pg.mkPen(color,width=3)
            maxY = max(data_df_grp[var]) if maxY < max(data_df_grp[var]) else maxY
            minY = min(data_df_grp[var]) if minY > min(data_df_grp[var]) else minY
            self.plantGraphWidget.plot(x=tmstampArray,y=np.array(data_df_grp[var]), name=self.finalVarDescUnitDict[var], pen=pen)
            if i < 6:
                i = i + 1
            else:
                i = 0

        # set Y  and X range
        self.plantGraphWidget.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(minY*1.05,maxY*1.05),padding=0)
        self.plantGraphWidget.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=minY*1.05,yMax=maxY*1.05)


    def on_click_soilCNTab(self):
        LINECOLORS = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        checkedVar = []
        for i, checkbox in enumerate(self.soilCheckboxes):
            if checkbox.isChecked():
                for key, value in self.finalSoilCNVarDescDict.items():
                    if checkbox.text() == value:
                         checkedVar.append(key)

        # Create dictionary to hold dataframes
        data_df = pd.DataFrame([])
        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            t7 = pd.DataFrame([])
            self.g07Tablename = "g07_" + self.cropArr[runNum]
            t7 = extract_cropOutputData(self.g07Tablename,self.simIDArr[runNum])
            # drop the id column 
            t7 = t7.drop(columns=[self.g07Tablename + "_id"])
            # Read area from geometry table
            geo_df = readGeometrySimID(self.simIDArr[runNum])
            # Merge geo_df dataframe to t7 dataframe
            t7 = pd.merge(geo_df,t7, how='inner', left_on=['X','Y'], right_on=['X','Y'])
            # each simulation has its own rowSP and eomult, so here we are storing these values
            t7['eomult'] = self.eomultArr[runNum]
            t7['rowSP'] = self.rowSPArr[runNum]
            data_df = data_df.append(t7,ignore_index=True) 

        # Rename data_df to t7
        t7 = data_df
        new_df = t7['Date_Time'].str.split(' ', n=1, expand=True)
        # Get only date
        t7['Date'] = new_df[0]
        t7['Date'] = pd.to_datetime(t7['Date'])
        t7 = t7.drop(columns=["Date_Time"])
        for key in t7:
            if key != "Date":
                t7[key] = pd.to_numeric(t7[key],errors='coerce')
        t7 = t7.fillna(0)

        # Since 2dsoil assigns Y values from the max depth ->0 where the surface is the maximum Depth and the bottom
        # of the profile is 0, we have to reverse this for the layer file. Thus we subtract the max depth from all the Y's'
        maxY = max(t7['Y'])
        t7['Y'] = maxY-t7['Y']

        #values are now total ugrams in the domain area (1/2 row spacing *1 cm), scale to kg/ha
        t7['fact']=1.0/(0.01*t7['rowSP']/100.0*t7['eomult']) # m2 area if the slab
        t7['fact']=t7['fact']*10000./1000./1000./1000.  #scale area

        # First group every node by Date, X and Y
        # average the 24 hourly periods over each day
        t7 = t7.groupby(['Date','X','Y'], as_index=False).agg({'Area':['mean'],'Humus_N':['mean'],'Humus_C':['mean'],'Litter_N':['mean'],
                                                       'Litter_C':['mean'],'Manure_N':['mean'],'Manure_C':['mean'],
                                                       'Root_N':['mean'],'Root_C':['mean'],'fact':['mean']})

        t7 = t7.drop(columns=["X","Y"])
        t7.columns = ["_".join(x) for x in t7.columns.ravel()]
        t7.rename(columns={'Date_':'Date'}, inplace=True)

        # Multiply by area to get total g in each node
        for key in t7:
            if (key != "Date" and key != "Area_mean" and key != "fact"):
                t7[key] = t7[key]*t7['Area_mean']
        t7 = t7.drop(columns=["Area_mean"])

        # Group by Date adding all nodal values
        t7 = t7.groupby(['Date'], as_index=False).agg({'Humus_N_mean':['sum'],'Humus_C_mean':['sum'],'Litter_N_mean':['sum'],
                                                       'Litter_C_mean':['sum'],'Manure_N_mean':['sum'],'Manure_C_mean':['sum'],
                                                       'Root_N_mean':['sum'],'Root_C_mean':['sum'],'fact_mean':['mean']})
        t7.columns = ["_".join(x) for x in t7.columns.ravel()]
        t7.rename(columns={'Date_':'Date_Time'}, inplace=True)

        tmstampArray = np.array([row['Date_Time'].timestamp() for index, row in t7.iterrows()])
        #values are now total ugrams in the domain area (1/2 row spacing *1 cm), scale to kg/ha
        for column in t7.columns:
          if column in ['Humus_N_mean_sum','Humus_C_mean_sum','Litter_N_mean_sum','Litter_C_mean_sum','Manure_N_mean_sum','Manure_C_mean_sum','Root_N_mean_sum','Root_C_mean_sum']:
              t7[column]=t7[column]*t7['fact_mean_mean']                                         
              
        self.soilCNWidget.clear()
        self.soilCNWidget.setLabel("bottom", "Date")
        self.soilCNWidget.showGrid(x=True, y=True)
        self.legend = self.soilCNWidget.addLegend()
        
        i = 0
        maxY = 0
        minY = 0
        for var in checkedVar:
            color = LINECOLORS[i]
            pen = pg.mkPen(color, width=3)
            maxY = max(t7[var+'_mean_sum']) if maxY < max(t7[var+'_mean_sum']) else maxY
            minY = min(t7[var+'_mean_sum']) if minY > min(t7[var+'_mean_sum']) else minY
            self.soilCNWidget.plot(x=tmstampArray,y=np.array(t7[var+'_mean_sum']), name=self.finalSoilCNVarDescUnitDict[var], pen=pen)
            if i < 6:
                i = i + 1
            else:
                i = 0
        # set Y  and X range
        self.soilCNWidget.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(minY*1.05,maxY*1.05),padding=0)
        self.soilCNWidget.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=minY*1.05,yMax=maxY*1.05)


    def on_click_plotSoil2DTab(self):
        date = self.comboDate.currentText()
        data_df = pd.DataFrame([])
        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            t3 = pd.DataFrame([])
            self.g03Tablename = "g03_" + self.cropArr[runNum]
            t3 = extract_cropOutputData(self.g03Tablename,self.simIDArr[runNum])
            tableID = self.g03Tablename + "_id"
            t3.drop(columns={tableID}, inplace=True)
            data_df = data_df.append(t3,ignore_index=True) 
        new_df = data_df['Date_Time'].str.split(' ', n=1, expand=True)
        data_df['Date'] = new_df[0]

        for key in self.varSoilwhn2DDescUnitDict:
            data_df[key] = pd.to_numeric(data_df[key],errors='coerce')
        data_df = data_df.fillna(0)
        data_df_grouped = data_df.groupby(['Date','X','Y'], as_index=False).agg(self.varSoilwhn2DFuncDict)
        data_df_grouped.rename(columns={'Date':'Date_Time'}, inplace=True)
        df_collection = data_df_grouped.loc[data_df_grouped['Date_Time'] == date].filter(['hNew','thNew','NO3N','Temp','X','Y'],axis=1)

        rows = 1
        columns = 4
        i = 1

        ## Create image
        self.soilwhnTab.fig.clear()
        self.soilwhnTab.canvas.flush_events()
        for var, desc in self.varSoilwhn2DDescUnitDict.items():
            title = desc
            new_df = df_collection.filter(['X','Y',var],axis=1)
            new_arr = new_df.values
            colorMap = "cool"
            if var == "hNew":
                colorMap = "cool_r"
                new_df[var] = new_df[var].abs()
            nx = new_df['X'].nunique()
            ny = new_df['Y'].nunique()
            x = new_arr[:,0].reshape(nx,ny)
            y = new_arr[:,1].reshape(nx,ny)
            z = new_arr[:,2].reshape(nx,ny)
            maxY = max(map(max, y))
            y = maxY - y
            self.soilwhnTab.ax = self.soilwhnTab.fig.add_subplot(rows, columns, i)
            self.soilwhnTab.ax.invert_yaxis()
            levels = np.linspace(z.min(), z.max(),10)
            cf = self.soilwhnTab.ax.contourf(x, y, z, levels=levels, cmap=colorMap)   
            if var == 'thNew' or var == 'Temp':
                cb = self.soilwhnTab.fig.colorbar(cf, ax=self.soilwhnTab.ax,  shrink=0.9, format='%.2f')
            else:
                cb = self.soilwhnTab.fig.colorbar(cf, ax=self.soilwhnTab.ax,  shrink=0.9)
            if var == "hNew":
                cb.ax.invert_yaxis()
            cb.ax.tick_params(labelsize=7)
            self.soilwhnTab.ax.set_title(title, size="medium")
            self.soilwhnTab.ax.set_ylabel('Depth (cm)')
            if i > 1:
                self.soilwhnTab.ax.get_yaxis().set_visible(False)
            plt.tight_layout()
            self.soilwhnTab.canvas.draw()
            plt.tight_layout()
            i = i + 1

            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.exportSurfaceRot)

    def exportSurfaceRot(self, rotevent):
        self.rotfig=os.path.join(runDir,'ContourSurfaceRot.png')
        plt.savefig(self.rotfig)
        self.rotpixmap = QPixmap(self.rotfig)
        self.rotlabel = QLabel()
        self.rotlabel.setPixmap(self.rotpixmap)
        rotmenu = QMenu(self)
        rotexportsurfImage = QAction('Export', self)  
        rotmenu.addAction(rotexportsurfImage)
        sim_dir = os.path.join(runDir,self.simIDArr[0])
        rotexportsurface_path = os.path.join(sim_dir,'PlantSoil2DRot.png')
        if not os.path.exists(rotexportsurface_path):
            rotexportsurfImage.triggered.connect(lambda: self.rotpixmap.save(rotexportsurface_path))
            rotmenu.exec_(self.mapToGlobal(rotevent))
        else:
            pass
        os.remove(self.rotfig)


    def on_click_rootTab(self):
        date = self.comboDateRoot.currentText()

        data_df = pd.DataFrame([])
        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            t4 = pd.DataFrame([])
            if self.cropArr[runNum] != "fallow":
                self.g04Tablename = "g04_" + self.cropArr[runNum]
                t4 = extract_cropOutputData(self.g04Tablename,self.simIDArr[runNum])
                tableID = self.g04Tablename + "_id"
                t4.drop(columns=[tableID], inplace=True)
            data_df = data_df.append(t4,ignore_index=True) 

        new_df = data_df['Date_Time'].str.split(' ', n=1, expand=True)
        data_df['Date'] = new_df[0]
        data_df['RDenM'] = pd.to_numeric(data_df['RDenM'],errors='coerce')
        data_df['RDenY'] = pd.to_numeric(data_df['RDenY'],errors='coerce')
        data_df['RMassM'] = pd.to_numeric(data_df['RMassM'],errors='coerce')
        data_df['RMassY'] = pd.to_numeric(data_df['RMassY'],errors='coerce')
        # Creating RDenT and RMassT variables
        data_df['RDenT'] = data_df['RDenM'] + data_df['RDenY']
        data_df['RMassT'] = data_df['RMassM'] + data_df['RMassY']
        data_df_grouped = data_df.groupby(['Date','X','Y'], as_index=False).agg(self.varRootFuncDict)
        data_df_grouped.rename(columns={'Date':'Date_Time'}, inplace=True)
        df_collection = data_df_grouped.loc[data_df_grouped['Date_Time'] == date].filter(['RDenT','RMassT','X','Y'],axis=1)

        rows = 1
        columns = 2
        i = 1

        ## Create image
        self.rootTab.fig.clear()
        self.rootTab.canvas.flush_events()
        for var, desc in self.varRootDescUnitDict.items():
            title = desc
            new_df = df_collection.filter(['X','Y',var],axis=1)
            new_df[var] = new_df[var].apply(np.log10)
            new_arr = new_df.values
            colorMap = "cool"
            nx = new_df['X'].nunique()
            ny = new_df['Y'].nunique()
            x = new_arr[:,0].reshape(nx,ny)
            y = new_arr[:,1].reshape(nx,ny)
            z = new_arr[:,2].reshape(nx,ny)
            maxY = max(map(max, y))
            y = maxY - y
            self.rootTab.ax = self.rootTab.fig.add_subplot(rows, columns, i)
            self.rootTab.ax.invert_yaxis()
            levels = np.linspace(z.min(), z.max(),10)
            cf = self.rootTab.ax.contourf(x, y, z, levels=levels, cmap=colorMap)   
            if var == 'RDenT':
                cb = self.rootTab.fig.colorbar(cf, ax=self.rootTab.ax,  shrink=0.9, format='%.2f')
            else:
                cb = self.rootTab.fig.colorbar(cf, ax=self.rootTab.ax,  shrink=0.9)
            cb.ax.tick_params(labelsize=7)
            self.rootTab.ax.set_title(title, size="medium")
            self.rootTab.ax.set_ylabel('Depth (cm)')
            if i > 1:
                self.rootTab.ax.get_yaxis().set_visible(False)
            plt.tight_layout()
            self.rootTab.canvas.draw()
            plt.tight_layout()
            i = i + 1

            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.export2DRootRot)

    def export2DRootRot(self, rootrotevent):
        self.rootrotfig=os.path.join(runDir,'ContourRot.png')
        plt.savefig(self.rootrotfig)
        self.rootrotpixmap = QPixmap(self.rootrotfig)
        self.rootrotlabel = QLabel()
        self.rootrotlabel.setPixmap(self.rootrotpixmap)
        rootrotmenu = QMenu(self)
        rootrotexportImage = QAction('Export', self)   
        rootrotmenu.addAction(rootrotexportImage)  
        sim_dir = os.path.join(runDir,self.simIDArr[0])
        rotexport2Droot_path = os.path.join(sim_dir,'RDentandRMassRot.png')
        if not os.path.exists(rotexport2Droot_path):
            rootrotexportImage.triggered.connect(lambda: self.rootrotpixmap.save(rotexport2Droot_path))
            rootrotmenu.exec_(self.mapToGlobal(rootrotevent))
        else:
            pass
        os.remove(self.rootrotfig)
    pd.set_option('display.max_rows', None)

    def on_click_plotSurfChaTab(self):
        checkedVar = []
        LINECOLORS = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        SEASONAL_COLS = ['SeasPSoEv', 'SeasASoEv', 'SeasPTran', 'SeasATran', 'SeasRain', 'SeasInfil']

        for i, checkbox in enumerate(self.surfChaCheckboxes):
            if checkbox.isChecked():
                for key, value in self.varSurfChaDescDict.items():
                    if checkbox.text() == value:
                         checkedVar.append(key)

        data_df = pd.DataFrame([])
        rot_Irrig_df = pd.DataFrame([])

        # Loop through each run model to give detail information about each run
        t51 = []
        t51_max = []

        data_df_mid = pd.DataFrame([])
        for runNum in range(len(self.simIDArr)):
          #  print(runNum)
            t5 = pd.DataFrame([])
            self.g05Tablename = "g05_" + self.cropArr[runNum]
            exid = read_experimentDB_id(self.cropArr[runNum],self.expArr[runNum])
            tid = read_treatmentDB_id(exid,self.treatArr[runNum])
            plantDensity = getPlantDensity(tid)
            t5 = extract_cropOutputData(self.g05Tablename,self.simIDArr[runNum])

            tableID = self.g05Tablename + "_id"
            t5.drop(columns={tableID}, inplace=True)
            # Converting from ugco2/plant to kg/ha
            t5['CO2Flux'] = (t5['CO2Flux']/10)
            t5['O2Flux'] = (t5['O2Flux']/10)

            t5['TotIrrig']  = 0

            t5['Date_Time'] = pd.to_datetime(t5['Date_Time'])

            # Check if the data is hourly or daily
            time_diff = t5['Date_Time'].diff().mean()

            if time_diff == pd.Timedelta(hours=1):
                print('Data is hourly')
                daily_data = t5.resample('D', on='Date_Time').mean().reset_index()    
                print(type(data_df))
            elif time_diff == pd.Timedelta(days=1):
                print('Data is daily')
                daily_data = t5.resample('D', on='Date_Time').mean().reset_index()    
                print(type(data_df))
            else:
                print('Data is neither hourly nor daily')
       
            daily_data.columns.values[0] = 'Date'
           # print(daily_data)

            o_t_exid = getTreatmentID(self.treatArr[runNum],self.expArr[runNum],self.cropArr[runNum]) 
            t5_Irrig = getIrrigationData(self.simIDArr[runNum],o_t_exid)
            Irrig_df = pd.DataFrame(t5_Irrig, columns=['Date','AmtIrrAppl'])         

            new_dates = []
            for date in Irrig_df['Date']:
                date_obj = datetime.strptime(date, "%m/%d/%Y")
                new_date_str = date_obj.strftime("%Y-%m-%d")
                new_dates.append(new_date_str)
            Irrig_df['Date'] = new_dates
           # print(Irrig_df)

            daily_data.loc[daily_data['Date'].isin(Irrig_df['Date']), 'TotIrrig'] = Irrig_df['AmtIrrAppl'].values      

            if runNum == 0:
                data_df = data_df.append(daily_data, ignore_index=False) 
            else:               
                t5_cum = daily_data.loc[:, ['SeasPSoEv','SeasASoEv','SeasPTran','SeasATran','SeasRain','SeasInfil']]
 
                n = runNum -1
                t51 = extract_cropOutputData("g05_" + self.cropArr[n],self.simIDArr[n])
                t51 = np.asarray(t51)
                t51_max = t51.max(axis=0, keepdims=True)
                t51_max_df = pd.DataFrame(t51_max) 

                for i in range(15, 21):
                    t5_cum_joined = t5_cum.iloc[:, i-15].apply(lambda x:x + t51_max_df.iloc[:, i] )        
                    daily_data.iloc[:,i-1] = t5_cum_joined
                data_df_mid = data_df_mid.append(daily_data,ignore_index=False)                           
                data_df= data_df.append(data_df_mid, ignore_index=False)

        data_df['TotIrrig'] = data_df['TotIrrig'].cumsum()

      
        for key in self.varSurfChaFuncDict:
            data_df[key] = pd.to_numeric(data_df[key], errors='coerce')
            

        data_df = data_df.fillna(0)
   
        data_df_grouped = data_df.groupby(['Date'], as_index=False).agg(self.varSurfChaFuncDict)
        data_df_grouped.rename(columns={'Date':'Date_Time'}, inplace=True)
        data_df_grouped['Date_Time'] = pd.to_datetime(data_df_grouped['Date_Time'])
        tmstampArray = np.array([row['Date_Time'].timestamp() for index, row in data_df_grouped.iterrows()])

        self.surfChaGraphWidget.clear()
        self.surfChaGraphWidget.setLabel("bottom", "Date")
        self.surfChaGraphWidget.showGrid(x=True, y=True)
        self.legend = self.surfChaGraphWidget.addLegend()
        
        i = 0
        maxY = 0
        minY = 0
        for var in checkedVar:
            color = LINECOLORS[i]
            pen = pg.mkPen(color,width=3)
            maxY = max(data_df_grouped[var]) if maxY < max(data_df_grouped[var]) else maxY
            minY = min(data_df_grouped[var]) if minY > min(data_df_grouped[var]) else minY
            self.surfChaGraphWidget.plot(x=tmstampArray,y=np.array(data_df_grouped[var]), name=self.varSurfChaDescUnitDict[var], pen=pen)
            if i < 6:
                i = i + 1
            else:
                i = 0
        # set Y  and X range
        self.surfChaGraphWidget.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(minY*1.05,maxY*1.05),padding=0)
        self.surfChaGraphWidget.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=minY*1.05,yMax=maxY*1.05)

 
    def on_deletebuttonclick(self):
        '''
        This function gets called when user chooses to delete a simulation. Simulations on cropOutput database tables and information on pastruns table on crop 
        database will be deleted and the simulation directory will be deleted as well.
        '''
        delete_flag = messageUserDelete("Are you sure you want to delete this simulation?")
        if delete_flag:
            self.rowNumChecked = [self.table2.simGrp.buttons()[x].isChecked() for x in range(len(self.table2.simGrp.buttons()))].index(True)
            self.rotationID = self.table2.simGrp.buttons()[self.rowNumChecked].text()
            self.cropname = self.table2.item(self.rowNumChecked,6).text().split('/')[0]   

            delete_pastrunsDB_rotationID(self.rotationID,runDir,self.cropname)
            self.populate()


    def on_click_table_widget(self):
        '''
        This gets called when USER clicks one of the old simulation row/column. 
        It will plot the graph(s) for the selected simulation
        '''
        global img, data, i, updateTime, fps
        tab = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        self.simIDArr = []
        self.cropArr = []   
        self.expArr = []   
        self.treatArr = [] 
        self.eomultArr = []
        self.rowSPArr = []

        self.rowNumChecked = [self.table2.simGrp.buttons()[x].isChecked() for x in range(len(self.table2.simGrp.buttons()))].index(True)
        self.rotationID = self.table2.simGrp.buttons()[self.rowNumChecked].text()

        # self.rowNumChecked is the index of the radio box that was checked which doesn't match the 
        # table row index, that the radio box is located.
        placeOnTable = self.rowNumChecked + 1
        count = 0
        for x in range(self.table2.rowCount()):
            #print(self.table2.item(x,0))
            if self.table2.item(x,0) is None:
                count = count + 1
                if count == placeOnTable:
                    ind = x

        self.sitename = self.table2.item(ind,1).text()    
        self.stationtypename = self.table2.item(ind,2).text()    
        self.weathername = self.table2.item(ind,3).text()    
        self.soilname = self.table2.item(ind,4).text()
        self.simIDArr.append(self.table2.item(ind,5).text())
        self.cropArr.append(self.table2.item(ind,6).text().split('/')[0])   
        self.expArr.append(self.table2.item(ind,6).text().split('/')[1])   
        self.treatArr.append(self.table2.item(ind,6).text().split('/')[2]) 

        # Find crop, experiment and treatments associated with this rotation
        nextRow = ind + 1
        while nextRow < self.table2.rowCount():
            if self.table2.item(nextRow,1).text() == "":
                self.simIDArr.append(self.table2.item(nextRow,5).text())
                self.cropArr.append(self.table2.item(nextRow,6).text().split('/')[0])   
                self.expArr.append(self.table2.item(nextRow,6).text().split('/')[1])   
                self.treatArr.append(self.table2.item(nextRow,6).text().split('/')[2])
            else:
                break
            nextRow = nextRow + 1

        self.display1.clear()
        scrollbar = QScrollArea(widgetResizable=True)
        self.simTab = QWidget()
        scrollbar.setWidget(self.simTab)
        self.plantTab = QWidget()
        self.soilCNTab = QWidget()
        self.soilTSTab = QWidget()
        self.soilwhnTab = QWidget()
        self.rootTab = QWidget()
        self.surfChaTab = QWidget()

        ########## simTab ##########
        self.simTabWidget = QtWidgets.QWidget(self.simTab)
        self.simTab.mainlayout = QFormLayout(self.simTabWidget)
        self.simTabWidget.setLayout(self.simTab.mainlayout)
        self.simTab.setLayout(self.simTab.mainlayout)

        genInfoBox = QVBoxLayout()
 
        # Box with general info like sitename, soil, station and weather
        genInfoBoxSum = QHBoxLayout()
        genInfoBoxSumLabel = QLabel()
        genInfoBoxSum.addWidget(genInfoBoxSumLabel)
        genInfoBoxSum.setAlignment(Qt.AlignTop)

        self.simSummaryGen = "<i>General Information </i>"
        self.simSummaryGen += "<br><br><i>Site: </i>" + self.sitename
        self.simSummaryGen += tab + "<i>Soil: </i>" + self.soilname
        self.simSummaryGen += tab + "Station Name: </i>" + self.stationtypename
        self.simSummaryGen += tab + "<i>Weather: </i>" + self.weathername
        genInfoBoxSumLabel.setText(self.simSummaryGen)

        # Adding sections to genInfoBox
        genInfoBox.addLayout(genInfoBoxSum)

        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            # Box with information about crop, cultivar, treatment and experiment
            runInfoBoxSum = QHBoxLayout()
            runInfoBoxSumLabel = QLabel()
            runInfoBoxSum.addWidget(runInfoBoxSumLabel)
            runInfoBoxSum.setAlignment(Qt.AlignTop)

            self.simSummaryRun = tab + "<br><br><i>Crop: </i>" + self.cropArr[runNum]
            self.simSummaryRun += tab + "<i>Experiment: </i>" + self.expArr[runNum]
            self.simSummaryRun += tab + "<i>Treatment: </i>" + self.treatArr[runNum]
            runInfoBoxSumLabel.setText(self.simSummaryRun)

            # Adding sections to genInfoBox
            genInfoBox.addLayout(runInfoBoxSum)

            # Separator
            separatorBox = QHBoxLayout()
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setLineWidth(2)
            separatorBox.addWidget(separator)

            # Adding sections to genInfoBox
            genInfoBox.addLayout(separatorBox)

            # Create horizontal box to store the verticql boxes with dates, agronomic and environmental data
            datesAgroEnvBoxSum = QHBoxLayout()
         
            # Agronomic dates
            genInfoBoxAgroDates = QVBoxLayout()
            genInfoBoxAgroDatesLabel = QLabel()
            genInfoBoxAgroDates.addWidget(genInfoBoxAgroDatesLabel)
            genInfoBoxAgroDates.setAlignment(Qt.AlignTop)

            exid = read_experimentDB_id(self.cropArr[runNum],self.expArr[runNum])
            tid = read_treatmentDB_id(exid,self.treatArr[runNum])
            plantDensity = getPlantDensity(tid)
            operationList = read_operationsDB_id(tid) #gets all the operations
            FertilizerDateList = []
            IrrigationDateList = []
            BeginDate = ""
            SowingDate = ""
            TillageDate = ""
            EmergenceDate = ""
            HarvestDate = ""
            EndDate = ""            
            totalNAppl = 0
            totalirrAppl = 0
                 
            for ii,jj in enumerate(operationList):
                if jj[1] == 'Simulation Start':
                    BeginDate = jj[2] #month/day/year
 
                    initCond = readOpDetails(jj[0],jj[1])
                    self.plantDensity = initCond[0][3]
                    self.eomultArr.append(initCond[0][8])
                    self.rowSPArr.append(initCond[0][9])
                    self.cultivar = initCond[0][10]

                if jj[1] == 'Sowing':                            
                    SowingDate=jj[2]

                if jj[1] == 'Tillage':                            
                    TillageDate=jj[2]

                if jj[1] in "Fertilizer":   
                    FertilizerDateList.append(jj[2])       
                    fertInfo = readOpDetails(jj[0],jj[1])
                    for j in range(len(fertInfo)):
                        if fertInfo[j][5] == "Nitrogen (N)":
                            totalNAppl = totalNAppl + fertInfo[j][6]

                if jj[1] == 'Emergence':                            
                    EmergenceDate=jj[2]

                if jj[1] == 'Harvest':                            
                    HarvestDate=jj[2] #month/day/year

                if jj[1] == "Irrigation":
                    IrrigationDateList.append(jj[2])       
                    irrInfo = readOpDetails(jj[0],jj[1])
                    for j in range(len(irrInfo)):
                        if irrInfo[j][2] == "Sprinkler":
                            totalirrAppl = totalirrAppl + irrInfo[j][4]

                if jj[1] == 'Simulation End':                            
                    EndDate=jj[2] #month/day/year

            FertilizerDate = ""
            IrrigationDate = ""
            if len(FertilizerDateList) >= 1:
                FertilizerDate = ", "
                FertilizerDate = FertilizerDate.join(FertilizerDateList) 
                
            FertilizerDateList.sort(key=lambda FertilizerDateList: datetime.strptime(FertilizerDateList, '%m/%d/%Y'))

            if len(IrrigationDateList) >= 1:
                IrrigationDate = ", "
                IrrigationDate = IrrigationDate.join(IrrigationDateList) 
                
            IrrigationDateList.sort(key=lambda IrrigationDateList: datetime.strptime(IrrigationDateList, '%m/%d/%Y'))

            self.simSummaryDates = "<i>Simulation Dates </i>"
            self.simSummaryDates += "<br><i>Start Date: </i>" + BeginDate
            if TillageDate != "":
                self.simSummaryDates += "<br><i>Tillage Date: </i>" + TillageDate
            if self.cropArr[runNum] != "fallow":
                self.simSummaryDates += "<br><i>Planting Date: </i>" + SowingDate
            if FertilizerDate != "":
                self.simSummaryDates += "<br><i>Fertilization Date: </i>" +  "<br>----" + "<br>----".join(FertilizerDateList)
            if IrrigationDate != "":
                self.simSummaryDates += "<br><i>Irrigation Date: </i>" + "<br>----" + "<br>----".join(IrrigationDateList) 
            if self.cropArr[runNum] == "potato":
                TuberInitDate = getTuberInitDate(self.simIDArr[runNum])
                MaturityDate = getMaturityDate(self.simIDArr[runNum])
                self.simSummaryDates += "<br><i>Emergence Date: </i>" + EmergenceDate
                self.simSummaryDates += "<br><i>Tuber Initiation Date: </i>" + TuberInitDate
                self.simSummaryDates += "<br><i>Maturity Date: </i>" + MaturityDate
            elif self.cropArr[runNum] == "maize":
                EmergenceDate = getMaizeDateByDev(self.simIDArr[runNum],"Emerged")
                TasseledDate = getMaizeDateByDev(self.simIDArr[runNum],"Tasseled")
                SilkedDate = getMaizeDateByDev(self.simIDArr[runNum],"Silked")
                MaturityDate = getMaizeDateByDev(self.simIDArr[runNum],"Matured")
                self.simSummaryDates += "<br><i>Emergence Date: </i>" + EmergenceDate
                self.simSummaryDates += "<br><i>Tasseled Date: </i>" + TasseledDate
                self.simSummaryDates += "<br><i>Silked Date: </i>" + SilkedDate
                self.simSummaryDates += "<br><i>Maturity Date: </i>" + MaturityDate
            elif self.cropArr[runNum] == "soybean":
                FirstFlowerDate = getSoybeanDevDate(self.simIDArr[runNum],1)
                PodInitDate = getSoybeanDevDate(self.simIDArr[runNum],3)
                SeedInitDate = getSoybeanDevDate(self.simIDArr[runNum],4)
                MaturityDate = getSoybeanDevDate(self.simIDArr[runNum],7)
                self.simSummaryDates += "<br><i>Emergence Date: </i>" + EmergenceDate
                self.simSummaryDates += "<br><i>First Flower Date: </i>" + FirstFlowerDate
                self.simSummaryDates += "<br><i>Pod Initiation Date: </i>" + PodInitDate
                self.simSummaryDates += "<br><i>Seed Initiation Date: </i>" + SeedInitDate
                self.simSummaryDates += "<br><i>Maturity Date: </i>" + MaturityDate
            if self.cropArr[runNum] != "fallow":
                self.simSummaryDates += "<br><i>Harvest Date: </i>" + HarvestDate
 
            genInfoBoxAgroDatesLabel.setText(self.simSummaryDates)
            datesAgroEnvBoxSum.addLayout(genInfoBoxAgroDates)

            # Agronomic data
            if self.cropArr[runNum] != "fallow":
                genInfoBoxAgroData = QVBoxLayout()
                genInfoBoxAgroDataLabel = QLabel()
                genInfoBoxAgroData.addWidget(genInfoBoxAgroDataLabel)
                genInfoBoxAgroData.setAlignment(Qt.AlignTop)

                self.simSummaryAgroData = ""
                if self.cropArr[runNum] == "potato" or self.cropArr[runNum] == "soybean":
                    if self.cropArr[runNum] == "potato":
                        agroDataTuple = getPotatoAgronomicData(self.simIDArr[runNum], HarvestDate)
                    else:
                        agroDataTuple = getSoybeanAgronomicData(self.simIDArr[runNum], HarvestDate)
                    NitrogenUptakeTuple = getNitrogenUptake(self.simIDArr[runNum], HarvestDate, self.cropArr[runNum])
                    self.simSummaryAgroData = "<i>Simulation Agronomic Data at <br>" + HarvestDate + " (harvest date)</i>"
                    self.simSummaryAgroData += "<br><i>Yield: </i>" + '{:3.2f}'.format(agroDataTuple[0]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Total biomass: </i>" +  '{:3.2f}'.format(agroDataTuple[1]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Nitrogen Uptake: </i>" +  '{:3.2f}'.format(NitrogenUptakeTuple[0]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Transpiration: </i>" +  '{:3.2f}'.format(agroDataTuple[2]*plantDensity/1000) + " mm"
                elif self.cropArr[runNum] == "maize":
                    if(MaturityDate != "N/A"):
                        agroDataTuple = getMaizeAgronomicData(self.simIDArr[runNum], MaturityDate)
                        self.simSummaryAgroData = "<i>Simulation Agronomic Data at <br>" + MaturityDate + " (maturity date)</i>"
                    else:
                        agroDataTuple = getMaizeAgronomicData(self.simIDArr[runNum], HarvestDate)
                        self.simSummaryAgroData = "<i>Simulation Agronomic Data at <br>" + HarvestDate + " (harvest date)</i>"
                    self.simSummaryAgroData += "<br><i>Yield: </i>" + '{:3.2f}'.format(agroDataTuple[0]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Total biomass: </i>" + '{:3.2f}'.format(agroDataTuple[1]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Nitrogen Uptake: </i>" +  '{:3.2f}'.format(agroDataTuple[2]*plantDensity*10) + " kg/ha"
                elif self.cropArr[runNum] == "cotton":
                    yieldDataTuple = getCottonAgronomicData(self.simIDArr[runNum])
                    yieldDate = dt.strptime(yieldDataTuple[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y %H:%M')
                    FirstSquareDate = getCottonDevDate(self.simIDArr[runNum],"1stSquare")
                    FirstBloomDate = getCottonDevDate(self.simIDArr[runNum],"1stBloom")
                    FirstOpenBollDate = getCottonDevDate(self.simIDArr[runNum],"1stOpenBoll")
                    envDataTuple = getEnvironmentalData(self.simIDArr[runNum],HarvestDate,self.cropArr[runNum])
                    self.envSummaryData = "<i>Simulation Environmental Data </i>"
                    self.simSummaryAgroData = "<i>Simulation Agronomic Data at <br>" + yieldDate + "</i>"
                    self.simSummaryAgroData += "<br><i>Date of first square: </i>" + FirstSquareDate
                    self.simSummaryAgroData += "<br><i>Date of first bloom: </i>" + FirstBloomDate
                    self.simSummaryAgroData += "<br><i>Date of first open boll: </i>" + FirstOpenBollDate
                    self.simSummaryAgroData += "<br><i>Yield: </i>" + '{:3.2f}'.format(yieldDataTuple[1]) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Total biomass: </i>" + '{:3.2f}'.format(yieldDataTuple[2]*plantDensity*10) + " kg/ha"
                    self.simSummaryAgroData += "<br><i>Nitrogen Uptake: </i>" + '{:3.2f}'.format(yieldDataTuple[3]*plantDensity*10) + " kg/ha"

                self.simSummaryAgroData += "<br><i>Total Nitrogen Applied: </i>" + '{:3.2f}'.format(totalNAppl) + " kg/ha"
                self.simSummaryAgroData += "<br><i>Total Irrigation Applied: </i>" + '{:3.2f}'.format(totalirrAppl) + " mm"
                genInfoBoxAgroDataLabel.setText(self.simSummaryAgroData)
                datesAgroEnvBoxSum.addLayout(genInfoBoxAgroData)

            # Environment Data
            envInfoBoxData = QVBoxLayout()
            envInfoBoxDataLabel = QLabel()
            envInfoBoxData.addWidget(envInfoBoxDataLabel)
            envInfoBoxData.setAlignment(Qt.AlignTop)

            if self.cropArr[runNum] == "potato" or self.cropArr[runNum] == "soybean":
                envDataTuple = getEnvironmentalData(self.simIDArr[runNum], HarvestDate, self.cropArr[runNum])
                self.envSummaryData = "<i>Simulation Environmental Data at <br>" + HarvestDate + " (harvest date)</i>"
            elif self.cropArr[runNum] == "maize":
                if(MaturityDate != "N/A"):
                    envDataTuple = getEnvironmentalData(self.simIDArr[runNum], MaturityDate, self.cropArr[runNum])
                    self.envSummaryData = "<i>Simulation Environmental Data at <br>" + MaturityDate + " (maturity date)</i>"
                else:
                    envDataTuple = getEnvironmentalData(self.simIDArr[runNum], HarvestDate, self.cropArr[runNum])
                    self.envSummaryData = "<i>Simulation Environmental Data at <br>" + HarvestDate + " (harvest date)</i>"
            elif self.cropArr[runNum] == "fallow":
                plantDensity = 6.5
                envDataTuple = getEnvironmentalData(self.simIDArr[runNum], EndDate, self.cropArr[runNum])
                self.envSummaryData = "<i>Simulation Environmental Data at <br>" + EndDate + " (simulation end date)</i>"
 
            self.envSummaryData += "<br><i>Total Potential Transpiration: </i>" + '{:3.2f}'.format(envDataTuple[0]) + " mm"
            self.envSummaryData += "<br><i>Total Actual Transpiration: </i>" + '{:3.2f}'.format(envDataTuple[1]) + " mm"
            self.envSummaryData += "<br><i>Total Potential Soil Evaporation: </i>" + '{:3.2f}'.format(envDataTuple[3]) + " mm"
            self.envSummaryData += "<br><i>Total Actual Soil Evaporation: </i>" + '{:3.2f}'.format(envDataTuple[2]) + " mm"
            self.envSummaryData += "<br><i>Total Drainage: </i>" + '{:5.2f}'.format(envDataTuple[7]) + " mm"
            self.envSummaryData += "<br><i>Total Water From Deep Soil: </i>" + '{:5.2f}'.format(envDataTuple[8]) + " mm"
            self.envSummaryData += "<br><i>Total Infiltration: </i>" + '{:3.2f}'.format(envDataTuple[4]) + " mm"
            self.envSummaryData += "<br><i>Total Runoff: </i>" + '{:3.2f}'.format(envDataTuple[5]) + " mm"
            self.envSummaryData += "<br><i>Total Rain: </i>" + '{:3.2f}'.format(envDataTuple[6]) + " mm"
            self.envSummaryData += "<br><i>CO2 Flux: </i>" + '{:3.2f}'.format(envDataTuple[9]/10) + " kg CO2/ha"
            self.envSummaryData += "<br><i>O2 Flux: </i>" + '{:3.2f}'.format(envDataTuple[10]/10) + " kg O2/ha"
            self.envSummaryData += "<br><i>Nitrogen Leach: </i>" + '{:3.2f}'.format(envDataTuple[11]/10) + " kg/ha"
            envInfoBoxDataLabel.setText(self.envSummaryData)

            datesAgroEnvBoxSum.addLayout(envInfoBoxData)

            # Adding sections to genInfoBox
            genInfoBox.addLayout(datesAgroEnvBoxSum)

        self.simTab.mainlayout.addRow(genInfoBox)
        self.simTab.setLayout(self.simTab.mainlayout)
     
        ########## plantTab ##########
        # Creates dictionaries based on crop type
        self.finalVarDescDict, self.finalVarDescUnitDict, self.finalVarFuncDict = genDictOutput(self.cropArr,"plant",1)

        dateAxis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.plantGraphWidget = pg.PlotWidget(axisItems = {'bottom':dateAxis}) 
        self.plantGraphWidget.setMinimumSize(500,300)
        self.plantTab.groupBox = QGroupBox("Select parameter to plot")
        self.leftBoxLayout = QGridLayout()

        self.checkboxes = []
        i = 0
        for var in self.finalVarDescDict:
            checkbox = QtWidgets.QCheckBox(self.finalVarDescDict[var])
            self.checkboxes.append(checkbox)
            j = i//3
            if i % 3 == 0:
                self.leftBoxLayout.addWidget(checkbox,j,0)
            elif i % 3 == 1:
                self.leftBoxLayout.addWidget(checkbox,j,1)
            else:
                self.leftBoxLayout.addWidget(checkbox,j,2)
            i+=1
        j+=1


        self.plotButtom = QPushButton("Plot")

        self.leftBoxLayout.addWidget(self.plotButtom,j,0,1,3)
        self.leftBoxLayout.addWidget(self.plantGraphWidget,0,3,j-1,3)
        self.plantTab.groupBox.setLayout(self.leftBoxLayout)
        self.plotButtom.clicked.connect(self.on_click_plotPlantTab)
 
        self.plantTab.mainlayout = QHBoxLayout()
        self.plantTab.mainlayout.addWidget(self.plantTab.groupBox)
        self.plantTab.setLayout(self.plantTab.mainlayout)
     
        ########## Soil Carbon Nitrogen tab ##########
        # Creates dictionaries based on crop type
        self.finalSoilCNVarDescDict, self.finalSoilCNVarDescUnitDict, self.finalSoilCNVarFuncDict = genDictOutput(self.cropArr,"soilCN",1)

        dateAxis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.soilCNWidget = pg.PlotWidget(axisItems = {'bottom':dateAxis}) 
        self.soilCNWidget.setMinimumSize(500,300)
        self.soilCNTab.groupBox = QGroupBox("Select parameter to plot")
    
        self.leftBoxLayout = QGridLayout()

        self.soilCheckboxes = []
        i = 0
        for var in self.finalSoilCNVarDescDict:
            checkbox = QtWidgets.QCheckBox(self.finalSoilCNVarDescDict[var])
            self.soilCheckboxes.append(checkbox)
            
            j = i//2
            if i % 2 == 0:
                self.leftBoxLayout.addWidget(checkbox,j,0)
            else:
                self.leftBoxLayout.addWidget(checkbox,j,1)
            i+=1
        j+=1

        self.plotButtom = QPushButton("Plot")
        
        self.leftBoxLayout.addWidget(self.plotButtom,j,0,1,2)
        self.leftBoxLayout.addWidget(self.soilCNWidget,0,2,j-1,4)
        self.soilCNTab.groupBox.setLayout(self.leftBoxLayout)
        self.plotButtom.clicked.connect(self.on_click_soilCNTab)
 
        self.soilCNTab.mainlayout = QHBoxLayout()
        self.soilCNTab.mainlayout.addWidget(self.soilCNTab.groupBox)
        
        self.soilCNTab.setLayout(self.soilCNTab.mainlayout)
     
        ########## Soil Water Heat Nitrogen components ##########
        # Creates dictionaries based on crop type
        self.varSoilwhn2DDescDict, self.varSoilwhn2DDescUnitDict, self.varSoilwhn2DFuncDict = genDictOutput(self.cropArr,"soilwhn2D",1)

        self.soilwhnTab.fig = matplotlib.figure.Figure() #plt.figure()
        self.soilwhnTab.canvas = FigureCanvas(self.soilwhnTab.fig)
        self.soilwhnTab.groupBox = QGroupBox()

        date_df = pd.DataFrame([])
        # Create and populate date combo
        # Loop through each run model to give detail information about each run
        for runNum in range(len(self.simIDArr)):
            self.g03Tablename = "g03_" + self.cropArr[runNum]
            t3 = extract_cropOutputData(self.g03Tablename,self.simIDArr[runNum])
            tableID = self.g03Tablename + "_id"
            t3.drop(columns={tableID}, inplace=True)
            date_df = date_df.append(t3,ignore_index=True) 
        new_df = date_df['Date_Time'].str.split(' ', n=1, expand=True)
        date_df['Date'] = new_df[0]
        dateList = date_df['Date'].unique()

        self.comboDate = QComboBox() 
        for date in dateList:         
            self.comboDate.addItem(date)
 
        self.dateselectionlabel= QLabel("Select Date")
        self.hboxLayoutSoil = QHBoxLayout()
        self.hboxLayoutSoil.addWidget(self.dateselectionlabel)
        self.hboxLayoutSoil.addWidget(self.comboDate)

        self.plotButtomSoil = QPushButton("Plot")

        self.hboxLayoutSoil.addWidget(self.plotButtomSoil)
        self.hboxLayoutSoil.addStretch()
        self.soilwhnTab.groupBox.setLayout(self.hboxLayoutSoil)
        self.plotButtomSoil.clicked.connect(self.on_click_plotSoil2DTab)

        self.soilwhnTab.mainlayout = QVBoxLayout()
        self.soilwhnTab.mainlayout.addWidget(self.soilwhnTab.groupBox)
        self.soilwhnTab.mainlayout.addWidget(self.soilwhnTab.canvas)
        self.soilwhnTab.setLayout(self.soilwhnTab.mainlayout)
     
        ########## Soil Time Series Tab ##########
        # Creates dictionaries based on crop type
        self.varSoilTSDescDict, self.varSoilTSDescUnitDict, self.varSoilTSFuncDict = genDictOutput(self.cropArr,"soilTS",0)

        self.SoilTSGraphWidget = pg.GraphicsLayoutWidget()

        dateAxisTotWatProf = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.totWaterProfilePlot = self.SoilTSGraphWidget.addPlot(row=0,col=0,title="Total Water for Entire Profile (mm)",axisItems = {'bottom':dateAxisTotWatProf,'unitPrefix':None})

        dateAxisTotWatLayer = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.totWaterLayerPlot = self.SoilTSGraphWidget.addPlot(row=0,col=1,title="Total Water by Layer (mm)",axisItems = {'bottom':dateAxisTotWatLayer,'unitPrefix':None})

        dateAxisWaterContLayer = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.waterContentLayerPlot = self.SoilTSGraphWidget.addPlot(row=0,col=2,title="Water Content by Layer (cm3/cm3)",axisItems = {'bottom':dateAxisWaterContLayer,'unitPrefix':None})

        dateAxisNNO3ConcProf = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.NNO3ConcProfilePlot = self.SoilTSGraphWidget.addPlot(row=1,col=0,title="Total NNO3 as Nitrogen for Entire Profile (kg/ha)",axisItems = {'bottom':dateAxisNNO3ConcProf,'unitPrefix':None})

        dateAxisNNO3ConcLayer = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.NNO3ConcLayerPlot = self.SoilTSGraphWidget.addPlot(row=1,col=1,title="Total NNO3 as Nitrogen by Layer (kg/ha)",axisItems = {'bottom':dateAxisNNO3ConcLayer,'unitPrefix':None})

        dateAxisTemp = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.tempPlot = self.SoilTSGraphWidget.addPlot(row=1,col=2,title="Temperature by Layer (oC)",axisItems = {'bottom':dateAxisTemp,'unitPrefix':None})
       
        self.soilTSTab.mainlayout = QHBoxLayout()
        self.soilTSTab.mainlayout.addWidget(self.SoilTSGraphWidget)
        self.soilTSTab.setLayout(self.soilTSTab.mainlayout)
     
        data_df = pd.DataFrame([])
        # Loop through each run model to append to the dataframe
        for runNum in range(len(self.simIDArr)):
            self.g03Tablename = "g03_" + self.cropArr[runNum]
            t3 = pd.DataFrame([])
            t3 = extract_cropOutputData(self.g03Tablename,self.simIDArr[runNum])
            # Read geometry table for this simulation
            geo_df = readGeometrySimID(self.simIDArr[runNum])
            # Merge geo_df dataframe to t3 dataframe
            t3 = t3.merge(geo_df, how='inner', on=['X','Y'])
            tableID = self.g03Tablename + "_id"
            t3.drop(columns=[tableID,"Layer"], inplace=True)
            t3['thNew'] = t3['thNew']
            t3['NO3N'] = t3['NO3N']
            t3['thNewArea'] = t3['thNew'] * t3['Area']
            t3['thNewNO3NArea'] = t3['thNew'] * t3['NO3N'] * t3['Area']
            t3['totWat'] = t3['thNewArea']/(self.eomultArr[runNum]*self.rowSPArr[runNum])*10
            t3['NConc'] = t3['thNewNO3NArea']*(14/64)/10/(self.eomultArr[runNum]*self.rowSPArr[runNum])
            
            data_df = data_df.append(t3,ignore_index=True) 

        t3 = data_df
        new_df = t3['Date_Time'].str.split(' ', n=1, expand=True)
        # Get only date
        t3['Date'] = new_df[0]
        t3['Date'] = pd.to_datetime(t3['Date'])
        t3['Y'] = pd.to_numeric(t3['Y'],errors='coerce')
        for key in self.varSoilTSFuncDict:
            t3[key] = pd.to_numeric(t3[key],errors='coerce')
        t3 = t3.fillna(0)

        # Since 2dsoil assigns Y values from the max depth ->0 where the surface is the maximum Depth 
        # and the bottom of the profile is 0, we have to reverse this for the layer file. Thus we 
        # subtract the max depth from all the Y's'
        maxY = max(t3['Y'])
        t3['Y'] = maxY-t3['Y']

        # Need to get layers from soil_long table
        connCrop, cCrop = openDB('crop.db')
        querySL = "select Bottom_depth as Y from soil_long where o_sid = (select id from soil where soilname = '" + self.soilname + "')"
        tSL = pd.read_sql_query(querySL,connCrop)
        tSL = tSL.reset_index()
        tSL['Y'] = pd.to_numeric(tSL['Y'],errors='coerce')

        # Assign layer
        t3Grouped = pd.DataFrame()
        prevY = 0
        for index, rowSL in tSL.iterrows():
            t3Temp = pd.DataFrame()
            mask = (t3['Y']>=prevY) & (t3['Y']<=rowSL['Y'])
            t3Temp = t3.loc[mask]
            t3Temp['layer'] = rowSL['Y']
            prevY = rowSL['Y'] + 0.0001
            t3Grouped = t3Grouped.append(t3Temp)

        # First, we need to group the data by day
        t3GrpDay = t3Grouped.groupby(['Date','X','Y'],as_index=False).mean()
        t3 = t3GrpDay.drop(columns=["X","Y","Q","NH4N","hNew","Area"])

        LINECOLORS = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

        # Set total water profile plot x-axis label
        self.totWaterProfilePlot.clear()
        self.totWaterProfilePlot.setLabel("bottom", "Date")
        self.totWaterProfilePlot.showGrid(x=True, y=True)

        # Set total water by layer plot legend and x-axis label
        self.totWaterLayerPlot.clear()
        self.totWaterLayerPlot.setLabel("bottom", "Date")
        self.totWaterLayerPlot.showGrid(x=True, y=True)
        
        #Initialize totWaterLayerPlot
        self.totWaterLayerPlotLegend = self.totWaterLayerPlot.addLegend()
        try:
            self.totWaterLayerPlotLegend.scene().removeItem(self.totWaterLayerPlotLegend)
        except Exception as e:
            print(e)
        

        # Set water content by layer plot legend and x-axis label
        self.waterContentLayerPlot.clear()
        self.waterContentLayerPlot.setLabel("bottom", "Date")
        self.waterContentLayerPlot.showGrid(x=True, y=True)
        
        #Initialize waterContentLayerPlot
        self.waterContentLayerPlotLegend = self.waterContentLayerPlot.addLegend()
        try:
            self.waterContentLayerPlotLegend.scene().removeItem(self.waterContentLayerPlotLegend)
        except Exception as e:
            print(e)
        

        # Set NNO3 concentration for profile plot x-axis label
        self.NNO3ConcProfilePlot.clear()
        self.NNO3ConcProfilePlot.setLabel("bottom", "Date")
        self.NNO3ConcProfilePlot.showGrid(x=True, y=True)

        # Set NNO3 concentration by layer plot legend and x-axis label
        self.NNO3ConcLayerPlot.clear()
        self.NNO3ConcLayerPlot.setLabel("bottom", "Date")
        self.NNO3ConcLayerPlot.showGrid(x=True, y=True)
        
        # Initialize NNO3ConcLayerPlot
        self.NNO3ConcLayerPlotLegend = self.NNO3ConcLayerPlot.addLegend()
        try:
            self.NNO3ConcLayerPlotLegend.scene().removeItem(self.NNO3ConcLayerPlotLegend)
        except Exception as e:
            print(e)
        

        # Set Temp plot legend and x-axis label
        self.tempPlot.clear()
        self.tempPlot.setLabel("bottom", "Date")
        self.tempPlot.showGrid(x=True, y=True)
        
        #Initialize tempPlot
        self.tempPlotLegend = self.tempPlot.addLegend()
        try:
            self.tempPlotLegend.scene().removeItem(self.tempPlotLegend)
        except Exception as e:
            print(e)
        

        pen = pg.mkPen('r', width=3)

        # total water profile
        totWatProf = t3.groupby('Date',as_index=False)['totWat'].sum()
        # Get values for x-axis, these values will be used in all graphics on this tab.
        totWatProf['Date'] = pd.to_datetime(totWatProf['Date'])
        tmstampArray = np.array([row['Date'].timestamp() for index, row in totWatProf.iterrows()])
        totWatProfMaxY = max(totWatProf['totWat'])
        self.totWaterProfilePlot.plot(x=tmstampArray,y=np.array(totWatProf['totWat']), pen=pen)
        # Set x-axis and y-axis
        self.totWaterProfilePlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(0,totWatProfMaxY*1.05),padding=0)
        self.totWaterProfilePlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=0,yMax=totWatProfMaxY*1.05)

        # NNO3 concentration profile
        NConcProf = t3.groupby('Date',as_index=False)['NConc'].sum()
        NNO3ConcProfMaxY = max(NConcProf['NConc'])
        self.NNO3ConcProfilePlot.plot(x=tmstampArray,y=np.array(NConcProf['NConc']), pen=pen)
        # Set NNO3 concentration profile x-axis and y-axis
        self.NNO3ConcProfilePlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(0,NNO3ConcProfMaxY*1.05),padding=0)
        self.NNO3ConcProfilePlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=0,yMax=NNO3ConcProfMaxY*1.05)

        # Group by layer
        layers = t3.layer.unique()
        i = 0
        totWatLayMaxY = 0
        watContLayMaxY = 0
        NNO3ConcLayMaxY = 0
        tempMaxY = 0
        tempMinY = 0

        for layer in layers:
            temp = t3.loc[t3['layer']==layer]
            color = LINECOLORS[i]
            if i == 6:
                i = -1
            pen = pg.mkPen(color, width=3)

            # total water by layer
            totWatLay = temp.groupby(['Date','layer'],as_index=False)['totWat'].sum()
            totWatLayMaxY = max(totWatLay['totWat']) if totWatLayMaxY < max(totWatLay['totWat']) else totWatLayMaxY
            self.totWaterLayerPlot.plot(x=tmstampArray,y=np.array(totWatLay['totWat']), name="Layer "+str(layer)+" cm", pen=pen)

            # water content by layer
            watContLay = temp.groupby(['Date','layer'],as_index=False)['thNew'].mean()
            watContLayMaxY = max(watContLay['thNew']) if watContLayMaxY < max(watContLay['thNew']) else watContLayMaxY
            self.waterContentLayerPlot.plot(x=tmstampArray,y=np.array(watContLay['thNew']), name="Layer "+str(layer)+" cm", pen=pen)

            # NNO3 concentration by layer
            NConcLay = temp.groupby(['Date','layer'],as_index=False)['NConc'].sum()
            NNO3ConcLayMaxY = max(NConcLay['NConc']) if NNO3ConcLayMaxY < max(NConcLay['NConc']) else NNO3ConcLayMaxY
            self.NNO3ConcLayerPlot.plot(x=tmstampArray,y=np.array(NConcLay['NConc']), name="Layer "+str(layer)+" cm", pen=pen)

            # temperature by layer
            tempLay = temp.groupby(['Date','layer'],as_index=False)['Temp'].mean()
            tempMaxY = max(tempLay['Temp']) if tempMaxY < max(tempLay['Temp']) else tempMaxY
            tempMinY = min(tempLay['Temp']) if tempMinY > min(tempLay['Temp']) else tempMinY
            self.tempPlot.plot(x=tmstampArray,y=np.array(tempLay['Temp']), name="Layer "+str(layer)+" cm", pen=pen)

            i = i + 1

        # Set total water by layer x-axis and y-axis
        self.totWaterLayerPlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(0,totWatLayMaxY*1.05),padding=0)
        self.totWaterLayerPlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=0,yMax=totWatLayMaxY*1.05)
        # Set water content by layer x-axis and y-axis
        self.waterContentLayerPlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(0,watContLayMaxY*1.05),padding=0)
        self.waterContentLayerPlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=0,yMax=watContLayMaxY*1.05)
        # Set NNO3 concentration by layer x-axis and y-axis
        self.NNO3ConcLayerPlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(0,NNO3ConcLayMaxY*1.05),padding=0)
        self.NNO3ConcLayerPlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=0,yMax=NNO3ConcLayMaxY*1.05)
        # Set temperature by layer x-axis and y-axis
        self.tempPlot.setRange(xRange=(min(tmstampArray),max(tmstampArray)),yRange=(tempMinY*1.05,tempMaxY*1.05),padding=0)
        self.tempPlot.setLimits(xMin=min(tmstampArray),xMax=max(tmstampArray),yMin=tempMinY*1.05,yMax=tempMaxY*1.05)


        ########## Root tab ##########
        # Creates dictionaries based on crop type
        self.varRootDescDict, self.varRootDescUnitDict, self.varRootFuncDict = genDictOutput(self.cropArr,"root",1)

        self.rootTab.fig = matplotlib.figure.Figure() #plt.figure()
        self.rootTab.canvas = FigureCanvas(self.rootTab.fig)
        self.rootTab.groupBox = QGroupBox()

        data_df = pd.DataFrame([])
        for runNum in range(len(self.simIDArr)):
            t4 = pd.DataFrame([])
            if self.cropArr[runNum] != "fallow":
                self.g04Tablename = "g04_" + self.cropArr[runNum]
                t4 = extract_cropOutputData(self.g04Tablename,self.simIDArr[runNum])
                tableID = self.g04Tablename + "_id"
                t4.drop(columns=[tableID], inplace=True)
                data_df = data_df.append(t4,ignore_index=True) 
        new_df = data_df['Date_Time'].str.split(' ', n=1, expand=True)
        data_df['Date'] = new_df[0]
        dateRootList = data_df['Date'].unique()
 
        self.comboDateRoot = QComboBox() 
        for date in dateRootList:         
            self.comboDateRoot.addItem(date)
 
        self.dateselectionlabel= QLabel("Select Date")
        self.hboxLayoutRoot = QHBoxLayout()
        self.hboxLayoutRoot.addWidget(self.dateselectionlabel)
        self.hboxLayoutRoot.addWidget(self.comboDateRoot)

        self.plotButtomRoot = QPushButton("Plot")

        self.hboxLayoutRoot.addWidget(self.plotButtomRoot)
        self.hboxLayoutRoot.addStretch()
        self.rootTab.groupBox.setLayout(self.hboxLayoutRoot)
        self.plotButtomRoot.clicked.connect(self.on_click_rootTab)

        self.rootTab.mainlayout = QVBoxLayout()
        self.rootTab.mainlayout.addWidget(self.rootTab.groupBox)
        self.rootTab.mainlayout.addWidget(self.rootTab.canvas)
        self.rootTab.setLayout(self.rootTab.mainlayout)
     
        ### Surface Characteristics tab ###
        # Creates dictionaries based on crop type
        self.varSurfChaDescDict, self.varSurfChaDescUnitDict, self.varSurfChaFuncDict = genDictOutput(self.cropArr,"surfCha",1)

        dateAxis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation = 'bottom')
        self.surfChaGraphWidget = pg.PlotWidget(axisItems = {'bottom':dateAxis}) 
        self.surfChaGraphWidget.setMinimumSize(500,300)
        self.surfChaTab.groupBox = QGroupBox("Select parameter to plot")
        self.surfChaTab.groupBox.setMaximumWidth(270)
        self.vboxSurfChaLayout = QVBoxLayout()
 
        self.surfChaCheckboxes = []
        for var in self.varSurfChaDescDict:
            checkbox = QtWidgets.QCheckBox(self.varSurfChaDescDict[var])
            self.surfChaCheckboxes.append(checkbox)
            self.vboxSurfChaLayout.addWidget(checkbox)

        self.surfChaPlotButtom = QPushButton("Plot")

        self.vboxSurfChaLayout.addWidget(self.surfChaPlotButtom)
        self.vboxSurfChaLayout.addStretch()
        self.surfChaTab.groupBox.setLayout(self.vboxSurfChaLayout)
        self.surfChaPlotButtom.clicked.connect(self.on_click_plotSurfChaTab)
 
        self.surfChaTab.mainlayout = QGridLayout()
        self.surfChaTab.mainlayout.addWidget(self.surfChaTab.groupBox,0,0,2,1)
        self.surfChaTab.mainlayout.addWidget(self.surfChaGraphWidget,0,1)
        self.surfChaTab.setLayout(self.surfChaTab.mainlayout)
        #################################################################################

        if self.rotationID != None:            
            self.display1.addTab(scrollbar,"Rotation Summary")
            self.display1.addTab(self.plantTab,"Plant")
            self.display1.addTab(self.soilTSTab,"Soil Time Series")                      
            self.display1.addTab(self.soilwhnTab,"2D Soil Water Heat Nitrogen")                                  
            self.display1.addTab(self.rootTab,"2D Root")            
            self.display1.addTab(self.surfChaTab,"Surface Characteristics")
            self.display1.addTab(self.soilCNTab,"Soil Carbon Storage") 
            self.display1.setVisible(True)

   
    def importfaq(self, thetabname=None):        
        faqlist = read_FaqDB(thetabname,'')         
        for item in faqlist:
            roottreeitem = QTreeWidgetItem(self.faqtree)
            roottreeitem.setText(0,item[2])
            childtreeitem = QTreeWidgetItem()
            childtreeitem.setText(0,item[3])
            roottreeitem.addChild(childtreeitem)


    def controlfaq(self):                
        if self.helpcheckbox.isChecked():
            self.faqtree.setVisible(True)
        else:
            self.faqtree.setVisible(False)              