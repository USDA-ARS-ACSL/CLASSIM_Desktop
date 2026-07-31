from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, \
                            QPushButton, QSpacerItem, QSizePolicy, QMenu, QHeaderView, QCheckBox, QGridLayout, QHeaderView, \
                            QShortcut, QApplication
from PyQt5.QtCore import pyqtSlot
from CustomTool.custom1 import *
from CustomTool.UI import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from functools import partial
from decimal import Decimal
import xmltodict
import pandas as pd
import requests

'''
Contains 1 class
1). Class Soil_Widget is derived from Qwidget. It is initialed and called by Tabs.py -> class Tabs_Widget. 
    It handles all the features of SOIL Tab on the interface.
    It has signal slot mechanism. It does interact with the DatabaseSys\Databasesupport.py for all the 
    databases related task.
    Pretty generic and self explanotory methods. 
    Refer baseline classes at http://pyqt.sourceforge.net/Docs/PyQt5/QtWidgets.html#PyQt5-QtWidgets
'''


class Soil_Widget(QWidget):
    def __init__(self):
        super(Soil_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
        self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
      #  self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("Soil")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)
        
        self.tab_summary = QTextEdit()        
        self.tab_summary.setPlainText("This tab allows to add a new soil profile or modify an existing one. Soil profile is linked with an existing site. \
If the soil you are creating is located within the USA territory, data will be retrieved from the Natural Resources Conservation Services (NRCS) for the most \
prominent soil profile for that location.  You will have the ability to edit or delete the values.  A soil profile can have one or more layers, to add or delete \
a soil layer, select the entire row and right click. It will open a dialog box with simple instructions. Once changes are done, please make sure to press the \
UPDATE/SAVE button.")
        self.tab_summary.setReadOnly(True)  
        self.tab_summary.setMaximumHeight(80) # need it        
        self.tab_summary.setAlignment(QtCore.Qt.AlignTop)
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)      
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink1="<a href=\"https://youtu.be/JoaKV-NHcA0/\">Click here \
                to watch the video tutorial for existing soil. </a><br>"
        self.soilVidlabel1=QLabel()
        self.soilVidlabel1.setOpenExternalLinks(True)
        self.soilVidlabel1.setText(urlLink1)

        urlLink2="<a href=\"https://youtu.be/a6B1Ud4LGhk/\">Click here \
                to watch the video tutorial to add new soil. </a><br>"
        self.soilVidlabel2=QLabel()
        self.soilVidlabel2.setOpenExternalLinks(True)
        self.soilVidlabel2.setText(urlLink2)

        
        self.vl1 = QVBoxLayout()
        self.hl1 = QHBoxLayout()
        self.hl2 = QHBoxLayout()
        self.mainlayout1 = QGridLayout()
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hl1.addWidget(self.tab_summary)
        self.hl1.setContentsMargins(0,0,0,0)
        self.hl1.setSpacing(0)
       

        self.save_update_button = QPushButton("Save")
        self.delete_button = QPushButton("Delete")
        self.currentsoillabel = QLabel("Soil Name")
        self.soilname2 = QLineEdit()
        self.system_msg = QLineEdit()
        self.system_msg.setFrame(False)
        self.save_update_button.setVisible(False)
        self.soilname2.setVisible(False)
        self.delete_button.setVisible(False)
        self.currentsoillabel.setVisible(False)
        self.hl2.addWidget(self.currentsoillabel)        
        self.hl2.addWidget(self.soilname2)
        self.hl2.addWidget(self.save_update_button)
        self.hl2.addWidget(self.delete_button)
        
        ## main sub tab 
        self.soillists = read_soilDB()
        self.soillistlabel2 = QLabel("Soil")
        self.sitelabel = QLabel("Site")
        self.bottomBClabel = QLabel("Soil Boundary Condition")

        self.soilcombo = QComboBox()
        self.sitecombo = QComboBox()
        # Create and populate bottomBCcombo
        self.bottomBCcombo = QComboBox()
        self.bottomBCcombo.addItem("Unsaturated Drainage") # val = -7
        self.bottomBCcombo.addItem("Water Table")          # val = 1
        self.bottomBCcombo.addItem("Seepage")              # val = -2

        self.soilselectionlabel= QLabel("Soil Properties")
        self.soiltable1 = QTableWidget()
        self.soiltable1.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.soiltable1.verticalHeader().customContextMenuRequested.connect(self.soiltableverticalheader_popup)        
        # After creating self.soiltable1
        self.soiltable1.viewport().installEventFilter(self)

        # Enable copy / paste on soil table (attach to viewport so editors do not steal it)
        self.copyShortcut = QShortcut(QtGui.QKeySequence.Copy, self.soiltable1.viewport())
        self.copyShortcut.activated.connect(self.copy_selection_to_clipboard)
        self.pasteShortcut = QShortcut(QtGui.QKeySequence.Paste, self.soiltable1.viewport())
        self.pasteShortcut.activated.connect(self.paste_from_clipboard_into_table)

        self.soilselectionlabel.setVisible(False)
        self.soiltable1.setVisible(False)
        self.sitecombo.setVisible(False)
        self.sitelabel.setVisible(False)
        self.bottomBClabel.setVisible(False)
        self.bottomBCcombo.setVisible(False)

        self.soiltable1.horizontalScrollBar().setStyleSheet("QScrollBar:: horizontal {border: 2px solid grey; background: lightgray; height: 15px; \
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

        self.soilcombo.addItem("Select From List")
        self.soilcombo.addItem("Add New Soil")
        for key in self.soillists:            
            self.soilcombo.addItem(key)

        self.soilcombo.currentIndexChanged.connect(self.showsoildetailscombo,self.soilcombo.currentIndex())
        self.soilpagegl = QGridLayout()
        self.soilpagegl.setSpacing(1) 
        self.soilpagegl.setHorizontalSpacing(5)
        self.soilpagegl.setVerticalSpacing(5)
        self.soilpagegl.addWidget(self.soillistlabel2,2,0)
        self.soilpagegl.addWidget(self.soilcombo,2,1)
        self.soilpagegl.addWidget(self.sitelabel,3,0)
        self.soilpagegl.addWidget(self.sitecombo,3,1)
        self.soilpagegl.addWidget(self.bottomBClabel,4,0)
        self.soilpagegl.addWidget(self.bottomBCcombo,4,1)
        self.soilpagegl.addWidget(self.soilselectionlabel,5,0,-1,-1)        
        self.soilpagegl.addWidget(self.soiltable1,5,1,-1,-1)
        self.vl1.setContentsMargins(1,1,1,1)
        self.vl1.addLayout(self.hl1)        
        self.vl1.addItem(self.spacer)
        self.vl1.addWidget(self.soilVidlabel1)
        self.vl1.addWidget(self.soilVidlabel2)
        self.vl1.addWidget(self.helpcheckbox)
        self.vl1.addLayout(self.soilpagegl)
        self.vl1.addLayout(self.hl2)
        self.system_msg.setReadOnly(True)
        self.vl1.addWidget(self.system_msg)
        self.vl1.addItem(self.spacer)
        self.vl1.setAlignment(QtCore.Qt.AlignTop)
        self.mainlayout1.addLayout(self.vl1,0,0)
        self.mainlayout1.setColumnStretch(0,3)
        self.mainlayout1.addWidget(self.faqtree,0,4)
        self.setLayout(self.mainlayout1)
        self.show()

    def loadSoilProfile(self,value):
        if self.soilcombo.itemText(self.soilcombo.currentIndex()) == "Add New Soil":
            # Get site lat lon
            site_tuple = extract_sitedetails(self.sitecombo.itemText(self.sitecombo.currentIndex()))   
            lat = site_tuple[1]
            lon = site_tuple[2]

            # Get soil profile from NRCS website
            lonLat = str(lon) + " " + str(lat)
            url="https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
            headers = {'content-type': 'text/xml'}
            body = """<?xml version="1.0" encoding="utf-8"?>
                      <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
                      <soap:Header/>
                      <soap:Body>
                          <sdm:RunQuery>
                              <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, slope_r, slope_h as slope, hzname, hzdepb_r as depth, 
                                         awc_r as awc, claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, om_r as OM, dbthirdbar_r as dbthirdbar, 
                                         wthirdbar_r/100 as th33, (dbthirdbar_r-(wthirdbar_r/100)) as bd FROM sacatalog sc
                                         FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
                                         FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
                                         FULL OUTER JOIN component co ON mu.mukey=co.mukey
                                         FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
                                         FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
                                         FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
                                         FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
                                         FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
                                         WHERE mu.mukey IN (SELECT * from SDA_Get_Mukey_from_intersection_with_WktWgs84('point(""" + lonLat + """)')) order by co.cokey, ch.chkey, prcent, depth
                              </sdm:Query>
                          </sdm:RunQuery>
                       </soap:Body>
                       </soap:Envelope>"""

            response = requests.post(url,data=body,headers=headers)
            # Put query results in dictionary format
            my_dict = xmltodict.parse(response.content)

            soilheader = ["Bottom depth (cm)","OM (%)","NO3 (ppm)","NH4 (ppm)","HNew","Unit Type","Tmpr (C)","Sand (%)","Silt (%)","Clay (%)",\
                          "BD (g/cm3)","TH33 (cm3/cm3)","TH1500 (cm3/cm3)","thr","ths","tha","th","Alfa","n","Ks","Kk","thk"]
            self.soiltable1.setVisible(True)                
            self.save_update_button.setVisible(True)
            self.soilname2.setVisible(True)
            self.delete_button.setVisible(False)
            self.currentsoillabel.setVisible(True)
            self.soilselectionlabel.setVisible(False)
            self.sitecombo.setEnabled(True) 
            self.bottomBClabel.setVisible(True)
            self.bottomBCcombo.setVisible(True)

            self.save_update_button.setText("SaveAs")
            self.soilname2.setText("")
            self.soilname2.setReadOnly(False)

            self.soiltable1.clear()
            self.soiltable1.setRowCount(0)
            self.soiltable1.setRowCount(1)
            self.soiltable1.setAlternatingRowColors(True)
            self.soiltable1.setColumnCount(22)
            self.soiltable1.setHorizontalHeaderLabels(soilheader)
  
            # Create and populate initType combo
            self.comboInitType = QComboBox()          
            self.comboInitType.addItem("m") # val = 1
            self.comboInitType.addItem("w") # val = 2

            # Convert from dictionary to dataframe format
            try:
                soil_df = pd.DataFrame.from_dict(my_dict['soap:Envelope']['soap:Body']['RunQueryResponse']['RunQueryResult']['diffgr:diffgram']['NewDataSet']['Table'])

                # Drop columns where all values are None or NaN
                soil_df = soil_df.dropna(axis=1, how='all')
                soil_df = soil_df[soil_df.chkey.notnull()]

                # Drop unecessary columns
                soil_df = soil_df.drop(['@diffgr:id', '@msdata:rowOrder', '@diffgr:hasChanges'], axis=1)

                # Drop duplicate rows
                soil_df = soil_df.drop_duplicates()

                # Convert prcent and depth column from object to float
                soil_df['prcent'] = soil_df['prcent'].astype(float)
                soil_df['depth'] = soil_df['depth'].astype(float)

                # Select rows with max prcent
                soil_df = soil_df[soil_df.prcent == soil_df.prcent.max()]

                # Sort rows by depth
                soil_df = soil_df.sort_values(by=['depth'])

                # Check for rows with NaN values
                soil_df_with_NaN = soil_df[soil_df.isnull().any(axis=1)]
                depth = ", ".join(soil_df_with_NaN["depth"].astype(str))
                if len(depth) > 0:
                    messageUserInfo("Layers with the following depth " + depth + " were deleted.")
                    soil_df = soil_df.dropna()

                ### here add the logic for add soil layer
                ## check if all the existing layer has valid data. If yes, then activate the "Add Soil Layer" 
                #button else keep is grayed out
                for index, row in soil_df.iterrows():
                    # Create and populate initType combo
                    self.comboInitType = QComboBox()          
                    self.comboInitType.addItem("m") # val = 1
                    self.comboInitType.addItem("w") # val = 2

                    ccurentrow = self.soiltable1.rowCount()
                    self.soiltable1.insertRow(ccurentrow)
                    for col in range(22):
                        if col == 0:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['depth'])))
                        elif col == 1:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['OM'])))
                        elif col == 2:    
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem("25"))
                        elif col == 3:    
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem("4"))
                        elif col == 4:    
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem("-200"))
                        elif col == 5:    
                            self.soiltable1.setCellWidget(ccurentrow-1,col,self.comboInitType)
                        elif col == 6:    
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem("25"))
                        elif col == 7:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['sand'])))
                        elif col == 8:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['silt'])))
                        elif col == 9:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['clay'])))
                        elif col == 10:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['bd'])))
                        elif col == 11:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem(str(row['th33'])))
                        else:
                            self.soiltable1.setItem(ccurentrow-1,col,QTableWidgetItem("-1"))

            except KeyError:
                print("No data!")
                self.soiltable1.clear()
                self.soiltable1.setRowCount(0)
                self.soiltable1.setRowCount(1)
                self.soiltable1.setAlternatingRowColors(True)
                self.soiltable1.setColumnCount(22)
                self.soiltable1.setHorizontalHeaderLabels(soilheader)
               # Create and populate initType combo
                self.comboInitType = QComboBox()          
                self.comboInitType.addItem("m") # val = 1
                self.comboInitType.addItem("w") # val = 2

                # This list holds the soil long table default values
                soillonglist = [0,0,25,4,-200,1,25,0,0,0,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
                colnum=0
                for val in soillonglist:
                    if colnum == 5:    
                        if(val == 1):
                            matchedindex = self.comboInitType.findText("m")
                        self.comboInitType.setCurrentIndex(matchedindex)
                        self.soiltable1.setCellWidget(0,colnum,self.comboInitType)
                    else:
                        self.soiltable1.setItem(0,colnum,QTableWidgetItem(str(val)))
                    colnum=colnum+1


    def showsoildetailscombo(self,value):
        # Selected "Select from list"
        if self.soilcombo.itemText(self.soilcombo.currentIndex()) == "Select From List":
            self.soiltable1.setVisible(False)                
            self.save_update_button.setVisible(False)
            self.soilname2.setVisible(False)
            self.delete_button.setVisible(False)
            self.currentsoillabel.setVisible(False)
            self.sitecombo.setVisible(False)
            self.sitelabel.setVisible(False)
            self.soilselectionlabel.setVisible(False)
            self.bottomBClabel.setVisible(False)
            self.bottomBCcombo.setVisible(False)
        else:
            self.sitelists = read_sitedetailsDB()
            self.sitecombo.clear()
            self.sitecombo.addItem("Select From List")
            for key in self.sitelists:            
                self.sitecombo.addItem(key)

            soilheader = ["Bottom depth (cm)","OM (%)","NO3 (ppm)","NH4 (ppm)","HNew","Unit Type","Tmpr (C)","Sand (%)","Silt (%)","Clay (%)",\
                          "BD (g/cm3)","TH33 (cm3/cm3)","TH1500 (cm3/cm3)","thr","ths","tha","th","Alfa","n","Ks","Kk","thk"]

            self.sitecombo.setVisible(True)
            self.sitelabel.setVisible(True)

            # Selected "add new soil"
            if self.soilcombo.itemText(self.soilcombo.currentIndex()) == "Add New Soil":
                self.soiltable1.setVisible(False)                
                self.save_update_button.setVisible(False)
                self.soilname2.setVisible(False)
                self.delete_button.setVisible(False)
                self.currentsoillabel.setVisible(False)
                self.soilselectionlabel.setVisible(False)
                self.bottomBClabel.setVisible(False)
                self.bottomBCcombo.setVisible(False)
                self.sitecombo.setEnabled(True)
                self.sitecombo.setCurrentIndex(self.sitecombo.findText("Select From List"))
                self.sitecombo.currentIndexChanged.connect(self.loadSoilProfile,self.sitecombo.currentIndex())
                self.soiltable1.clear()
                self.soiltable1.setRowCount(0)
                self.soiltable1.setRowCount(1)
                self.soiltable1.setAlternatingRowColors(True)
                self.soiltable1.setColumnCount(22)
                self.soiltable1.setHorizontalHeaderLabels(soilheader)            
            else:
                self.soilselectionlabel.setVisible(True)
                self.soiltable1.setVisible(True)
                self.save_update_button.setVisible(True)
                self.soilname2.setVisible(True)
                self.delete_button.setVisible(True)
                self.currentsoillabel.setVisible(True)
                self.bottomBClabel.setVisible(True)
                self.bottomBCcombo.setVisible(True)
                self.save_update_button.setText("Update")  
                self.soilname2.setText(self.soilcombo.itemText(value))  
                self.soilname2.setReadOnly(True)

                soillonglist = read_soillongDB(self.soilcombo.itemText(value)) 
                sitename =  getSiteFromSoilname(self.soilcombo.itemText(value))
                self.sitecombo.setCurrentIndex(self.sitecombo.findText(sitename[0]))
                self.sitecombo.setEnabled(False)
                gridratio_list = read_soilgridratioDB(self.soilcombo.itemText(value))
                for rrow in range(0,len(gridratio_list)):
                    record_tuple = gridratio_list[rrow]
                    bottomBCval = int(record_tuple[6])

                if(bottomBCval == 1):
                   matchedindexBC = self.bottomBCcombo.findText("Water Table")
                elif(bottomBCval == -2):
                   matchedindexBC = self.bottomBCcombo.findText("Seepage")
                else:
                   matchedindexBC = self.bottomBCcombo.findText("Unsaturated Drainage")

                self.bottomBCcombo.setCurrentIndex(matchedindexBC)
         
                self.soiltable1.clear()
                self.soiltable1.setRowCount(0)
                self.soiltable1.setAlternatingRowColors(True)
                self.soiltable1.setColumnCount(22)
                self.soiltable1.setHorizontalHeaderLabels(soilheader)
            
                for rrecord in soillonglist[0:21]:
                    ccurentrow = self.soiltable1.rowCount()
                    self.soiltable1.insertRow(ccurentrow)
                    colnum=0

                    # Create and populate initType combo
                    self.comboInitType = QComboBox()          
                    self.comboInitType.addItem("m") # val = 1
                    self.comboInitType.addItem("w") # val = 2

                    for ccolumn in rrecord:
                        if colnum == 1:
                            ccolumn = ccolumn * 100
                        if colnum == 5:  
                            if(ccolumn == 1):
                                matchedindex = self.comboInitType.findText("m")
                            else:
                                matchedindex = self.comboInitType.findText("w")
                            self.comboInitType.setCurrentIndex(matchedindex)
                            self.soiltable1.setCellWidget(ccurentrow,colnum,self.comboInitType)
                        else:
                            self.soiltable1.setItem(ccurentrow,colnum,QTableWidgetItem(str(ccolumn)))
                        colnum=colnum+1
            
                self.delete_button.clicked.connect(lambda:self.on_deletebuttonclick())

            self.save_update_button.clicked.connect(lambda:self.on_savebuttonclick())
            self.soiltable1.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)                                   
            self.soiltable1.resizeColumnsToContents()
            self.soiltable1.verticalHeader().setStretchLastSection(False)
            self.soiltable1.resizeRowsToContents()
            self.soiltable1.verticalHeader().setStretchLastSection(True)

            self.soiltable1.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(5,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(6,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(7,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(8,QHeaderView.ResizeToContents)  
            self.soiltable1.horizontalHeader().setSectionResizeMode(9,QHeaderView.ResizeToContents)  
            self.soiltable1.horizontalHeader().setSectionResizeMode(10,QHeaderView.ResizeToContents)  
            self.soiltable1.horizontalHeader().setSectionResizeMode(11,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(12,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(13,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(14,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(15,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(16,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(17,QHeaderView.ResizeToContents)
            self.soiltable1.horizontalHeader().setSectionResizeMode(18,QHeaderView.ResizeToContents)  
            self.soiltable1.horizontalHeader().setSectionResizeMode(19,QHeaderView.ResizeToContents)  
            self.soiltable1.horizontalHeader().setSectionResizeMode(20,QHeaderView.ResizeToContents)   
            self.soiltable1.horizontalHeader().setSectionResizeMode(21,QHeaderView.ResizeToContents)   

        # This takes care of enter behaviour
        for key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            QtWidgets.QShortcut(key, self.soiltable1, partial(self.soiltable1.focusNextPrevChild, True))

          
    def getsoilrowinfo(self,rownum):
        currentrow_data = []
        if rownum >=0 and rownum < self.soiltable1.rowCount():
            colnum = 0            
            for ccolumn in range(0,self.soiltable1.columnCount()):
                if(colnum == 5):
                    if(self.comboInitType.currentText() == "m"):
                        val = 1
                    if(self.comboInitType.currentText() == "w"):
                        val = 2
                    currentrow_data.append(float(val))
                else:
                    currentrow_data.append(float(self.soiltable1.item(rownum,ccolumn).text()))
                colnum = colnum + 1
        return currentrow_data


    def deletethisrow(self):
        '''
        deletes the current row
        '''
        where2insertrow = self.soiltable1.currentRow()
        self.soiltable1.removeRow(where2insertrow)        
        howmanyrows = self.soiltable1.rowCount()
        if howmanyrows == 0:
            self.soiltable1.insertRow(howmanyrows)
            for rrecord in soillonglist:
                colnum=0
                # Create and populate initType combo
                self.comboInitType = QComboBox()          
                self.comboInitType.addItem("m") # val = 1
                self.comboInitType.addItem("w") # val = 2

                for ccolumn in rrecord:
                    if(colnum == 5):
                        if(ccolumn == 1):
                            matchedindex = self.comboInitType.findText("m")
                        else:
                            matchedindex = self.comboInitType.findText("w")
                        self.comboInitType.setCurrentIndex(matchedindex)
                        self.soiltable1.setCellWidget(ccurentrow,colnum,self.comboInitType)
                    else:
                        self.soiltable1.setItem((howmanyrows),colnum,QTableWidgetItem(str(ccolumn)))

                    colnum=colnum+1

        self.soiltable1.setItem(howmanyrows,0,QTableWidgetItem(str(-99)))                    
        self.soiltable1.setMaximumHeight(self.soiltable1.verticalHeader().length()*1.25)
        self.soiltable1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.soiltable1.resizeColumnsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(False)
        self.soiltable1.resizeRowsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(True)
        self.soiltable1.resizeColumnsToContents() 


    def duplicaterowabove(self):
        '''
        duplicate a row above
        '''
        # saving the states from these 3 layers
        currentrow_data = self.getsoilrowinfo(self.soiltable1.currentRow())
        previousrow_data = self.getsoilrowinfo(self.soiltable1.currentRow()-1)

        where2insertrow = 0
        where2insertrow = self.soiltable1.currentRow()

        self.soiltable1.insertRow(where2insertrow)        
        colnum=0
        # Create and populate initType combo
        self.comboInitType = QComboBox()          
        self.comboInitType.addItem("m") # val = 1
        self.comboInitType.addItem("w") # val = 2

        for ccolumn in  currentrow_data:               
            if(colnum == 5):
                if(ccolumn == 1):
                    matchedindex = self.comboInitType.findText("m")
                else:
                    matchedindex = self.comboInitType.findText("w")
                self.comboInitType.setCurrentIndex(matchedindex)
                self.soiltable1.setCellWidget(where2insertrow,colnum,self.comboInitType)
            else:
                self.soiltable1.setItem(where2insertrow,colnum,QTableWidgetItem(str(ccolumn)))

            colnum=colnum+1
            # initialize the depth for the new layer to be greater than previous layer (if no 3rd layer 
            # exist) or middle point of 1st and 3rd layer
            
        newdepth = currentrow_data[0]/2
        if len(previousrow_data) >0:
            newdepth = (currentrow_data[0]+ previousrow_data[0])/2                        

        self.soiltable1.setItem(where2insertrow,0,QTableWidgetItem(str(newdepth)))            
        self.soiltable1.setMaximumHeight(self.soiltable1.verticalHeader().length()*1.25)
        self.soiltable1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.soiltable1.resizeColumnsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(False)
        self.soiltable1.resizeRowsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(True)
        self.soiltable1.resizeColumnsToContents() 


    def duplicaterowbelow(self):
        '''
        duplicate a row below
        '''
        # saving the states from these 3 layers
        currentrow_data = self.getsoilrowinfo(self.soiltable1.currentRow())
        nextrow_data = self.getsoilrowinfo(self.soiltable1.currentRow()+1)

        where2insertrow = 0
        where2insertrow = self.soiltable1.currentRow()+1
        self.soiltable1.insertRow(where2insertrow)        
        colnum=0               
        # Create and populate initType combo
        self.comboInitType = QComboBox()          
        self.comboInitType.addItem("m") # val = 1
        self.comboInitType.addItem("w") # val = 2

        for ccolumn in  currentrow_data:               
            if(colnum == 5):
                if(ccolumn == 1):
                    matchedindex = self.comboInitType.findText("m")
                else:
                    matchedindex = self.comboInitType.findText("w")
                self.comboInitType.setCurrentIndex(matchedindex)
                self.soiltable1.setCellWidget(where2insertrow,colnum,self.comboInitType)
            else:
                self.soiltable1.setItem(where2insertrow,colnum,QTableWidgetItem(str(ccolumn)))

            colnum=colnum+1

        newdepth = currentrow_data[0] + 1.0
        if len(nextrow_data) >0:
            newdepth = (currentrow_data[0]+ nextrow_data[0])/2                        

        self.soiltable1.setItem(where2insertrow,0,QTableWidgetItem(str(newdepth)))            
        self.soiltable1.setMaximumHeight(self.soiltable1.verticalHeader().length()*1.25)
        self.soiltable1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.soiltable1.resizeColumnsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(False)
        self.soiltable1.resizeRowsToContents()
        self.soiltable1.verticalHeader().setStretchLastSection(True)
        self.soiltable1.resizeColumnsToContents() 


    def soiltableverticalheader_popup(self, pos):
        '''
        pop menu items will come here
        '''
        if (len(self.soiltable1.selectionModel().selectedRows()) !=1):
            return True

        menu = QMenu()
        duplicaterowbelowaction = menu.addAction("Duplicate this layer below")
        duplicaterowaboveaction = menu.addAction("Duplicte this layer above")
        deletethisrowaction = menu.addAction("Delete this row")
        action = menu.exec_(QtGui.QCursor.pos())
        
        if action == duplicaterowaboveaction:
            self.duplicaterowabove()

        if action == duplicaterowbelowaction:
            self.duplicaterowbelow()

        if action == deletethisrowaction:
            self.deletethisrow()



    def eventFilter(self, obj, event):
        # Intercept Ctrl+V on the table viewport and route it to our paste handler
        if obj is self.soiltable1.viewport() and event.type() == QtCore.QEvent.KeyPress:
            key_event = event
            if key_event.matches(QtGui.QKeySequence.Paste):
                self.paste_from_clipboard_into_table()
                return True  # do not let the editor handle it
        return super(Soil_Widget, self).eventFilter(obj, event)


            
    def copy_selection_to_clipboard(self):
        """
        Copy selected cells in soiltable1 as tab-separated values (TSV),
        compatible with Excel and other spreadsheets.
        """
        sel_ranges = self.soiltable1.selectedRanges()
        if not sel_ranges:
            return

        r = sel_ranges[0]
        rows = []
        for row in range(r.topRow(), r.bottomRow() + 1):
            cols = []
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                if col == 5:
                    # Combo column: read from the QComboBox widget
                    widget = self.soiltable1.cellWidget(row, col)
                    cols.append(widget.currentText() if widget is not None else "")
                else:
                    item = self.soiltable1.item(row, col)
                    cols.append(item.text() if item is not None else "")
            rows.append("\t".join(cols))

        QApplication.clipboard().setText("\n".join(rows))                                                                   

    def paste_from_clipboard_into_table(self):
        """
        Paste TSV/CSV-style text (e.g. from Excel) into soiltable1,
        starting at the current cell; adds rows if necessary.
        """
        start_row = self.soiltable1.currentRow()
        start_col = self.soiltable1.currentColumn()
        if start_row < 0 or start_col < 0:
            return

        text = QApplication.clipboard().text()
        if not text:
            return

        lines = [ln for ln in text.splitlines() if ln.strip() != ""]
        for r_off, line in enumerate(lines):
            cols = line.split("\t")
            row = start_row + r_off
            if row >= self.soiltable1.rowCount():
                self.soiltable1.insertRow(self.soiltable1.rowCount())

            for c_off, cell_text in enumerate(cols):
                col = start_col + c_off
                if col >= self.soiltable1.columnCount():
                    break

                value = cell_text.strip()

                # Unit Type combo column
                if col == 5:
                    combo = self.soiltable1.cellWidget(row, col)
                    if isinstance(combo, QComboBox):
                        idx = combo.findText(value)
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
                    continue

                item = self.soiltable1.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    self.soiltable1.setItem(row, col, item)
                item.setText(value)


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

        
    def resource_path(self,relative_path):
        """
        Get absolute path to resource, works for dev and for PyInstaller 
        """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)  


    @pyqtSlot()
    def on_deletebuttonclick(self):
        '''
        aim: to delete the soil file, on display, from the database
        '''
        check_and_delete_soilDB(self.soilname2.text(),True)
        self.reset_view()


    def reset_view(self):
        '''
        This will Block Signals, reset combobox entries. Unblock signals
        '''
        self.save_update_button.setText("Blank")
        self.soilcombo.blockSignals(True)
        self.soilcombo.clear()
        self.soillists = read_soilDB()
        self.soilcombo.addItem("Select From List")
        self.soilcombo.addItem("Add New Soil")
        for key in self.soillists:            
            self.soilcombo.addItem(key)

        self.sitelists = read_sitedetailsDB()
        self.sitecombo.clear()
        self.sitecombo.addItem("Select From List")
        for key in self.sitelists:            
            self.sitecombo.addItem(key)

        self.soilselectionlabel.setVisible(False)
        self.soiltable1.setVisible(False) 
        self.soiltable1.clear()
        self.soiltable1.reset()
        self.soiltable1.setRowCount(0)
        self.system_msg.clear()
        self.system_msg.setFrame(False)
        self.save_update_button.setVisible(False)
        self.soilname2.setVisible(False)
        self.delete_button.setVisible(False)
        self.currentsoillabel.setVisible(False)  
        self.soilcombo.blockSignals(False)  
        self.sitecombo.setVisible(False)
        self.sitelabel.setVisible(False)
        self.bottomBClabel.setVisible(False)
        self.bottomBCcombo.setVisible(False)


    @pyqtSlot()
    def on_savebuttonclick(self):
        '''
        aim: to save the soil data from the soil tab
        '''
        try:
            self.save_update_button.disconnect()
        except:
            pass
        bottomBC = self.bottomBCcombo.itemText(self.bottomBCcombo.currentIndex())
        if(bottomBC == "Water Table"):
            bottomBCval = 1
        elif(bottomBC == "Seepage"):
            bottomBCval = -2
        else:
            bottomBCval = -7

        soilgridratio_list =[1.2,0.5,2.1,3,10,23,bottomBCval,-4,1]
        next_gridratio_id =0
        self.system_msg.clear()
        #find is it update or save
        if self.save_update_button.text() == "SaveAs":
            print("Debug soiltab:on_savebuttonclick: self.soilname2.text=",self.soilname2.text())
            soilname = str(self.soilname2.text())
            if (soilname == "" or soilname == "Provide soil name"):
                return messageUser("Please, provide soil name.")
            # Get site_id
            site_tuple = extract_sitedetails(self.sitecombo.itemText(self.sitecombo.currentIndex()))   
            site_id = str(site_tuple[0])
            # proceed with creating ids for other tables - saveas logic will come here
            # save soilgridratiolist and preserve the value of new gridratio_id        
            next_gridratio_id = insert_soilgridratioDB(tuple(soilgridratio_list))
            #inserts the soil, gridratio
            check_and_insert_soilDB(soilname,site_id,next_gridratio_id)
            rowNum = self.soiltable1.rowCount() - 1
        elif self.save_update_button.text() == "Update":
            delete_soillong(self.soilname2.text())
            rowNum = self.soiltable1.rowCount()
            updateBottomBC(self.soilname2.text(),bottomBCval)

        wrnMess = ""
        errMess = "" 
        soilTableRowList = []
        for rrow in range(rowNum):
            retrieved_datalist = []
            for ccol in range(self.soiltable1.columnCount()):
                if(ccol == 5):
                    opt = self.soiltable1.cellWidget(rrow,ccol).currentText()
                    if(opt == "m"):
                        val = 1
                    if(opt == "w"):
                        val = 2
                    retrieved_datalist.append(int(val))
                else:
                    retrieved_datalist.append(self.soiltable1.item(rrow,ccol).text())
            retrieved_datalist[1] = float(retrieved_datalist[1])/100
            lLev = self.soiltable1.item(rrow,0).text()
            hNew = Decimal(self.soiltable1.item(rrow,4).text())
            sand = Decimal(self.soiltable1.item(rrow,7).text())
            silt = Decimal(self.soiltable1.item(rrow,8).text())
            clay = Decimal(self.soiltable1.item(rrow,9).text())

            if(sand+silt+clay != 100):
                errMess += "For bottom depth " + lLev + " cm: sand, silt and clay should add up to 100%.<br>"

            if(hNew>=0 and val==1):
                wrnMess += "For bottom depth " + lLev + " cm: if HNew >= 0, the unit type should be 'w', otherwise this will be treated as ponded water surface.<br>"

            soilTableRowList.append(retrieved_datalist)

        if errMess != "":
            if self.save_update_button.text() == "SaveAs":
                check_and_delete_soilDB(self.soilname2.text(),False)
            messageUser(errMess)
            self.save_update_button.clicked.connect(lambda:self.on_savebuttonclick())
        else:
            for row in soilTableRowList:
                insert_into_soillong(self.soilname2.text(), tuple(row))

            if  wrnMess != "":
                messageUserInfo(wrnMess)
            self.reset_view()
