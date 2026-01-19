import os
import pandas as pd
import ssl
from urllib.request import Request, urlopen
from urllib.error import URLError
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QVBoxLayout, QPushButton, QSizePolicy, \
                            QMessageBox, QFileDialog, QScrollArea, QCheckBox, QGridLayout, QHeaderView
from PyQt5.QtCore import pyqtSlot
from CustomTool.custom1 import *
from CustomTool.UI import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from functools import partial
from datetime import datetime, timedelta
from dateutil import parser

ssl._create_default_https_context = ssl._create_unverified_context

'''
Contains 1 class.
1). Class Weather_Widget is derived from Qwidget. It is initialed and called by Tabs.py -> class Tabs_Widget. 
    It handles all the features of Weather Tab on the interface. It has signal slot mechanism. It does interact with the 
    DatabaseSys\Databasesupport.py for all the databases related task.
    Pretty generic and self explanotory methods. 
    Refer baseline classes at http://pyqt.sourceforge.net/Docs/PyQt5/QtWidgets.html#PyQt5-QtWidgets
'''

class Weather_Widget(QWidget):
    def __init__(self):
        super(Weather_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
     #  self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
      # self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("weather")             
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.tab_summary = QTextEdit()        
        self.tab_summary.setPlainText("This tab allows to add or update a weather station. A weather station can have more than one weather data, if you are uploading a weather file and you don't want this data to have the same weather_id as the weather station name, \
please provide a column named weather_id with the identifier you want.  For sites within the US territory there is an option to download hourly data for the past 5 years. This data is from NLDAS and MRMS databases (NASA and NOAA administrations respectively).") 
        self.tab_summary.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tab_summary.setReadOnly(True)  
        self.tab_summary.setMinimumHeight(10)    
        self.tab_summary.setAlignment(QtCore.Qt.AlignTop)
        # no scroll bars
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)      
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink="<a href=\"https://youtu.be/m22yAianoFw/\">Click here \
                to watch the Weather Tab video tutorial. </a><br>"
        self.weatherVidlabel=QLabel()
        self.weatherVidlabel.setOpenExternalLinks(True)
        self.weatherVidlabel.setText(urlLink)

        self.mainlayout = QGridLayout()
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vHeader = QVBoxLayout()
        self.vHeader.setContentsMargins(0,0,0,0)
        self.vHeader.addWidget(self.tab_summary)
        self.vHeader.addWidget(self.weatherVidlabel)
        self.vHeader.addWidget(self.helpcheckbox)
        self.vHeader.setAlignment(QtCore.Qt.AlignTop)

        ## Setting up the form elements    
        stationtypelists = read_weather_metaDB()
        self.stationtypelistlabel = QLabel("Station")
        self.stationtypecombo = QComboBox()        
        self.stationtypelistlabel.setBuddy(self.stationtypecombo)
        self.stationtypecombo.addItem("Select from list")
        self.stationtypecombo.addItem("Add New Station Name")
        for id in sorted(stationtypelists, key = lambda i: (stationtypelists[i])):            
            self.stationtypecombo.addItem(stationtypelists[id])
        self.stationtypecombo.currentIndexChanged.connect(self.showweatherdetailscombo,self.stationtypecombo.currentIndex())

        self.sitelabel = QLabel("Site")
        self.sitecombo = QComboBox()        
        self.sitecombo.addItem("Select from list")

        scroll = QScrollArea(widgetResizable=True)
        self.weathersummarylabel = QLabel("")
        scroll.setWidget(self.weathersummarylabel)
        self.scrollWeatherSummary = QVBoxLayout()
        self.scrollWeatherSummary.addWidget(scroll)
        self.avgwindlabel = QLabel("Average Wind (Km/h)")
        self.avgwindedit = QLineEdit("")
        self.avgrainratelabel = QLabel("Average Rain Rate (cm/hr)")
        self.avgrainrateedit = QLineEdit("")
        self.avgco2label = QLabel("Average CO2 (ppm)")
        self.avgco2edit = QLineEdit("")
        self.chemclabel = QLabel("N content in Rainfall (Kg/ha)")
        self.chemcedit = QLineEdit("")
        #Upload weather file button
        self.uploadwflabel = QLabel("Upload Weather File (.csv format)")
        self.buttonUpload = QPushButton("Upload File")
        self.buttonUpload.clicked.connect(self.upload_csv)
        self.downloadwflabel = QLabel("Download Weather Data (last 5 years)")
        self.buttonDownload = QPushButton("Download Data")
        self.buttonDownload.clicked.connect(self.downloadWeatherData)
        self.stationtypelabel = QLabel("Station Name")
        self.stationtypeedit = QLineEdit("")
        self.weatherbutton = QPushButton("SaveAs")
        self.weatherdeletebutton = QPushButton("Delete")

        self.mainlayout.addLayout(self.vHeader,0,0,1,4)
        self.mainlayout.addWidget(self.faqtree,0,4,2,1)       
        self.mainlayout.addWidget(self.stationtypelistlabel,1,0)
        self.mainlayout.addWidget(self.stationtypecombo,1,1)
        self.mainlayout.addWidget(self.sitelabel,2,0)
        self.mainlayout.addWidget(self.sitecombo,2,1)
        self.mainlayout.addWidget(self.avgwindlabel,3,0)
        self.mainlayout.addWidget(self.avgwindedit,3,1)
        self.mainlayout.addWidget(self.avgrainratelabel,4,0)
        self.mainlayout.addWidget(self.avgrainrateedit,4,1)
        self.mainlayout.addWidget(self.avgco2label,5,0)
        self.mainlayout.addWidget(self.avgco2edit,5,1)
        self.mainlayout.addWidget(self.chemclabel,6,0)
        self.mainlayout.addWidget(self.chemcedit,6,1)
        self.mainlayout.addWidget(self.uploadwflabel,7,0)
        self.mainlayout.addWidget(self.buttonUpload,7,1)
        self.mainlayout.addWidget(self.downloadwflabel,8,0)
        self.mainlayout.addWidget(self.buttonDownload,8,1)
        self.mainlayout.addLayout(self.scrollWeatherSummary,9,0,1,4)
        self.mainlayout.addWidget(self.stationtypelabel,10,0)
        self.mainlayout.addWidget(self.stationtypeedit,10,1)
        self.mainlayout.addWidget(self.weatherbutton,10,2)
        self.mainlayout.addWidget(self.weatherdeletebutton,10,3)
        self.sitelabel.setVisible(False)
        self.sitecombo.setVisible(False)
        self.avgwindlabel.setVisible(False)
        self.avgwindedit.setVisible(False)
        self.avgrainratelabel.setVisible(False)
        self.avgrainrateedit.setVisible(False)
        self.avgco2label.setVisible(False)
        self.avgco2edit.setVisible(False)
        self.chemclabel.setVisible(False)
        self.chemcedit.setVisible(False)
        self.uploadwflabel.setVisible(False)
        self.buttonUpload.setVisible(False)
        self.downloadwflabel.setVisible(False)
        self.buttonDownload.setVisible(False)
        self.weathersummarylabel.setVisible(False)
        self.stationtypelabel.setVisible(False)
        self.stationtypeedit.setVisible(False)
        self.weatherbutton.setVisible(False)
        self.weatherdeletebutton.setVisible(False)
        self.setLayout(self.mainlayout) 

       

    def convertDate(row):
        try:
            return parser.parse(row['date'])
        except ValueError:
            try:
                return parser.parse(row['date'], dayfirst=True)
            except ValueError:
                try:
                    return datetime.strptime(row['date'], '%Y-%d-%b')
                except:
                    return row['date']


    def checkWeatherBySite(self,siteIndex):
        siteName = str(self.sitecombo.currentText())
        if siteName == "":
            return False
        # Get site lat lon
        weathertuple = extract_sitedetails(siteName)
        print("PPPP")
        print(weathertuple)
        lat = weathertuple[1]
        lon = weathertuple[2]
        if(Weather_Widget.checkUS(lat,lon)):
            self.downloadwflabel.setVisible(True)
            self.buttonDownload.setVisible(True)
        else:
            self.downloadwflabel.setVisible(False)
            self.buttonDownload.setVisible(False)


    def showweatherdetailscombo(self,value):
        if self.stationtypecombo.itemText(self.stationtypecombo.currentIndex()) == "Select from list" or \
            self.stationtypecombo.itemText(self.stationtypecombo.currentIndex()) == "":
            self.sitelabel.setVisible(False)
            self.sitecombo.setVisible(False)
            self.avgwindlabel.setVisible(False)
            self.avgwindedit.setVisible(False)
            self.avgrainratelabel.setVisible(False)
            self.avgrainrateedit.setVisible(False)
            self.avgco2label.setVisible(False)
            self.avgco2edit.setVisible(False)
            self.chemclabel.setVisible(False)
            self.chemcedit.setVisible(False)
            self.uploadwflabel.setVisible(False)
            self.buttonUpload.setVisible(False)
            self.downloadwflabel.setVisible(False)
            self.buttonDownload.setVisible(False)
            self.weathersummarylabel.setVisible(False)
            self.stationtypelabel.setVisible(False)
            self.stationtypeedit.setVisible(False)
            self.weatherbutton.setVisible(False)
            self.weatherdeletebutton.setVisible(False)
        else:
            self.sitelists = read_sitedetailsDB()
            self.sitecombo.clear()
            self.sitecombo.addItem("Select from list")
            for item in self.sitelists:         
                if item != "Generic Site":
                    self.sitecombo.addItem(item)

            self.sitelabel.setVisible(True)
            self.sitecombo.setVisible(True)
            self.avgwindlabel.setVisible(True)
            self.avgwindedit.setVisible(True)
            self.avgrainratelabel.setVisible(True)
            self.avgrainrateedit.setVisible(True)
            self.avgco2label.setVisible(True)
            self.avgco2edit.setVisible(True)
            self.chemclabel.setVisible(True)
            self.chemcedit.setVisible(True)
          #  self.uploadwflabel.setVisible(True)
          #  self.buttonUpload.setVisible(True)
            self.weatherbutton.setVisible(True)

            stationtype = str(self.stationtypecombo.itemText(self.stationtypecombo.currentIndex()))
            print("FFF")
            print(stationtype)
            if stationtype ==  "Add New Station Name":
              #  self.sitecombo.currentIndexChanged.connect(self.checkWeatherBySite,self.sitecombo.currentIndex())
                self.weathersummarylabel.setText("")
                self.avgwindedit.setText("0")
                self.avgrainrateedit.setText("3.0")
                self.avgco2edit.setText("420")
                self.chemcedit.setText("0")
                self.stationtypeedit.setText("")
                self.stationtypelabel.setVisible(True)
                self.stationtypeedit.setVisible(True)
                self.weatherbutton.setText("SaveAs")
             #   self.weatherbutton.clicked.connect(self.showPrompt)
                self.sitecombo.setEnabled(True)
                self.uploadwflabel.setVisible(False)
                self.buttonUpload.setVisible(False)
                self.downloadwflabel.setVisible(False)
                self.buttonDownload.setVisible(False)
            else:
                self.uploadwflabel.setVisible(True)
                self.buttonUpload.setVisible(True)
                self.downloadwflabel.setVisible(True)
                self.buttonDownload.setVisible(True)
                weathertuple = read_weatherlongDB(stationtype)  
                self.stationtypelabel.setVisible(False)
                self.stationtypeedit.setVisible(False)
                self.sitecombo.setEnabled(False)
                self.weatherbutton.setText("Update")
                if Weather_Widget.checkWeather(stationtype):
                    self.downloadwflabel.setVisible(True)
                    self.buttonDownload.setVisible(True)

                self.avgwindedit.setText(str(weathertuple[7]))
                self.avgrainrateedit.setText(str(weathertuple[8]))
                self.chemcedit.setText(str(weathertuple[9]))
                self.avgco2edit.setText(str(weathertuple[10]))
                self.sitecombo.setCurrentIndex(self.sitecombo.findText(str(weathertuple[12])))
        
                self.weatherSummary = Weather_Widget.getWeatherSummary(stationtype)
                self.weathersummarylabel.setText(self.weatherSummary)
                self.weathersummarylabel.setVisible(True)
                site = str(self.sitecombo.currentText())
                self.weatherdeletebutton.setVisible(True)
                
            if not self.weatherdeletebutton.receivers(self.weatherdeletebutton.clicked):
                self.weatherdeletebutton.clicked.connect(self.on_weatherdeletebuttonclick)                
            self.weatherbutton.clicked.connect(lambda:self.on_weatherbuttonclick(stationtype))
    

    def getWeatherSummary(stationtype):
        # getting weather data from sqlite
        conn, c = openDB('crop.db')
        if c:
            weather_query = "select weather_id, date, hour, srad, wind, rh, rain, tmax, tmin, temperature from weather_data where stationtype=?" 
            df_weatherdata = pd.read_sql(weather_query,conn,params=[stationtype]) 
            weatherSummary = stationtype + " Data Availability Report"
            if df_weatherdata.empty:
                weatherSummary += "<br>No data available.<br>"
            else:
                # Convert date column to Date type
                df_weatherdata['date'] = pd.to_datetime(df_weatherdata.date)
                df_weatherdata = df_weatherdata.sort_values(by='date')
                nan_value = float("NaN")
                df_weatherdata.replace("", nan_value, inplace=True)
                df_weatherdata = df_weatherdata.groupby('weather_id').agg({'date':['min','max'],'srad':['min','max'],'wind':['min','max'],
                                                                           'rh':['min','max'],'rain':['min','max'],'tmax':['min','max'],
                                                                           'tmin':['min','max'],'temperature':['min','max']})
                df_weatherdata.dropna(how='all', axis=1, inplace=True)
                df_weatherdata = df_weatherdata.reset_index()
                weatherSummary = df_weatherdata.to_html(index=False,justify="left")

            return weatherSummary


    def checkWeatherData(df_weatherdata):
        date = []
        sdate = []
        edate = []

        df_weatherdata['date'] = pd.to_datetime(df_weatherdata.date)
        df_weatherdata = df_weatherdata.sort_values(by='date')
        if not 'hour' in df_weatherdata:
            df_weatherdata['hour'] = pd.to_datetime(df_weatherdata['date']).dt.strftime('%H')
        date = df_weatherdata.date.tolist()
        sdate.append(date[0])
        for i in range(1, len(date)):
            if((date[i] != date[i-1]) and (date[i] != date[i-1] + timedelta(days=1))):
                edate.append(date[i-1])
                sdate.append(date[i])
        edate.append(date[len(date)-1])

        weatherSummary = ""
        for sdt, edt in zip(sdate, edate):
            df_weatherSeg = df_weatherdata.loc[(df_weatherdata.date >= sdt) & (df_weatherdata.date <= edt)]
            startDate = sdt.strftime("%m/%d/%Y")
            endDate = edt.strftime("%m/%d/%Y")
            weatherSummary += "<br><i>Start Date:</i> " + startDate + "        <i>End Date:</i>" + endDate + "<br>"

            if df_weatherSeg['hour'].isna().sum() > 0:
                weatherSummary += "Daily data. " + str(df_weatherSeg['date'].count()) + " records read.<br>"
                if df_weatherSeg['tmax'].isna().sum() > 0:
                    weatherSummary += str(df_weatherSeg['tmax'].isna().sum()) + " records missing for maximum temperature.<br>"

                if df_weatherSeg['tmin'].isna().sum() > 0:
                    weatherSummary += str(df_weatherSeg['tmin'].isna().sum()) + " records missing for minimum temperature.<br>"
            else:
                weatherSummary += "Hourly data. " + str(df_weatherSeg['date'].count()) + " records read.<br>"
                if df_weatherSeg['temperature'].isnull().sum() > 0:
                    weatherSummary += str(df_weatherSeg['temperature'].isnull().sum()) + " records missing for temperature.<br>"

            if df_weatherSeg['srad'].isna().sum() > 0:
                weatherSummary += str(df_weatherSeg['srad'].isna().sum()) + " records missing for solar radiation.<br>"

            if df_weatherSeg['rain'].isna().sum() > 0:
                weatherSummary += str(df_weatherSeg['rain'].isna().sum()) + " records missing for rain.<br>"

            if df_weatherSeg['wind'].isna().sum() > 0:
                weatherSummary += str(df_weatherSeg['wind'].isna().sum()) + " records missing for wind speed.<br>"

            if df_weatherSeg['rh'].isna().sum() > 0:
                weatherSummary += str(df_weatherSeg['rh'].isna().sum()) + " records missing for relative humidity.<br>"

            if df_weatherSeg['co2'].isna().sum() > 0:
                weatherSummary += str(df_weatherSeg['co2'].isna().sum()) + " records missing for CO2.<br>"

        return weatherSummary


    def upload_csv(self):
        if self.weatherbutton.text() == "SaveAs":
            stationType = self.stationtypeedit.text()
            if (self.stationtypeedit.text() == ""):
                return messageUser("Station Name is empty. Please, type a Station Name name.")
        else:
            stationType = str(self.stationtypecombo.itemText(self.stationtypecombo.currentIndex()))
        dialog = QFileDialog()
        fname = dialog.getOpenFileName(None, "Import CSV", "", "CSV data files (*.csv)")
        data = pd.read_csv(fname[0])
        # lowercase all column names
        data.columns = map(str.lower, data.columns)
        # get column names
        colNames = list(data.columns.values)
        # check for minimum data requirement
        colNames = set(colNames)
        message = ""
        # test first for date, solar radiation and rain
        reqCol = ['date', 'srad', 'rain']
        for col in reqCol:
            if not col in colNames:
                 message = message + "\nColumn " + col + " is missing."

        if 'hour' not in colNames:
            if 'tmax' not in colNames:
                message = message + "Maximum temperature (tmax) is missing. "
            if 'tmin' not in colNames:
                message = message + "Minimum temperature (tmin) is missing. "
        else:
            if 'temperature' not in colNames:
                message = message + "Column temperature is missing. "

        if message != '':
            return messageUser(message)
        else:
            out = "Would you like to proceed with the ingestion of the following data?\n\n"
            for i, j in data.iterrows():
                if(i <= 9):
                    if i == 0:
                        for col in colNames:
                            out = out + str(col) + ","
                        out = out[:-1] + "\n"
                    for col in colNames:
                        out = out + str(j[col]) + ","
                    out = out[:-1] + "\n"
            ingest_flag = messageUserIngest(out)
            if ingest_flag:
                data['date'] = data.apply(lambda row: Weather_Widget.convertDate(row), axis=1)
                if not 'hour' in data:
                    data['hour'] = pd.to_datetime(data['date']).dt.strftime('%H')
                if not 'jday' in data:
                    data['jday'] = pd.to_datetime(data['date']).dt.strftime('%j')
                dateList = pd.to_datetime(data['date'])

                conn, c = openDB('crop.db')
                # Check if data already exists in the database for stationType for this date range
                minDate = min(dateList)
                maxDate = max(dateList)

                # Check id weather_id is a column on the file, if not create column
                if not 'weather_id' in data:
                    data['weather_id'] = stationType
                weather_ids = "','".join(data['weather_id'].unique().tolist())

                # list of database fields on weather_data table
                dbColumns = ['weather_id','jday', 'date', 'hour', 'srad', 'wind', 'rh', 'rain', 'tmax', 'tmin', 'temperature', 'co2']

                for col in data.columns: 
                    if col not in dbColumns:
                        data.drop(col, axis=1, inplace=True)

                data['stationtype'] = stationType

                # Time to create the columns that are missing
                for col in dbColumns:
                    if col not in data.columns:
                        data[col] = ''

                data = data[['stationtype', 'weather_id','jday', 'date', 'hour', 'srad', 'wind', 'rh', 'rain', 'tmax', 'tmin', 'temperature', 'co2']]
                numRec = data.shape[0]
                recMessage = "Number of rows ingested into database: "+ str(numRec)
                # Before start data ingestion check if dataset is complete
                summary = Weather_Widget.checkWeatherData(data)
                data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
                substr = "records missing"
                message = "<p>This weather station can't be recorded because weather data are missing.</p>"
                # Check for string "records missing"
                if substr in summary:
                    message += summary
                    return messageUser(message)
                else:
                    query = f"select * from weather_data where stationtype='{stationType}' and weather_id in ('{weather_ids}')\
 and date>='{minDate}' and date<='{maxDate}'"
                    c1 = c.execute(query) 
                    c1_row = c1.fetchone()
                    if not c1_row == None:  # means data already exist
                        message = "There is already data for this station and weather type for this date range.  Would you like to replace this data?"
                        ingest_flag2 = messageUserIngest(message)
                        if not ingest_flag2:
                            return False
                        else:
                            queryDel = f"DELETE FROM weather_data where stationtype='{stationType}' and weather_id in ('{weather_ids}')\
 and date>='{minDate}' and date<='{maxDate}'"
                            c.execute(queryDel)
                            conn.commit()
                    
                    data.to_sql('weather_data',conn,if_exists="append",index=False)
                    conn.close() 
                    self.weathersummarylabel.setVisible(True)
                    self.weatherSummary = Weather_Widget.getWeatherSummary(stationType)
                    self.weathersummarylabel.setText(self.weatherSummary)
                    messageUserInfo(recMessage)


    def downloadWeatherData(self):
        sttype = str(self.stationtypecombo.currentText())
        if self.weatherbutton.text().find("SaveAs") > -1:
            sttype = self.stationtypeedit.text()
            if (sttype == ""):
                return messageUser("Station Name is empty. Please, type a Station Name name.")
        msgBox = QMessageBox()
        msgBox.setText("Downloading data, please wait.  New message will show how many records were recorded in the database.")
        msgBox.setWindowTitle("Downloading ....")
        msgBox.setWindowModality(QtCore.Qt.NonModal)
        msgBox.setStandardButtons(QMessageBox.Close)
        msgBox.exec()
        site = str(self.sitecombo.currentText())
        # Get site lat lon
        weathertuple = extract_sitedetails(site)     
        lat = str(weathertuple[1])
        lon = str(weathertuple[2])  
        currentyear = datetime.now().year
       # print("Cuurent Date: ", currentyear)
        year = str(currentyear+2)
        url = "https://weather.covercrop-data.org/hourly?email=Classim-help-ars@usda.gov&lat="+lat+"&lon="+lon+"&start=2015-1-1&end="+year+"-12-31&attributes=air_temperature,relative_humidity,wind_speed,shortwave_radiation,precipitation&output=csv&options=predicted"
        try:
          #  print(url)
            data = pd.read_csv(url,storage_options={'User-Agent':'Mozilla/5.0'})
        except:
            return messageUser("Website has reported an error.  Please, try again later.")

        if data.empty:
            return messageUser("Data is not available at the moment, please try again later.")

        data['jday'] = pd.to_datetime(data['date']).dt.strftime('%j')
        data['hour'] = pd.to_datetime(data['date']).dt.strftime('%H')
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        data.rename(columns={"air_temperature":"temperature","relative_humidity":"rh","wind_speed":"wind","shortwave_radiation":"srad","precipitation":"rain"}, inplace=True)
        # Convert solar radiation
        data['srad'] = data['srad'] * 3600 / 1000000
        # Convert rh to percentage
        data['rh'] = data['rh'] * 100

        msgBox.close()
        conn, c = openDB('crop.db')

        # Check if data already exists in the database for stationType for this date range
        dateList = data['date']
        minDate = min(dateList)
        maxDate = max(dateList) #datetime.date.today() + 730 #
        query = "select * from weather_data where stationtype='" + sttype + "' and weather_id='" + sttype + "' and date>='" + minDate + "' and date<='" + maxDate + "'"
        c1 = c.execute(query) 
        c1_row = c1.fetchone()
        if not c1_row == None:  # means data already exist
            message = "There is already data for this site and weather type for this date range.  Would you like to replace this data?"
            ingest_flag2 = messageUserIngest(message)
            if not ingest_flag2:
                return False
            else:
                queryDel = "DELETE FROM weather_data where stationtype='" + sttype + "' and weather_id='" + sttype + "' and date>='" + minDate + "' and date<='" + maxDate + "'"
                c.execute(queryDel)
                conn.commit()

        # list of database fields on weather_data table
        dbColumns = ['weather_id','jday', 'date', 'hour', 'srad', 'wind', 'rh', 'rain', 'tmax', 'tmin', 'temperature', 'co2']
        data['stationtype'] = sttype
        data['weather_id'] = sttype
 
        # Time to create the columns that are missing
        for col in dbColumns:
            if col not in data.columns:
                data[col] = ''

        data = data[['stationtype', 'weather_id','jday', 'date', 'hour', 'srad', 'wind', 'rh', 'rain', 'tmax', 'tmin', 'temperature', 'co2']]
        numRec = data.shape[0]
        recMessage = "Number of rows ingested into database: "+ str(numRec)
        data.to_sql('weather_data',conn,if_exists="append",index=False, chunksize=200)
        conn.close() 
        self.weathersummarylabel.setVisible(True)
        self.weatherSummary = Weather_Widget.getWeatherSummary(sttype)
        self.weathersummarylabel.setText(self.weatherSummary)
        messageUserInfo(recMessage)


    @pyqtSlot()
    def on_weatherbuttonclick(self,stationtype):
        '''
         save the changes to weather table
        '''
        sttype = str(self.stationtypecombo.currentText())
        if self.weatherbutton.text() == "SaveAs":
            if str(self.sitecombo.currentText()) == "Select from list":
                return messageUser("Please, select a site.")
            sttype = self.stationtypeedit.text()
            if (sttype == ""):
                return messageUser("Station Name is empty. Please, type a Station Name name.")
            matchedindex = self.stationtypecombo.findText(sttype) 
            if (matchedindex > 0):
                return messageUser("Station Name exist. Please use a different name")

        errMess = ""
        bsolar = 1000000
        btemp = 1
        atemp = 0
        bwind = 1
        bir = 1
        avgrain = Weather_Widget.FloatOrZero(self.avgrainrateedit.text())
        avgwind = Weather_Widget.FloatOrZero(self.avgwindedit.text())
        avgco2 = Weather_Widget.FloatOrZero(self.avgco2edit.text())
        chem = Weather_Widget.FloatOrZero(self.chemcedit.text())

        if(avgrain < 0 or avgrain > 10):
            errMess += "- The average rain rates ranges from 0 to 10 cm/day.<br>"

        if(avgwind < 0 or avgwind > 25):
            errMess += "- The average wind ranges from 0 to 25 km/h.<br>"

        if(avgco2 < 0 or avgco2 > 2000):
            errMess += "- The average CO2 ranges from 0 to 2000 ppm.<br>"

        if(chem < 0 or chem > 10):
            errMess += "- The average content of N in rainfall ranges from 0 to 10 kg/ha.<br>"

        if(errMess != ""):     
            messageUserInfo("You might want to check the following information:<br>"+errMess)
        
        record_tuple = (bsolar,btemp,atemp,bwind,bir,avgwind,avgrain,chem,avgco2,str(self.sitecombo.currentText()),sttype)
       
        
        c1 = insert_update_weather(record_tuple,self.weatherbutton.text())
        if c1:
            self.stationtypecombo.clear()  
            stationtypelists = read_weather_metaDB() 
            self.stationtypecombo.addItem("Select from list")
            self.stationtypecombo.addItem("Add New Station Name")
            if self.weatherbutton.text() == "SaveAs":
                self.showPrompt()
            for id in sorted(stationtypelists, key = lambda i: (stationtypelists[i])):            
                self.stationtypecombo.addItem(stationtypelists[id])
            self.sitelabel.setVisible(False)
            self.sitecombo.setVisible(False)
            self.avgwindlabel.setVisible(False)
            self.avgwindedit.setVisible(False)
            self.avgrainratelabel.setVisible(False)
            self.avgrainrateedit.setVisible(False)
            self.avgco2label.setVisible(False)
            self.avgco2edit.setVisible(False)
            self.chemclabel.setVisible(False)
            self.chemcedit.setVisible(False)
            self.uploadwflabel.setVisible(False)
            self.buttonUpload.setVisible(False)
            self.downloadwflabel.setVisible(False)
            self.buttonDownload.setVisible(False)
            self.weathersummarylabel.setVisible(False)
            self.stationtypelabel.setVisible(False)
            self.stationtypeedit.setVisible(False)
            self.weatherbutton.setVisible(False)
            self.weatherdeletebutton.setVisible(False)
            self.weatherbutton.setText("")
            self.refresh() 


    @pyqtSlot()
    def on_weatherdeletebuttonclick(self):
        '''
        Delete record on weather table
        '''  
        print("Delete button clicked.") 
        site = str(self.sitecombo.currentText())
        stationtype = str(self.stationtypecombo.currentText())

        delete_flag = messageUserDelete("Are you sure you want to delete this record?")           
        if not delete_flag:
            print("User canceled deletion.")  # Debugging
            return False
        c1 = delete_weather(site,stationtype)
        if c1:
            self.refresh()          
            self.sitecombo.setCurrentIndex(-1)  # Use setCurrentIndex(-1) for non-editable comboboxes 
            print("After clearing sitecombo:", self.sitecombo.currentText())
            return True

        

    def importfaq(self, thetabname=None):        
        faqlist = read_FaqDB(thetabname,'') 
        faqcount=0
        
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
     

    def FloatOrZero(value):
        try:
            return float(value)
        except:
            return 0.0


    def checkUS(lat,lon):
        if lon > 180:
            lon = lon - 360
        # US continental bounding box
        top = 49.3457868 # north lat
        left = -124.7844079 # west long
        right = -66.9513812 # east long
        bottom =  24.7433195 # south lat
        if bottom <= lat <= top and left <= lon <= right:
            return True

        # Alaska bounding box
        left = -179.148909
        bottom = 51.214183	
        right = 179.77847	
        top = 71.365162
        if bottom <= lat <= top and (-180 <= lon <= left or right <= lon <= 180):
            return True

        # Hawaii bounding box
        left = -178.334698	
        bottom = 18.910361
        right = -154.806773
        top = 28.402123
        if bottom <= lat <= top and left <= lon <= right:
            return True
        else:
            return False


    def checkWeather(stationName):
        if stationName == "":
            return False
        # Get site lat lon
        weathertuple = read_weatherlongDB(stationName)             
        lat = weathertuple[0]
        lon = weathertuple[1]
        return Weather_Widget.checkUS(lat,lon)


    def refresh(self):
        self.stationtypecombo.clear()        
        stationtypelists = read_weather_metaDB() 
        self.stationtypecombo.addItem("Select from list")
        self.stationtypecombo.addItem("Add New Station Name")
        for id in sorted(stationtypelists, key = lambda i: (stationtypelists[i])):
            if str(stationtypelists[id]) != "Generic Site":
                self.stationtypecombo.addItem(stationtypelists[id])
        self.sitelabel.setVisible(False)
        self.sitecombo.setVisible(False)
        self.avgwindlabel.setVisible(False)
        self.avgwindedit.setVisible(False)
        self.avgrainratelabel.setVisible(False)
        self.avgrainrateedit.setVisible(False)
        self.avgco2label.setVisible(False)
        self.avgco2edit.setVisible(False)
        self.chemclabel.setVisible(False)
        self.chemcedit.setVisible(False)
        self.uploadwflabel.setVisible(False)
        self.buttonUpload.setVisible(False)
        self.downloadwflabel.setVisible(False)
        self.buttonDownload.setVisible(False)
        self.weathersummarylabel.setVisible(False)
        self.stationtypelabel.setVisible(False)
        self.stationtypeedit.setVisible(False)
        self.weatherbutton.setVisible(False)
        self.weatherdeletebutton.setVisible(False)
        return True
    
    
    def showPrompt(self):
        msg = QMessageBox()
        msg.setWindowTitle("SaveAs")
        msg.setText("After saving the station name, select the saved station name from the dropdown in Weather Tab to Download/Upload weather data!")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setIcon(QMessageBox.Information)     
        response = msg.exec()  
        if response == QMessageBox.Ok:
            print("You clicked Ok!")
        else:
            print("You clicked Cancel!")
       
        
            