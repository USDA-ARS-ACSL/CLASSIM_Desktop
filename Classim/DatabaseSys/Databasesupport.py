import sqlite3
import re
import os
import pandas as pd
import shutil

from datetime import datetime as dt
from datetime import datetime, timedelta
from CustomTool.UI import *
from CustomTool.getClassimDir import *

dbDir = getClassimDir()

def openDB(database):
    '''
    Open database and return connector
    Input:
       databese: database name and location
    Output:
       database connector and cursor
    '''
    conn = sqlite3.connect(dbDir+'\\'+database)
    c = conn.cursor()   
    if not c:
       print("database not open")
       return False
    else:
        return conn, c


def getClassimVersion():
    '''
    Get latest Classim version, date that was updated and comment
    Input:
    Output:
       version number
       version date
       version comment
    '''
    rlist =() # tuple   
    conn, c = openDB('crop.db')
    if c:
        c.execute("select version from classimVersion ORDER BY id DESC LIMIT 1")  #where id= (select max(id) from classimVersion)")
        c_row = c.fetchone()
     #   print(c_row[0])
        if c_row != None:        
            rlist=c_row[0]
        conn.close()
        return rlist


def insert_update_sitedetails(record_tuple,buttontext):
    '''
 Insert or update a record on sitedetails table
 Input:
    record_tuple=(sitename, latitude, longitude, altitude)
    buttontext is Save or Update
    '''
    conn, c = openDB('crop.db')
    if c:
        record_tuple_aux= record_tuple[1:] + (record_tuple[0],)
        if buttontext == 'SaveAs':
            c.execute("insert into sitedetails(sitename, rlat, rlon, altitude) values (?,?,?,?)",record_tuple)             
        else: 
            c.execute("update sitedetails set rlat=?, rlon=?, altitude=? where sitename=?",record_tuple_aux)       
        conn.commit() 
        conn.close()
        return True


def delete_sitedetails(site):
    '''
  Delete a record from sitedetails table
  Input:
    record_tuple = (sitename)
    '''
    conn, c = openDB('crop.db')
    if c:
        # First update site_id=23 (Generic Site) if there is any soil associated with this site
        c.execute("update soil set site_id=23 where site_id=(select si.id from sitedetails si where sitename=?)",(site,))    

        # Delete from weather_data all records related with this site
        c.execute("delete from weather_data where stationtype in (select stationtype from weather_meta where site=?)",(site,)) 
        c.execute("delete from weather_meta where site=?",(site,)) 

        c.execute("delete from sitedetails where sitename = ?",(site,))  
        conn.commit()

        conn.close()
        return True


def extract_sitedetails(site_string):
    '''
  Retrieve site information from sitedetails table
  Input:
    site_string = sitename
  Output:
    tuple = (site id, latitude, longitude, altitude)
    '''

    result1 =0
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select id,rlat,rlon,altitude from sitedetails where sitename = '%s';"%(site_string)) 
        c1_row = c1.fetchall()
        if c1_row != None:
            for c1_row_record in c1_row:
                 result1 = (c1_row_record[0],c1_row_record[1],c1_row_record[2],c1_row_record[3])
      #  result1 = [(c1_row_record[0],c1_row_record[1],c1_row_record[2],c1_row_record[3]) for c1_row_record in c1_row if c1_row != None]
     #   print(result1)
        conn.close()    
        
    return result1


def read_cropDB():
    '''
  List all crops in the database
  Output: 
    Tuple with crop name
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT id, cropname FROM crops order by lower(cropname)")  
        c1row = c1.fetchall()
      #  if c1row != None:
      #      for c1rowrecord in c1row:
        id = [c1rowrecord[0] for c1rowrecord in c1row if c1row != None][0]
       # name = c1rowrecord[1] 
       # rlist.append(name)
        rlist = [c1rowrecord[1] for c1rowrecord in c1row if c1row != None]
                    
        conn.close()
        return rlist


def read_cultivar_DB(cropname):
    '''
  Extracts hybridname list from cultivar_maize based on the cropname. First get the id from crops table based on 
  crop name then use this information  to link with cultivar_maize table.
  Input:
    cropname
  Output:
    tuple with hybridname list for specific crop
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #print("cropname=",cropname)
        if len(cropname) > 0:     
            if cropname=="maize":   
                c1=c.execute("SELECT hybridname FROM cultivar_maize order by lower(hybridname)")   
            elif cropname=="potato":     
                c1=c.execute("SELECT hybridname FROM cultivar_potato order by lower(hybridname)")
            elif cropname=="soybean":     
                c1=c.execute("SELECT hybridname FROM cultivar_soybean order by lower(hybridname)")
            elif cropname=="cotton":     
                c1=c.execute("SELECT hybridname FROM cultivar_cotton order by lower(hybridname)")

            c1_rows = c1.fetchall()
          #  for c1_row in c1_rows:        
          #      rlist.append(c1_row[0])
            rlist = [c1_row[0] for c1_row in c1_rows]
            
        conn.close()
        return rlist


def read_tillageTypeDB():
    '''
  List all tillage types in the database
  Output: 
    Tuple with tillage types name
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT id, tillage FROM tillageType order by lower(tillage)")  
        c1row = c1.fetchall()
        rlist = [c1rowrecord[1] for c1rowrecord in c1row if c1row != None]
     #   if c1row != None:
      #      for c1rowrecord in c1row:
      #          id = c1rowrecord[0]
      #          tillage = c1rowrecord[1]
      #          rlist.append(tillage)
              
        conn.close()
        return rlist


def read_PGRChemicalDB():
    '''
  List all PGR chemical types in the database
  Output: 
    Tuple with PGR chemical types name
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT id, PGRChemical FROM PGRChemical order by lower(PGRChemical)")  
        c1row = c1.fetchall()
       # if c1row != None:
       #     for c1rowrecord in c1row:
       #         id = c1rowrecord[0]
       #         PGRChemical = c1rowrecord[1]
       #         rlist.append(PGRChemical)
        rlist = [c1rowrecord[1] for c1rowrecord in c1row if c1row != None]       
        conn.close()
        return rlist


def read_PGRAppTypeDB():
    '''
  List all PGR application types in the database
  Output: 
    Tuple with PGR application types name
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT id, applicationType FROM PGRApplType order by lower(applicationType)")  
        c1row = c1.fetchall()
      #  if c1row != None:
       #     for c1rowrecord in c1row:
       #         id = c1rowrecord[0]
       #         applicationType = c1rowrecord[1]
       #         rlist.append(applicationType)
        rlist =  [c1rowrecord[1] for c1rowrecord in c1row  if c1row != None]   
        conn.close()
        return rlist


def read_PGRAppUnitDB():
    '''
  List all PGR application units in the database
  Output: 
    Tuple with PGR application units
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT id, PGRUnit FROM PGRUnit order by lower(PGRUnit)")  
        c1row = c1.fetchall()
      #  if c1row != None:
       #     for c1rowrecord in c1row:
       #         id = c1rowrecord[0]
       #         PGRUnit = c1rowrecord[1]
       #         rlist.append(PGRUnit)
        rlist =  [c1rowrecord[1] for c1rowrecord in c1row  if c1row != None]        
        conn.close()
        return rlist


def read_SurfResTypeDB():
    '''
  List all surface residue types in the database
  Output: 
    Tuple with surface residue type
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("select residueType from surfResType order by lower(residueType)")  
        c1row = c1.fetchall()
      #  if c1row != None:
      #      for c1rowrecord in c1row:
       #         surfResType = c1rowrecord[0]
       #         rlist.append(surfResType)
        rlist =  [c1rowrecord[0]  for c1rowrecord in c1row  if c1row != None]        
        conn.close()
        return rlist


def read_SurfResApplTypeDB():
    '''
  List all surface residue application types in the database
  Output: 
    Tuple with surface residue application type
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("select applicationType from surfResApplType order by lower(applicationType)")  
        c1row = c1.fetchall()
       # if c1row != None:
      #      for c1rowrecord in c1row:
       #         surfResApplType = c1rowrecord[0]
       #         rlist.append(surfResApplType)
        rlist =  [c1rowrecord[0]  for c1rowrecord in c1row  if c1row != None]        
        conn.close()
        return rlist

def read_irrigationType():
    '''
    List all Irrigation types in the database
    Input:
    Output:
    Irrigation Types.
    '''
    irrlist = []
    conn, c =openDB('crop.db')
    if c:
        c1 = c.execute("SELECT irrigationClass from irrigationClass order by irrigationClass")
        c1_row = c1.fetchall()
        irrlist = [c1_row_record[0] for c1_row_record in c1_row  if c1_row != None]  
        conn.close()
        return irrlist

def read_irrOption():
    '''
    List all Irrigation options in the database
    Input:
    Output:
    Irrigation Options.
    '''
    irrlist = []
    conn, c =openDB('crop.db')
    if c:
        c1 = c.execute("SELECT irrOption from Irr_Options order by irrOption")
        c1_row = c1.fetchall()
        irrlist = [c1_row_record[0] for c1_row_record in c1_row  if c1_row != None] 
        conn.close()
        return irrlist


def readSoilWater(simulationname, cropname):
    '''
    Returns the soil water content data
    input:
        simulationname
    Output:
        soil water content
    '''
    
    conn, c = openDB('cropOutput.db')
    croptable = "g05_" + cropname
    id = croptable + "_id"
    
    if c:
        query = f"SELECT Date_Time, ThetaAvail FROM {croptable} WHERE {id} = ?"
  #      query =  "SELECT Date_Time, ThetaAvail FROM g05_maize WHERE  g05_maize_id = ? "
        param=(simulationname,)
        df = pd.read_sql_query(query,conn, params = param)
        conn.close()
        return df #irrlist
    

def read_cultivar_DB_detailed(hybridname,cropname):
    '''
  Extracts the link id from cropname and  croptable. With linkid, we can query cultivar_maize table to get details of the crop variety.
  This one gives lot more parameters
  Input:
    hybridname
    cropname
  Output:
    tuple with complete information about a particular hybridname
    '''
    rlist = [] # tuple   
    conn, c = openDB('crop.db')
    if c:
        if len(cropname) > 0:   
            if cropname == "maize":
                c1=c.execute("SELECT juvenileleaves, DaylengthSensitive, Rmax_LTAR, Rmax_LTIR, PhyllFrmTassel,StayGreen,LM_min,\
                              RRRM,RRRY,RVRL,ALPM, ALPY,RTWL,RTMinWTperArea,EPSI,IUPW,CourMax,Diffx, Diffz,Velz,lsink,Rroot,\
                              Constl_M,ConstK_M,Cmin0_M,ConstI_Y,ConstK_Y, Cmin0_Y,hybridname FROM cultivar_maize where \
                              hybridname = ?",[hybridname])      
            elif cropname == "potato":       
                c1=c.execute("SELECT A1, A6, A8, A9, A10, G1, G2, G3, G4, RRRM, RRRY, RVRL, ALPM, ALPY, RTWL, RTMinWTperArea, \
                              EPSI, IUPW, CourMax, Diffx, Diffz, Velz, lsink, Rroot, Constl_M, ConstK_M, Cmin0_M, ConstI_Y, \
                              ConstK_Y, Cmin0_Y FROM cultivar_potato where hybridname = ?",[hybridname])      
            elif cropname == "soybean":       
                c1=c.execute("SELECT matGrp, seedLb, fill, v1, v2, v3, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, g1, \
                              g2, g3, g4, g5, g6, g7, g8, g9, RRRM, RRRY, RVRL, ALPM, ALPY, RTWL, RTMinWTperArea, EPSI, IUPW, \
                              CourMax, Diffx, Diffz, Velz, lsink, Rroot, Constl_M, ConstK_M, Cmin0_M, ConstI_Y, ConstK_Y, \
                              Cmin0_Y FROM cultivar_soybean where hybridname = ?",[hybridname])  
            elif cropname == "cotton":       
                c1=c.execute("SELECT calbrt11, calbrt12, calbrt13, calbrt15, calbrt16, calbrt17, calbrt18, calbrt19, calbrt22, \
                              calbrt26, calbrt27, calbrt28, calbrt29, calbrt30, calbrt31, calbrt32, calbrt33, calbrt34, calbrt35, \
                              calbrt36, calbrt37, calbrt38, calbrt39, calbrt40, calbrt41, calbrt42, calbrt43, calbrt44, calbrt45, \
                              calbrt47, calbrt48, calbrt49, calbrt50, calbrt52, calbrt57 FROM cultivar_cotton where hybridname = ?",[hybridname])
            c1_row = c1.fetchone()
            if c1_row != None:        
                rlist=c1_row

      #  print(rlist)
        conn.close()
        return rlist


def read_experimentDB():
    '''
  Extracts list of experiments.
  Output:
    tuple with experiment names
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("SELECT exid, name FROM experiment order by experiment")  
        c1row = c1.fetchall()
      #  if c1row != None:
      #      for c1rowrecord in c1row:
      #          id = c1rowrecord[0]
       #         name = c1rowrecord[1]
       #         rlist.append(name) 
        rlist = [c1rowrecord[1] for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def getExpTreatByCrop(cropname):
    '''
  Extracts experiment based on crop name.
  Input:
    cropname
  Output:
    tuple with experiment names
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        #need auto increment ID, nonnull
        c1 = c.execute("select e.name || '/' || t.name as expTreat from experiment e, treatment t where t_exid=exid and e.crop = ? order by lower(e.name), lower(t.name)",[cropname])  
        c1row = c1.fetchall()
      #  if c1row != None:
      #      for c1rowrecord in c1row:
      #          rlist.append(c1rowrecord[0])
        rlist = [c1rowrecord[0] for c1rowrecord in c1row if c1row != None]
    conn.close()
    return rlist


def getExpTreatByCropWeatherDate(cropname,stationtype,weatherID):
    '''
  Extracts experiment based on crop name.
  Input:
    cropname
    stationtype
    weatherID
  Output:
    tuple with experiment names
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        # Find the date range for the weatherID data
        record_tuple = (stationtype,weatherID)
        c = c.execute("select min(date) as minDate, max(date) as maxDate from weather_data where stationtype=? and weather_id=?",record_tuple)
        c_row = c.fetchone()
        if c_row != None:
            minDate = datetime.strptime(c_row[0],'%Y-%m-%d')
            maxDate = datetime.strptime(c_row[1],'%Y-%m-%d')

        query = "select e.name || '/' || t.name as expTreat, odate from experiment e, treatment t, operations o where \
                 t_exid=exid and e.crop='" + cropname + "' and t.tid=o.o_t_exid AND odate!='' order by lower(e.name), lower(t.name)"
        df = pd.read_sql_query(query,conn)
        df['odate'] = pd.to_datetime(df['odate'])
        mask = (df['odate'] >= minDate) & (df['odate'] <= maxDate)
        df = df.loc[mask]
        expTreatList = df['expTreat'].unique()

    conn.close()
    return expTreatList


def read_experimentDB_id(cropname, experimentname):
    '''
  Extracts experiment id based on crop and treatment name.
  Input:
    cropname
    treatmentname
  Output:
    experiment id
    '''
    rlist =None  
    conn, c = openDB('crop.db')
    if c:
        record_tuple =(cropname,experimentname)
        if len(cropname) > 0 and len(experimentname) > 0:
            c2 = c.execute("SELECT exid FROM experiment where crop = ? and name = ?",record_tuple)
            c2_row = c2.fetchone()
            if c2_row != None:
                rlist = c2_row[0]

        conn.close()    
        return rlist


def read_operationsDB_id(o_t_exid):
    '''
  Get all operations using treatment id.
  Input:
    o_t_exid = treatment id
  Output:
    tuple listing all operations with full detail.
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        if isinstance(o_t_exid,int):
            c2 = c.execute("SELECT opID, name, odate FROM operations where o_t_exid = ?", (o_t_exid,))
            c2_row = c2.fetchall()
           # if c2_row != None:
           #     for c2_row_record in c2_row:
           #         rlist.append(c2_row_record)
            rlist = [c2_row_record for c2_row_record in c2_row if c2_row != None]
        conn.close()    
        return rlist


def getPlantDensity(o_t_exid):
    '''
  Get all operations using treatment id.
  Input:
    o_t_exid = treatment id
  Output:
    plant density
    '''
    rlist = ""  
    conn, c = openDB('crop.db')
    if c:
        if isinstance(o_t_exid,int):
            c2 = c.execute("SELECT pop FROM initCondOp where opID = (select opID from operations where \
                            name = 'Simulation Start' and o_t_exid = ?)", (o_t_exid,))
            c2_row = c2.fetchone()
            if c2_row != None:            
                rlist= c2_row[0]

        conn.close() 
     #   print(rlist)
        return rlist


def read_treatmentDB_id(exid,treatmentname):
    '''
  Returns treatment id based on treatment name and experiment id.
  Input:
    exid = experiment id
    treatmentname
  Output:
    tid = treatment id
    '''
    rlist =None
    conn, c = openDB('crop.db')
    if c:
        treatmentname2 = treatmentname+'%'
        record_tuple =(exid,treatmentname2)
        if isinstance(exid,int) and isinstance(treatmentname2,str):
            c2 = c.execute("SELECT tid FROM treatment where t_exid = ? and name like ?",record_tuple)
            c2_row = c2.fetchone()
            if c2_row != None:            
                rlist= c2_row[0]
        conn.close()    
        return rlist


def check_and_update_experimentDB(item,cropname):
    '''
  Check if there is an experiment with name "item" for a pasrticular crop name. Insert record if this combination is 
  new, otherwise returns false.
  Input:
    item = experiment name
    cropname
  Output:
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        if len(item) > 0:
            c1 = c.execute("SELECT exid, name FROM experiment where name = '%s' and crop = '%s';" %(''.join(item),''.join(cropname)))  
            c1_row = c1.fetchone()
            if c1_row == None:
                c2 = c.execute("insert into experiment (name,crop) values ('%s','%s');" %(''.join(item),''.join(cropname)))
                conn.commit()
            else:  # means data already exist
                return False 
        conn.close()  
        return True


def check_and_delete_soilDB(soilname,askUserFlag):
    '''
  Delete records on tables gridratio, soil_long and soil based on soil name.
  Input:
    soilname
    askUserFlag
  Output:
    '''
    conn, c = openDB('crop.db')
    delete_flag = False
    if c:
        id = 0
        c.execute("Select id, o_gridratio_id FROM soil where soilname =?",[soilname])
        for op in c:
            id = int(op[0])
            gridratio_id = int(op[1])

        if id > 0:
            if askUserFlag:
                delete_flag = messageUserDelete("Are you sure you want to delete this record?")
            else:
                delete_flag = True

        if delete_flag:
            c.execute("DELETE FROM gridratio where gridratio_id = ?",(gridratio_id,))
            c.execute("DELETE FROM soil_long where o_sid = ?",(id,))
            c.execute("DELETE FROM soil where soilname =?",[soilname])
            conn.commit()

        conn.close()          


def check_and_delete_experimentDB(experimentname,cropname):
    '''
  Check if the item exist in experiment table, then do a iterative deletion of treatments & operations and then delete this experiment
  Input:
    experimentname
    cropname
  Output:
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        record_tuple = (experimentname,cropname)     
        if len(experimentname) > 0:
            c1 = c.execute("SELECT exid, name FROM experiment where name = '%s' and crop = '%s';" %(''.join(experimentname),''.join(cropname)))  
            c1_row = c1.fetchone()
            if c1_row != None:
                # get treatments defined under this experiment
                rtuple = (c1_row[0],)
                g_tid = c.execute("SELECT tid, name FROM treatment where t_exid=?", rtuple)  # getting treatment ids
                g_tid_rows = g_tid.fetchall()
                for g_tid_row in g_tid_rows:
                    check_and_delete_treatmentDB(g_tid_row[1],experimentname,cropname)
            
                c2 = c.execute("DELETE FROM experiment where name=? AND crop=?",record_tuple)
                conn.commit()

        conn.close()  
        return True


def check_and_delete_treatmentDB(treatmentname, experimentname ,cropname):
    '''
  Check if the item exist in experiment table, then do a iterative deletion of treatments & operations and then delete this experiment
  Input:
    treatmentname
    experimentname
    cropname
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT exid, name FROM experiment where name = '%s' and crop = '%s';" %(''.join(experimentname),''.join(cropname)))  
        c1_row = c1.fetchone()
        if c1_row != None:
            # get treatments defined under this experiment
            rtuple_str = str(c1_row[0])
            g_tid = c.execute("SELECT tid, name FROM treatment where t_exid= '%s' and name ='%s';" %(''.join(rtuple_str),''.join(treatmentname)))  # getting treatment ids
            g_tid_row = g_tid.fetchone()
            rtuple3 = (g_tid_row[0],)
            # Need to delete operations one by one
            origOp = c.execute("select opID, name from operations where o_t_exid=?",rtuple3)
            origOp_rows = origOp.fetchall()
            # Delete each operation
            for origOp_row in origOp_rows:
                check_and_delete_operationDB(origOp_row[0],origOp_row[1])
            c.execute("DELETE FROM treatment where tid=?",rtuple3)          
            conn.commit()

        conn.close() 
        return True


def isSiteOnPastruns(site):     
    '''
  Check if a site is being used in any simulation.
  Input:
    site
  Output:
    true/false
    '''
    conn, c = openDB('crop.db')
    if c:
        c1row = c.execute("select count(id) from pastruns where site = ?",(site,))    
        c1_row = c1row.fetchone()
        nSites = c1_row[0]
        conn.close()
        if nSites > 0:
            return True
        else:
            return False


def update_pastrunsDB(rotationID,site,managementname,stationtype,weatherID,soilname,startyear,endyear,waterstress,nitrostress,tempVar,rainVar,CO2Var):     
    '''
  Insert a new record on pastrun table and returns the assigned id.
  Input:
    rotationID
    site
    managementname
    weather
    stationtype
    soilname
    startyear
    endyear
    waterstress
    nitrostress
    tempVar
    rainVar
    CO2Var
  Output:
    pastrun id
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        odate =  datetime.now()

        record_tuple = (rotationID,site,managementname,stationtype,weatherID,soilname,startyear,endyear,odate,waterstress,nitrostress,tempVar,rainVar,CO2Var)
       # print(record_tuple)

        c.execute("insert into pastruns (rotationID, site, treatment, stationtype, weather, soil, startyear, endyear, odate, waterstress, nitrostress, tempVar, \
                   rainVar, CO2Var) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", record_tuple) 
        conn.commit()
        # retrieve the ID
        c1row = c.execute("select id from pastruns where rotationID = ? AND site = ? AND treatment = ? AND stationtype = ? AND weather = ? AND soil = ? AND  startyear = ? \
                           AND endyear = ? AND odate = ? AND waterstress = ? AND nitrostress = ? AND tempVar = ? AND rainVar = ? AND CO2Var = ?",record_tuple)    
        c1_row = c1row.fetchone()
        if c1_row != None:
            rlist=list(c1_row)
        conn.close()
        return rlist


def delete_pastrunsDB(id,cropname):     
    '''
  Delete pastrun.
  Input:
    id
    cropname
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        query = "delete from pastruns where id=" + id
        c.execute(query)    
        conn.commit()
        conn.close()

        # Delete the directory that was created with the simulation information
        sim_dir = os.path.join(dbDir,id)
        shutil.rmtree(sim_dir, ignore_errors=True)

        # Delete simulations on the cropOutput database tables
        delete_cropOutputSim(id,cropname)

        return True


def delete_pastrunsDB_rotationID(rotationID,cropname):     
    '''
  Delete pastrun.
  Input:
    id
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        # Find which runs belong to this rotationID
        query = "select id from pastruns where rotationID = " + str(rotationID)
        c1 = c.execute(query)      
        c1_rows = c1.fetchall()

        for c1_row in c1_rows:
            simulationID = str(c1_row[0])

            # Delete simulation from pastruns
            delete_pastrunsDB(simulationID,cropname)

        conn.close()
        return True


def extract_pastrunsidDB(id):    
    '''
  Returns a tuple with all pastruns in the database.
  Input:
  Output:
    Tuple with complete pastruns information.
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if id == 0:
            query = 'select id, rotationID, site, soil, stationtype, weather, treatment, startyear, endyear, waterstress, \
                     nitrostress, tempVar, RainVar, CO2Var from pastruns where rotationID == 0  order by rotationID, id desc'
        else:     
            query = 'select rotationID, site, stationtype, weather, soil, id, treatment, startyear, endyear, waterstress, \
                     nitrostress, tempVar, RainVar, CO2Var from pastruns where rotationID != 0  order by rotationID desc , id asc'
    
        c1 = c.execute(query)      
        c1_rows = c1.fetchall()
       # for c1_row in c1_rows:
     #       rlist.append(c1_row)
        rlist = [c1_row for c1_row in c1_rows]
        conn.close()
        return rlist


def getNextRotationID():
    '''
  Returns next rotationID
  Input:
  Output:
    rotationID
    '''
    conn, c = openDB('crop.db')
    if c:
        c1=c.execute("select max(rotationID) from pastruns")
        c1_row = c1.fetchone()
        if c1_row[0] != None:
            lastRotationID = c1_row[0]
            rotationID = int(lastRotationID) + 1
        else:
            rotationID = 1
        return rotationID

def read_simulationID():
    '''
    Returns next simulationID
    Input:
    Output:
    simulationID
    '''
    conn, c = openDB('crop.db')
    if c:
        c1=c.execute("select max(id) from pastruns")
        c1_row = c1.fetchone()
        if c1_row[0] != None:        
            simulationID = c1_row[0] 
        else:
            simulationID = 1
        conn.close()        
        return simulationID

def read_prevsimulationID():
    '''
    Returns next simulationID
    Input:
    Output:
    simulationID
    '''
    conn, c = openDB('crop.db')
    if c:
        c1=c.execute("select max(id) from pastruns")
        c1_row = c1.fetchone()
        if c1_row[0] != None:        
            simulationID = c1_row[0] - 1
        else:
            pass
        conn.close()        
        return simulationID


def extract_pastrunsExpSys(prevsimulationID):    
    '''
  Returns a tuple with last pastrun in the database.
  Input:
  Output:
    Tuple with complete pastruns information.
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        query = 'select id, site, soil, stationtype, weather, treatment, startyear, endyear, waterstress, nitrostress, tempVar, RainVar, CO2Var from pastruns where id = ?'
        param = (prevsimulationID, )
        df = pd.read_sql_query(query,conn, params = param)
      #  print(df['weather'])
   
        conn.close()
    #    print(df)
        return df

def getTreatmentID(treatmentname, experimentname, cropname):
    '''
  Get treatmentID based on treatment name, experiment name and crop name.
  Input:
    treatmentname
    experimentname
    cropname
  Output:
    treatmentID
    '''
    conn, c = openDB('crop.db')
    if c:
        #print("cropname=",cropname)
        record_tuple =(treatmentname,experimentname,cropname)
        c1=c.execute("SELECT tid FROM treatment where name = ? and t_exid = (select exid from experiment where name =? and crop = ?)",record_tuple)
        c1_row = c1.fetchone()
        treatmentID = ""
        if c1_row != None:
            treatmentID = c1_row[0]
        return treatmentID
            

def check_and_update_treatmentDB(treatmentname, experimentname, cropname):
    '''
  Check if treatment already exist in the database and if it is new insert the new treatment and create the default operations
  related with this treatment.  The default operations are Simulation Start, Sowing, Harvest ans Simulation End.
  Input:
    treatmentname
    experimentname
    cropname
  Output:
    '''
    conn, c = openDB('crop.db')
    record_tuple =(treatmentname,experimentname,cropname)
    if c:
        #print("cropname=",cropname)
        record_tuple =(treatmentname,experimentname,cropname)
        if len(experimentname) > 0:
            treatmentID = getTreatmentID(treatmentname,experimentname,cropname)
            if treatmentID == "":
                c2 = c.execute("SELECT exid, name FROM experiment where name = ? and crop = ?",record_tuple[1:])
                c2_row = c2.fetchone()
                if c2_row !=None:
                    t_exid = c2_row[0] #str(query2.value(0))
                    #insert
                    record_tuple = (t_exid,treatmentname)
                    c.execute("insert into treatment (t_exid, name) values (?,?)",record_tuple) # auto increment of tid
                    conn.commit()
                    # here we insert default operations of (Simulation Start and sowing). Read these 3 operations from 
                    # default_operation table and insert them.
                    # Populate Simulation Start and Sowing with today date
                    now = datetime.now()
                    yesterday_date = (now - timedelta(1)).strftime('%m/%d/%Y')
                    in5days_date = (now + timedelta(5)).strftime('%m/%d/%Y')
                    in7days_date = (now + timedelta(7)).strftime('%m/%d/%Y')
                    in60days_date = (now + timedelta(60)).strftime('%m/%d/%Y')
                    in65days_date = (now + timedelta(65)).strftime('%m/%d/%Y')

                    if(cropname == "fallow"):
                        initCond_record = [6.5,0,0,5,0.65,0.5,75,"fallow",0]
                    else:
                        initCond_record = [6.5,0,0,5,0.65,0.5,75,"",0]
                    tillage_record = ["No tillage"]
                    fert_record = []
                    fertNut_record = []
                    PGR_record = []
                    SR_record = []
                    irr_record = []

                    op_id = -10 # This indicates that the record is new
                    new_record = ['Simulation Start',yesterday_date]
                    check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    new_record = ['Tillage','']
                    check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    if(cropname != "fallow" and cropname != "cotton"):
                        new_record = ['Sowing',in5days_date]
                        check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    if(cropname != "fallow"):
                        new_record = ['Harvest',in60days_date]
                        check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    new_record = ['Simulation End',in65days_date]
                    check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    if(cropname != "maize" and cropname != "fallow"):
                        new_record = ['Emergence',in7days_date]
                        check_and_update_operationDB(op_id, treatmentname, experimentname, cropname, new_record, \
                                                 initCond_record, tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_record)

                    conn.commit()
                    conn.close()
                    return True
            else: # data exist, so not inserting
                return False
        return False



def copy_treatmentDB(treatmentname, experimentname, cropname, newtreatmentname):
    '''
  Copy current treatment with all its operations to a new treatment. 
  Input:
    treatmentname
    experimentname
    cropname
    newtreatmentname
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        treatmentID = getTreatmentID(newtreatmentname,experimentname,cropname)
        # Treatment with this name does not exist, so we can insert it 
        if treatmentID == "":
            t_id = getTreatmentID(treatmentname,experimentname,cropname)
            record_tuple = (experimentname,cropname)
            c2 = c.execute("SELECT exid, name FROM experiment where name = ? and crop = ?",record_tuple)
            c2_row = c2.fetchone()
            t_exid = c2_row[0]
            # insert new treatment
            record_tuple = (t_exid,newtreatmentname)
            c.execute("insert into treatment (t_exid, name) values (?,?)",record_tuple)
            conn.commit()
            # Get new treatment id
            c1 = c.execute("SELECT tid FROM treatment where t_exid = ? and name = ?",record_tuple)
            c1_row = c1.fetchone()
            new_t_id = c1_row[0]
            # Copy the operations from current treatment to new treatment 
            # First need to get all operations related with original treatment
            origOp = c.execute("select opID, name, odate from operations where o_t_exid=?",(t_id,))
            origOp_rows = origOp.fetchall()
            # Insert each operation
            for origOp_row in origOp_rows:
                c.execute("insert into operations (o_t_exid,name,odate) values (?,?,?)",(new_t_id,origOp_row[1],origOp_row[2],))
                # Find new opID
                nOpID = c.execute("select opID from operations where o_t_exid=? and name=? and odate=?",(new_t_id,\
                                   origOp_row[1],origOp_row[2],))
                nOpID_row = nOpID.fetchone()
                newOpID = nOpID_row[0]
           #     print("################################################")
            #    print(newOpID)
            
                if(origOp_row[1] == "Simulation Start"):
                    c.execute("insert into initCondOp (opID,pop,autoirrigation,xseed,yseed,cec,eomult,rowSpacing,cultivar,seedpieceMass) \
                               select ?, pop, autoirrigation, xseed, yseed, cec, eomult, rowSpacing, cultivar, seedpieceMass from \
                               initCondOp where opID=?",(newOpID, origOp_row[0],))
                elif(origOp_row[1] == "Tillage"):
                    c.execute("insert into tillageOp (opID,tillage) select ?, tillage from tillageOp where opID=?",(newOpID, origOp_row[0],))                 
                elif(origOp_row[1] == "Fertilizer"):
                    c.execute("insert into fertilizationOp (opID,fertilizationClass,depth) select ?, fertilizationClass, depth from \
                               fertilizationOp where opID=?",(newOpID, origOp_row[0],))
                    fertNut = c.execute("select nutrient, nutrientQuantity from fertNutOp where opID=?",(origOp_row[0],))
                    fertNut_rows = fertNut.fetchall()
                    for fertNut_row in fertNut_rows:
                        c.execute("insert into fertNutOp (opID,nutrient,nutrientQuantity) values (?,?,?)",(newOpID,fertNut_row[0],fertNut_row[1],))
                elif(origOp_row[1] == "Plant Growth Regulator"):
                    c.execute("insert into PGROp (opID,PGRChemical,applicationType,bandwidth,applicationRate,PGRUnit) select ?,PGRChemical,\
                               applicationType,bandwidth,applicationRate,PGRUnit from PGROp where opID=?",(newOpID, origOp_row[0],))                 
                elif(origOp_row[1] == "Surface Residue"):
                    c.execute("insert into surfResOp (opID,residueType,applicationType,applicationTypeValue) select ?,residueType,applicationType,\
                               applicationTypeValue from surfResOp where opID=?",(newOpID, origOp_row[0],))  
                elif(origOp_row[1] == "Irrigation"):
                    params = (newOpID, origOp_row[0])
                   # print("CVCVCVCV")
                  # print(params)
                    #c.execute("insert into irrigationDetails (opID,o_t_exid, irrigationClass) select ?, o_t_exid, irrigationClass \
                   # from irrigationDetails where opID=?",(newOpID, new_t_id, origOp_row[0],)) 
                    c.execute("INSERT INTO irrigationDetails (opID, o_t_exid, irrigationClass) " "SELECT ?, ?, irrigationClass " \
                   "FROM irrigationDetails "
                    "WHERE opID = ?",
                    (newOpID, new_t_id, origOp_row[0]) )
 
                    # Fetch the irrigationClass values for the given opID
                    c.execute("SELECT irrigationClass FROM irrigationDetails WHERE opID = ?", (newOpID,))
                    irrigation_class = c.fetchall()
                  #  print(irrigation_class)
                    if irrigation_class[0][0] == 'Sprinkler':
                        c.execute("insert into Irrig_pivotOp (opID,irrigationClass,AmtIrrAppl) select ?,irrigationClass,AmtIrrAppl \
                        from Irrig_pivotOp where opID=?",(newOpID, origOp_row[0],))  
                        
                    elif irrigation_class[0][0] == "FloodH":
                        c.execute("insert into Irrig_floodH (opID,irrigationClass,pondDepth, irrStartD, startH, irrStopD, stopH) select ?,irrigationClass,pondDepth, irrStartD, startH, \
                        irrStopD, stopH from Irrig_floodH where opID=?",(newOpID, origOp_row[0],))  
                        
                    elif irrigation_class[0][0] == "FloodR":
                        c.execute("insert into Irrig_floodR (opID,irrigationClass,pondDepth, rate, irrStartD, startH, irrStopD, stopH) select ?,irrigationClass, pondDepth, rate, irrStartD, startH, \
                        irrStopD, stopH from Irrig_floodR where opID=?",(newOpID, origOp_row[0],))  
                    new_t_id
            conn.commit()
            conn.close()
            return True
        else:
            return False


def check_and_delete_operationDB(op_id,op_name):
    '''
  Deletes the selected entry from the operation tables.
  Input:
    op_id = operation id
    op_name = operation name
  Output:
    '''   
    conn, c = openDB('crop.db')
    if c:
        c.execute("delete from operations where opID=?",(op_id,))
        if(op_name == "Simulation Start"):
            c.execute("delete from initCondOp where opID=?",(op_id,))
        elif(op_name == "Tillage"):
            c.execute("delete from tillageOp where opID=?",(op_id,))                 
        elif(op_name == "Fertilizer"):
            c.execute("delete from fertilizationOp where opID=?",(op_id,))
            c.execute("delete from fertNutOp where opID=?",(op_id,))
        elif(op_name == "Plant Growth Regulator"):
            c.execute("delete from PGROp where opID=?",(op_id,))
        elif(op_name == "Surface Residue"):
            c.execute("delete from surfResOp where opID=?",(op_id,))
        conn.commit()
        conn.close()
        return True


def check_and_update_operationDB(op_id,treatmentname, experimentname, cropname, operation_record, initCond_record, \
                                 tillage_record, fert_record, fertNut_record, PGR_record, SR_record, irr_param):
    '''
  Check if operation exist, if it exist the record is updated otherwise a new record is inserted into 
  operations table.
  Input:
    op_id = operation id
    treatmentname 
    experimentname
    cropname
    operation_record
    initCond_record
    tillage_record
    fert_record
    fertNut_record
    PGR_record
    SR_record
    irrAmt_record
  Ouput:
    '''
    conn, c = openDB('crop.db')
   # print("irr_param: ", irr_param)
   # print("operation_record: ",operation_record)
    if c:
        op_id = int(op_id)
        # If op_id=-10, it means it is a new operation record so we need to find treatment id and experiment id
        
        o_t_exid = getTreatmentID(treatmentname,experimentname,cropname)
        # tables experiment & treatment are expected to have some value for tid and t_exid.
        record_tuple = (o_t_exid,) + tuple(operation_record)

       
        
        # Need to do date validation before inserting or updating a operation for "Tillage", "Fertilizer" and "Simulation End"
        if((operation_record[0] == "Simulation End" and op_id != -10) or (operation_record[0] == "Fertilizer") \
           or (operation_record[0] == "Plant Growth Regulator") or (operation_record[0] == "Irrigation") or (operation_record[0] == "Tillage" and tillage_record[0] != "No tillage")):
           validate_date(o_t_exid,operation_record[0],operation_record[1]) 

        if(op_id != -10):
            record_tuple2 = record_tuple + (op_id,)
            if operation_record[0] != 'Irrigation':              
                
                c.execute("update operations set o_t_exid =?, name=?, odate=? where opID = ? ",record_tuple2)
                conn.commit()
                # We need to update the related table to the operation like "Simulation Start" -> initCondOp table, "Tillage"
                # -> tillageOp table and "Fertilizer" -> fertilizerOp and fertNutOp tables.
                if operation_record[0] == "Simulation Start":
                    initCond_record = tuple(initCond_record) + (op_id,)
                    c.execute("update initCondOp set pop=?, autoirrigation=?, xseed=?, yseed=?, cec=?, eomult=?, rowSpacing=?, cultivar=?, \
                                seedpieceMass=? where opID=?", initCond_record)
                elif operation_record[0] == "Tillage":
                    tillage_record = tuple(tillage_record) + (op_id,)
                    c.execute("update tillageOp set tillage=? where opID=?", tillage_record)
                elif operation_record[0] == "Fertilizer":
                    fert_record = tuple(fert_record) + (op_id,)
                    c.execute("update fertilizationOp set fertilizationClass=?, depth=? where opID =?", fert_record)
                    for i in range(0,len(fertNut_record),2):
                        fertNut =  (fertNut_record[i],fertNut_record[i+1],op_id,)
                        c.execute("update fertNutOp set nutrientQuantity=? where nutrient=? and opID=?", fertNut)
                elif operation_record[0] == "Plant Growth Regulator":
                    PGR_record = tuple(PGR_record) + (op_id,)
                    c.execute("update PGROp set PGRChemical=?, applicationType=?, bandwidth=?, applicationRate=?, PGRUnit=? where opID=?", PGR_record)
                elif operation_record[0] == "Surface Residue":
                    SR_record = tuple(SR_record) + (op_id,)
                    c.execute("update surfResOp set residueType=?, applicationType=?, applicationTypeValue=? where opID=?", SR_record)
            else: # operation_record[0] == "Irrigation":    
                
                if len(irr_param) == 2:
                    c.execute("update operations set o_t_exid =?, name=?, odate=? where opID = ? ",record_tuple2)
                    irrAmt_record = tuple(reversed(irr_param)) + (op_id,)
                    c.execute("update Irrig_pivotOp set irrigationClass=?, AmtIrrAppl=?  where opID=?", irrAmt_record)
                else:                       
                    if irr_param[-1] == 'FloodH':
                        record_tuple3 =  (op_id,) + record_tuple[:-1] +  (irr_param[1],)     
                       
                        c.execute("update operations set o_t_exid =?, name=?, odate=? where opID = ? ",record_tuple3)
                        irr_param_list = ['FloodH']+ irr_param[:-1]
                        irr_record = tuple(irr_param_list) + (op_id,)  
                    
                        for i in range (0, len(irr_record),7):
                            hour1 = irr_record[i+3].split(':')[0].lstrip('0')
                            hour2 = irr_record[i+5].split(':')[0].lstrip('0')
                            irr_rec = (irr_record[i], irr_record[i+1],irr_record[i+2],hour1,irr_record[i+4],hour2, op_id,)
                           
                            c.execute("update Irrig_floodH set irrigationClass=?, pondDepth=?, irrStartD=?, startH=?, irrStopD=?, stopH=? where opID=?", irr_rec)                       
                    else:                      
                        record_tuple4 = (op_id,) + record_tuple[:-1] +  (irr_param[1], )                              
                        c.execute("update operations set o_t_exid =?, name=?, odate=? where opID = ? ",record_tuple4)
                        irr_param_list = ['FloodR']+ [irr_param[0]] + [irr_param[5]] + irr_param[1:5]
                      
                        irr_record = tuple(irr_param_list) + (op_id,)  
                     
                        hour1 = irr_record[4].split(':')[0].lstrip('0')
                        hour2 = irr_record[6].split(':')[0].lstrip('0')
                        irr_rec = (irr_record[0], irr_record[1],irr_record[2],irr_record[3], hour1,irr_record[5],hour2, op_id,)
                        
                        c.execute("update Irrig_floodR set irrigationClass=?, pondDepth=?, rate=?, irrStartD=?, startH=?, irrStopD=?, stopH=? where opID=?", irr_rec)  
                    
                
            conn.commit()
        else:
            if operation_record[0] != 'Irrigation':
                c.execute("insert into operations (o_t_exid, name, odate) values (?,?,?)",record_tuple)
                conn.commit()
                
                # Need to find the id for this operation
                c1 = c.execute("select opID from operations where o_t_exid=? and name=? and odate=?",record_tuple)
                c1_row = c1.fetchone()
                op_id = c1_row[0]

                if operation_record[0] == "Simulation Start":
                    initCond_record = (op_id,) + tuple(initCond_record)
                   # c.execute("SELECT opID FROM initCondOp WHERE opID = ?", (op_id,)) 
                    #if c.fetchone() is not None: 
                     #   print("Duplicate entry found for opID:", op_id) 
                        
                    c.execute("insert into initCondOp (opID, pop, autoirrigation, xseed, yseed, cec, eomult, rowSpacing, cultivar,\
                               seedpieceMass) values (?,?,?,?,?,?,?,?,?,?)", initCond_record)
                elif operation_record[0] == "Tillage":
                    tillage_record = (op_id,) + tuple(tillage_record)
                    c.execute("insert into tillageOp (opID, tillage) values (?,?)", tillage_record)
                elif operation_record[0] == "Fertilizer":
                    fert_record = (op_id,) + tuple(fert_record)
                    c.execute("insert into fertilizationOp (opID, fertilizationClass, depth) values (?,?,?)", fert_record)
                    for i in range(0,len(fertNut_record),2):
                        fertNut =  (op_id,fertNut_record[i],fertNut_record[i+1],)
                        c.execute("insert into fertNutOp (opID, nutrientQuantity, nutrient) values (?,?,?)", fertNut)
                elif operation_record[0] == "Plant Growth Regulator":
                    PGR_record = (op_id,) + tuple(PGR_record)
                    c.execute("insert into PGROp (opID,PGRChemical,applicationType,bandwidth,applicationRate,PGRUnit) values (?,?,?,?,?,?)", PGR_record)
                elif operation_record[0] == "Surface Residue":
                    SR_record = (op_id,) + tuple(SR_record)
                    c.execute("insert into surfResOp (opID,residueType,applicationType,applicationTypeValue) values (?,?,?,?)", SR_record)
                    
            else : # operation_record[0] == "Irrigation":
                irrigation_class_value = irr_param[-1]
            
                if len(irr_param) == 2:
                    c.execute("insert into operations (o_t_exid, name, odate) values (?,?,?)",record_tuple)   
                    last_id =   c.lastrowid
                    opID_operation = last_id 
                    c.execute("insert into irrigationDetails (opID,o_t_exid, irrigationClass) VALUES (?, ?, ?)", (opID_operation, o_t_exid, irrigation_class_value))
                    irr_param = (opID_operation ,) + tuple(reversed(irr_param))   
                    c.execute("insert into Irrig_pivotOp (opID, irrigationClass, AmtIrrAppl) values (?,?,?)", irr_param)
                else:                       
                    if irr_param[-1] == 'FloodH':
                        record_tuple3 = record_tuple[:-1] +  (irr_param[1],)         
                        c.execute("insert into operations (o_t_exid, name, odate) values (?,?,?)",record_tuple3)
                        last_id =   c.lastrowid
                        opID_operation = last_id 
                        c.execute("insert into irrigationDetails (opID, o_t_exid, irrigationClass) VALUES (?, ?, ?)", (opID_operation, o_t_exid, irrigation_class_value))
                        irr_record = (opID_operation ,) + (irr_param[-1],) + tuple(irr_param[:-1]) 
                        #print(irr_record)
                        
                        hour1 = int(irr_record[4].split(':')[0])
                        hour2 = int(irr_record[6].split(':')[0])
                        irr_record = tuple(irr_record[0:4]) + (hour1, ) +  (irr_record[5], ) + (hour2, )
                        
                        c.execute("insert into Irrig_floodH (opID, irrigationClass, pondDepth, irrStartD, startH, irrStopD, stopH) values (?,?,?,?,?,?,?)", irr_record)
                    else:
                       # print("1111")
                     #   print(irr_param)
                        irr_param = [irr_param[0], irr_param[5], irr_param[1], irr_param[2], irr_param[3], irr_param[4], irr_param[6]]
                      #  print(irr_param)
                        record_tuple4 = record_tuple[:-1] +  (irr_param[2],)         
                        c.execute("insert into operations (o_t_exid, name, odate) values (?,?,?)",record_tuple4)
                        last_id =   c.lastrowid
                        opID_operation = last_id 
                        c.execute("insert into irrigationDetails (opID, o_t_exid, irrigationClass) VALUES (?, ?, ?)", (opID_operation, o_t_exid, irrigation_class_value))
                        irr_record = (opID_operation ,) + (irr_param[-1],) + tuple(irr_param[:-1])   
                        
                        hour3 = int(irr_record[5].split(':')[0])
                        hour4 = int(irr_record[7].split(':')[0])
                        irr_record = tuple(irr_record[0:5]) + (hour3, ) +  (irr_record[6], ) + (hour4, )
                        
                        c.execute("insert into Irrig_floodR (opID, irrigationClass, pondDepth, rate, irrStartD, startH, irrStopD, stopH) values (?,?,?,?,?,?,?,?)", irr_record)
                
            conn.commit()
        conn.close()
          # else:
           #    pass      
        return True


def validate_date(o_t_exid,op_name,date):
    '''
  Validate date for a specific operation and send an error message to the user in case a problem is found. 
  Input:
    o_t_exid
    op_name
    date
  Output:
    '''
    conn, c = openDB('crop.db')
    
    if c:
        err_string = ""
        date = dt.strptime(date,"%m/%d/%Y")
    
        # Check if there is any operation with valid date
        search_operation = (o_t_exid,)
     
        c.execute("SELECT name, odate, DATE(year||'-'||month||'-'||day) as dt_frmtd FROM (SELECT *, CASE WHEN LENGTH(substr(odate, 1, \
                   instr(odate,'/')-1)) = 2 THEN substr(odate, 1, instr(odate,'/')-1) ELSE '0'|| substr(odate, 1, instr(odate,'/')-1) END as month, \
                   CASE WHEN LENGTH(substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, instr(odate,'/')+1),'/')-1)) = 2 THEN \
                   substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, instr(odate,'/')+1),'/')-1) ELSE '0'|| \
                   substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, instr(odate,'/')+1),'/')-1) END AS day, CASE WHEN \
                   LENGTH(substr(substr(odate, instr(odate,'/')+1), instr(substr(odate, instr(odate,'/')+1),'/')+1)) = 4 THEN \
                   substr(substr(odate, instr(odate,'/')+1), instr(substr(odate, instr(odate,'/')+1),'/')+1) END AS year FROM operations) where \
                   o_t_exid=?", search_operation)

        c_row = c.fetchall()
     #   print(c_row)
        if c_row != None:
            for record in c_row:
                if(record[1] != ""):
                    op_date = dt.strptime(record[1],'%m/%d/%Y')
                    op_date_string = op_date.strftime("%b %d, %Y")
                  
                    if(record[0] == "Simulation Start"):
                        if(date <= op_date):
                            err_string = "Date should be greater then Simulation Start date (%s)." % str(op_date_string)
                            
                    elif(record[0] == "Sowing"):
                        if(op_name == "Harvest" or op_name == "Simulation End"):
                            if(date <= op_date):
                                err_string += "Date should be greater then sowing date (%s)." % str(op_date_string)
                        if(op_name == "Tillage"):
                            if(date > op_date):
                                err_string += "Date should be lower then sowing date (%s)." % str(op_date_string)
                    elif(record[0] == "Harvest"):
                        if(op_name == "Simulation End"):
                            if(date <= op_date):
                                err_string += "Date should be greater then harvest date (%s)." % str(op_date_string)
                    elif(record[0] == "Simulation End"):
                        if(op_name != "Simulation End"):
                            if(date >= op_date):
                                err_string += "Date should be less then Simulation End date (%s)." % str(op_date_string)
        conn.close()
    if(err_string != ""):        
        return messageUser(err_string)       
    return True


def getme_date_of_first_operationDB(treatmentname, experimentname ,cropname):
    '''
  It will extract operation dates for a particular treatment under given experiment and given crop
  Input:
    treatmentname
    experimentname
    cropname
  Output:
    '''
    rlist =[]
   
    conn, c = openDB('crop.db')
    if c:
        search_str0 = treatmentname     
        search_str1 = experimentname 
        search_str2 = cropname     
        record_tuple =(search_str0,search_str1,search_str2)
        if len(search_str1) > 0:        
            c1=c.execute("SELECT tid, t_exid FROM treatment where name = ? and t_exid = ( select exid from experiment where name =? \
                          and crop = ?)",record_tuple)
            c1_row = c1.fetchone()
            # tables experiment & treatment are expected to have some value for tid and t_exid.
            if c1_row !=None:
                o_t_exid = c1_row[0]
                search_record_tuple = (o_t_exid,)
                c2=c.execute("SELECT odate FROM operations where name='Simulation Start' and o_t_exid=?",search_record_tuple)
                c2_row = c2.fetchone()
                rlist.append(c2_row[0]) 
                conn.close()
                return rlist
 
        return False


def read_operation_timeDB2(operationname, treatmentname, experimentname ,cropname):
    '''
  Checks if the operations exist, then extract the time info based on operation, treatment, experiment and
  crop name.
  Input: 
    treatmentname
    experimentname
    cropname
    operationname.
  Output: 
    operationname date info
    '''
    rtuple =() 
    conn, c = openDB('crop.db')
    if c:
        record_tuple =(treatmentname,experimentname,cropname)
        check_str = re.sub(' ','',operationname)
        if len(experimentname) > 0 and len(check_str) > 0:        
            c1=c.execute("SELECT tid, t_exid FROM treatment where name = ? and t_exid = ( select exid from experiment where name =? \
                          and crop = ?)",record_tuple)
            c1_row = c1.fetchone()
            # tables experiment & treatment are expected to have some value for tid and t_exid.
            if c1_row !=None:
                o_t_exid = c1_row[0]
                #search and extract            
                record_tuple = (o_t_exid, operationname)            
                c2 = c.execute("SELECT odate, DATE(year||'-'||month||'-'||day) as dt_frmtd FROM (SELECT *, CASE WHEN LENGTH(substr(odate, 1, \
                                instr(odate,'/')-1)) = 2 THEN substr(odate, 1, instr(odate,'/')-1) ELSE '0'|| substr(odate, 1, instr(odate,'/')-1) \
                                END as month, CASE WHEN LENGTH(substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, \
                                instr(odate,'/')+1),'/')-1)) = 2 THEN substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, \
                                instr(odate,'/')+1),'/')-1) ELSE '0'|| substr(substr(odate, instr(odate,'/')+1), 1, instr(substr(odate, \
                                instr(odate,'/')+1),'/')-1) END AS day, CASE WHEN LENGTH(substr(substr(odate, instr(odate,'/')+1), \
                                instr(substr(odate, instr(odate,'/')+1),'/')+1)) = 4 THEN substr(substr(odate, instr(odate,'/')+1), \
                                instr(substr(odate, instr(odate,'/')+1),'/')+1) END AS year FROM operations) where o_t_exid = ? and name = ? \
                                order by dt_frmtd", record_tuple)
                c2_row = c2.fetchone()
                if c2_row != None:
                    rtuple = c2_row[0]

        conn.close()
        return rtuple


def readOpDetails(operationid, operationName):
    '''
  Extract operation info based on operation id
  Input: 
    operationid
    operationName
  Output: 
    tuple with operation info
    '''
    rlist = [] 
    conn, c = openDB('crop.db')
    if c:
        #search and extract            
        record_tuple = operationid, 
        # Based  on operationName a diferent tables will be queried
        if operationName == 'Simulation Start':          
            c1 = c.execute("select o.opID, name, odate, pop, autoirrigation, xseed, yseed, cec, eomult, rowSpacing, \
                            cultivar, seedpieceMass from operations o, initCondOp ico where o.opID = ico.opID and \
                            o.opID = ?",record_tuple)
        elif operationName == 'Tillage':
            c1 = c.execute("select o.opID, name, odate, tillage from operations o, tillageOp t where o.opID = t.opID \
                            and o.opID = ?",record_tuple)
        elif operationName == 'Fertilizer':
            c1 = c.execute("select o.opID, name, odate, fertilizationClass, depth, nutrient, nutrientQuantity \
                            from operations o, fertilizationOp fo, fertNutOp fno where o.opID = fo.opID and \
                            o.opID = fno.opID and o.opID = ?",record_tuple)
        elif operationName == 'Plant Growth Regulator':
            c1 = c.execute("select o.opID, name, odate, PGRChemical, Po.applicationType, bandwidth, applicationRate, \
                            Po.PGRUnit, Pat.code as appTypeCode, Pu.code as appUnitCode from operations o, PGROp Po, \
                            PGRApplType Pat, PGRUnit Pu where o.opID = Po.opID and Po.applicationType = Pat.applicationType \
                            and Po.PGRUnit=Pu.PGRUnit and o.opID = ?",record_tuple)
        elif operationName == "Surface Residue":
            c1 = c.execute("select o.opID, name, odate, residueType, applicationType, applicationTypeValue \
                            from operations o, surfResOp sro where o.opID = sro.opID and o.opID = ?",record_tuple)
        elif operationName =="Irrigation":
         #    print("XXXXXXXXX")
          #   print(record_tuple)
             c2 = c.execute("select irrigationClass from irrigationDetails where opID = ?", record_tuple)
             c2_row = c2.fetchall()
             rlist2 = [c2_row_record for c2_row_record in c2_row]
       
         #    print(rlist2)
             if rlist2[0][0]=='Sprinkler':
                c1 = c.execute("select o.opID, name, irrigationClass, odate, AmtIrrAppl from operations o, Irrig_pivotOp Iro where o.opID = Iro.opID and o.opID = ?", record_tuple)
             elif rlist2[0][0]=='FloodH':
                c1 = c.execute("select o.opID, name,  irrigationClass, pondDepth, irrStartD, startH, irrStopD, stopH from operations o, Irrig_floodH Iro where o.opID = Iro.opID and o.opID = ?", record_tuple) 
             elif rlist2[0][0]=='FloodR':
                c1 = c.execute("select o.opID, name, irrigationClass, pondDepth, rate, irrStartD, startH, irrStopD, stopH from operations o, Irrig_floodR Iro where o.opID = Iro.opID and o.opID = ?", record_tuple) 
        else:
            c1 = c.execute("select opID, name, odate from operations where opID = ?",record_tuple)

        c1_row = c1.fetchall()
      #  for c1_row_record in c1_row:
     #       rlist.append(c1_row_record)
        rlist = [c1_row_record for c1_row_record in c1_row]
        conn.close()
       # print(rlist)
        return rlist


def read_treatmentDB(crop,experiment):
    '''
  Returns treatment name based on experiment name.
  Input:
    crop
    experiment
  Output:
    return treatment name
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        record_tuple = (experiment, crop)
        c1 = c.execute("SELECT name FROM treatment where t_exid = (select exid from experiment where name = ? and crop = ?)",record_tuple)    
        c1_row = c1.fetchall()
        if c1_row != None:
            for c1_row_record in c1_row:
                rlist.append(c1_row_record[0])
        
        conn.close()  
        return rlist


def read_operationsDB(crop,eitem,titem):
    '''
  Returns all operations in ascending order by date based on experiment id and treatment id.
  Input:
    eitem = experiment id
    titem = treatment id
  Output:
    Tuple with complete operation information sorted by date in ascending order
    '''
    rlist =[] # list
    conn, c = openDB('crop.db')
    if c:
        if len(eitem) > 0:
            c1 = c.execute("SELECT name, odate, opID, DATE(year||'-'||month||'-'||day) as dt_frmtd \
                           FROM (SELECT *, CASE WHEN LENGTH(substr(odate, 1, instr(odate,'/')-1)) = 2 THEN substr(odate, 1, instr(odate,'/')-1) \
                           ELSE '0'|| substr(odate, 1, instr(odate,'/')-1) END as month, CASE WHEN LENGTH(substr(substr(odate, instr(odate,'/')+1), 1, \
                           instr(substr(odate, instr(odate,'/')+1),'/')-1)) = 2 THEN substr(substr(odate, instr(odate,'/')+1), 1, \
                           instr(substr(odate, instr(odate,'/')+1),'/')-1) ELSE '0'|| substr(substr(odate, instr(odate,'/')+1), 1, \
                           instr(substr(odate, instr(odate,'/')+1),'/')-1) END AS day, CASE WHEN LENGTH(substr(substr(odate, instr(odate,'/')+1), \
                           instr(substr(odate, instr(odate,'/')+1),'/')+1)) = 4 THEN substr(substr(odate, instr(odate,'/')+1), instr(substr(odate, \
                           instr(odate,'/')+1),'/')+1) END AS year FROM operations) where o_t_exid = (select tid from treatment where name ='%s' AND \
                           t_exid =(select exid from experiment where name ='%s' and crop ='%s')) order by dt_frmtd"%(titem,eitem,crop))            
            c1_row = c1.fetchall()
       #     if c1_row != None:
        #        for c1_row_record in c1_row:
        #            tmp_list = [c1_row_record[0],c1_row_record[1],c1_row_record[2],c1_row_record[3]]
        #            rlist.append(tmp_list)
            
            rlist = [[c1_row_record[0],c1_row_record[1],c1_row_record[2],c1_row_record[3]] for c1_row_record in c1_row if c1_row != None]
        conn.close()
        return rlist


def read_fertilizationClass():
    '''
  Returns all fertilizations.
  Input:
  Output:
    Fertilization list.
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT fertilizationClass from fertilizationClass order by fertilizationClass")
        c1_row = c1.fetchall()
    #    if c1_row != None:
     #       for c1_row_record in c1_row:
      #          rlist.append(c1_row_record[0])
        rlist = [c1_row_record[0] for c1_row_record in c1_row if c1_row != None]
        conn.close()
        return rlist

def read_irrigationClass():
    '''
    Returns all irrigation data.
    Input:
    Output:
    Irrigation list.
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT  irrigationClass from  irrigationClass order by  irrigationClass")
        c1_row = c1.fetchall()
       # print(c1_row)
   #     if c1_row != None:
   #         for c1_row_record in c1_row:
    #            rlist.append(c1_row_record[0])
        rlist = [c1_row_record[0] for c1_row_record in c1_row if c1_row != None]
       # print("rlist", rlist)
        conn.close()
        return rlist

def read_FaqDB(tabname,cropname):
    '''
  Returns FAQ information based on tabname
  Input:
    tabname
  Output:
    Tuple with FAQ information for a particular tab.
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        if tabname == None:
            c1= c.execute("SELECT id, tabname, question, answer FROM Faq")            
        else:
            if(tabname=="cultivar"):
                tabname = "Cultivar_" + cropname
            record_tuple = (tabname,)
            c1= c.execute("SELECT distinct id, tabname, question, answer FROM Faq where tabname='general' or tabname like ?",record_tuple)            

        c1_row = c1.fetchall()
      #  if c1_row != None:
      #      for c1_row_record in c1_row:                
      #          rlist.append(c1_row_record)
        rlist = [c1_row_record for c1_row_record in c1_row if c1_row != None]
        conn.close()
        return rlist

    
def read_sitedetailsDB():
    '''
  Returns list with site names.
  Input:
  Output:
    Tuple with sitenames list.
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        c1= c.execute("SELECT id, sitename FROM sitedetails order by lower(sitename)")            
        c1_row = c1.fetchall()
        if c1_row != None:
            for c1_row_record in c1_row:                
                rlist.append(c1_row_record[1])
        conn.close()
        return rlist


def read_soilOMDB(soilname): 
    '''
  Returns soil information from soil_long table based on soilname.
  Input:
    soilname
  Output:
    Tuple with soil information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select rowid, Sand, Silt, Clay, BD, OM_pct, TH33, TH1500 FROM soil_long where o_sid = (SELECT id FROM soil \
                           where soilname = ? )",[soilname])
            c1row = c1.fetchall()
 #           if c1row != None:
 #               for c1rowrecord in c1row:
 #                   rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def read_soilhydroDB(soilname): 
    '''
  Returns soil hydro information from soil_long table based on soilname.
  Input:
    soilname
  Output:
    Tuple with soil information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select thr, ths, tha, th, Alfa, n, Ks, Kk, thk, BD, OM_pct, Sand, Silt FROM soil_long \
                           where o_sid = (SELECT id FROM soil where soilname = ? )",[soilname])
            c1row = c1.fetchall()
          #  if c1row != None:
          #      for c1rowrecord in c1row:
           #         rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def insert_into_soillong(soilname,soilrow):   
    '''
  Insert the soil record on soil_long table based on soilname.
  Input:
    soilname
    soilrow = tuple with soil information to be ingested on soil_long table
  Output:
    '''  
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT id FROM soil where soilname=?",(soilname,))
        c1_row = c1.fetchall()
        if c1_row != []:
            new_tuple = tuple(c1_row[0]) + soilrow    
            qstatus = c.execute("insert into soil_long (o_sid,Bottom_depth,OM_pct,NO3,NH4,HnNew,InitType,Tmpr,Sand,Silt,Clay,BD,\
                                 TH33,TH1500,thr,ths,tha,th,Alfa,n,Ks,Kk,thk,kh,kL,km,kn,kd,fe,fh,r0,rL,rm,fa,nq,cs) \
                                 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0.00007,0.035,0.07,0.2,0.00001,0.6,\
                                 0.2,10.0,50.0,10.0,0.1,8,0.00001)",new_tuple)         
            conn.commit()
        conn.close()
        return True


def read_soillongDB(soilname): 
    '''
  Insert the soil record on soil_long table based on soilname.
  Input:
    soilname
    soilrow = tuple with soil information to be ingested on soil_long table
  Output:
    '''  
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select Bottom_depth,OM_pct,NO3,NH4,HnNew,initType,Tmpr,Sand,Silt,Clay,BD,TH33,TH1500,thr,ths,tha,th,Alfa,n,Ks,\
                           Kk,thk,kh,kL,km,kn,kd,fe,fh,r0,rL,rm,fa,nq,cs FROM soil_long where o_sid = (SELECT id FROM \
                           soil where soilname = ?)",[soilname])
            c1row = c1.fetchall()
         #   if c1row != None:
        #        for c1rowrecord in c1row:
        #            rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def getSiteFromSoilname(soilname): 
    '''
  Select sites that use the same soil type.
  Input:
    soilname
  Output:
    '''  
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("select sitename from soil so, sitedetails si where so.site_id = si.id and soilname=?",[soilname])
            c1_row = c1.fetchone()
            if c1_row != None:
                rlist = list(c1_row)
        conn.close()
        return rlist


def read_soilshortDB(soilname): 
    '''
  Returns more restricted soil information from soil_long table based on soilname
  are not asked from users.
  Input:
    soilname
  Output:
    Tuple with soil information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select Bottom_depth,initType,OM_pct,NO3,NH4,HnNew,Tmpr,Sand,Silt,Clay,BD,TH33,TH1500,thr,ths,tha,th,Alfa,n,Ks,Kk,thk,CO2,O2, N2O FROM soil_long \
                           where o_sid = (SELECT id FROM soil where soilname = ? )",[soilname])      
            c1row = c1.fetchall()
        #    if c1row != None:
        #        for c1rowrecord in c1row:
         #           rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def read_soiltextureDB(soilname): 
    '''
  Returns soil texture information from soil_long table based on soilname
  are not asked from users.
  Input:
    soilname
  Output:
    Tuple with soil information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select Sand,Silt,Clay FROM soil_long where o_sid = (SELECT id FROM soil where soilname = ? )",[soilname])
            c1row = c1.fetchall()
        #    if c1row != None:
         #       for c1rowrecord in c1row:
         #           rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def read_gasDB(): 
    '''
  Returns gas information
  Input:
  Output:
    Tuple with gas information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        c1= c.execute("Select name,EPSI,bTort,Diffusion_Coeff FROM gas order by id")
        c1row = c1.fetchall()
     #   if c1row != None:
      #      for c1rowrecord in c1row:
      #          rlist.append(c1rowrecord)
        rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def read_soilnitrogenDB(soilname):
    '''
  Returns soil nitrogen information from soil_long table based on soilname
  are not asked from users.
  Input:
    soilname
  Output:
    Tuple with soil information
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select kh,kL,km,kn,kd,fe,fh,r0,rL,rm,fa,nq,cs FROM soil_long where o_sid = (SELECT id FROM soil where \
                           soilname = ? )",[soilname])
            c1row = c1.fetchall()
       #     if c1row != None:
       #         for c1rowrecord in c1row:
       #             rlist.append(c1rowrecord)
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def read_soluteDB(id=1): #
    '''
  Returns default solute information to be used in the soil2d solute input file
  Input:
    id
  Output:
    Tuple with solute information
    '''
    rtuple = ()
    conn, c = openDB('crop.db')
    if c:
        if isinstance(id, int):
            c1= c.execute("Select name,EPSI,IUPW,CourMax,Diffusion_Coeff FROM solute where id = ? ",[id])
            c1row = c1.fetchone()
            if c1row != None:
                rtuple = (c1row[0],c1row[1],c1row[2],c1row[3],c1row[4])
        conn.close()
        return rtuple


def read_dispersivityDB(texture): #
    '''
  Return the selected record from the dispersivity table based on texture
  Input:
    texture
  Output:
    Tuple with dispersivity information
    '''
    rtuple = ()
    conn, c = openDB('crop.db')
    if c:
        if texture != "":
            query = "Select alpha FROM dispersivity where texturecl like '%" + texture + "%'"
            c1= c.execute(query)
            c1row = c1.fetchone()
            if c1row != None:
                rtuple = (c1row[0])
        conn.close()
        return rtuple


def read_soillongDB_maxdepth(soilname):
    '''
  Return max Bottom_depth from soil_long based on soilname
  Input:
    soilname
  Output:
    Tuple with max Bottom_depth
    '''
    rlist = 0 #[]
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select max(Bottom_depth) FROM soil_long where o_sid = (SELECT id FROM soil where soilname = ? )",[soilname])
            c1row = c1.fetchone()
            if c1row != None:
                rlist = c1row[0]
        conn.close()
        return rlist 


def delete_soillong(soilname):   
    '''
  Delete the soillong parameters
  Input:
    soilname
  Output:
    '''  
    conn, c = openDB('crop.db')
    if c:
        c1= c.execute("Select o_sid, id from soil_long where o_sid = (Select id FROM soil where soilname =? ORDER by id ASC)",[soilname])
        c1row = c1.fetchall()  
        for c1rowitem in c1row: 
            temp_tuple = (c1rowitem[0],c1rowitem[1])       
            c.execute("delete from soil_long where o_sid=? and id=? ",temp_tuple)
        conn.commit()            
        conn.close()
        return True 


def insert_soilgridratioDB(soilgrid_tuple):   
    '''
  Insert the soilgrid-ratio parameters. Returns the gridratio_id which might be needed for in soil table.
  Input:
    soilgrid_tuple = information to be inserted into gridratio table
  Output:
    next_gridratio_id
    '''  
    conn, c = openDB('crop.db')
    if c:
        #find what would be the id for next entry inside the gridratio table    
        c1= c.execute("Select max(gridratio_id) FROM gridratio")
        c1row = c1.fetchone()
        next_gridratio_id = 1
        if c1row != None:
            next_gridratio_id = c1row[0] +1
    
        new_tuple = (next_gridratio_id,)+ soilgrid_tuple    
        c.execute("insert into gridratio (gridratio_id,SR1,SR2,IR1,IR2,PlantingDepth,XLimitRoot,BottomBC,GasBCTop,GasBCBottom) values (?,?,?,?,?,?,?,?,?,?)",new_tuple)    
        conn.commit()     
        conn.close()
        return next_gridratio_id 
    

def updateBottomBC(soilname,bottomBCVal):   
    '''
  Update BottomBC on gridratio table based on soilname
  Input:
    soilname
    bottomBCVal
  Output:
    '''  
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT o_gridratio_id FROM soil where soilname=?",(soilname,))
        c1_row = c1.fetchone()
        if c1_row != []: #if c1_row != None:
            gridratio_id = ''.join(str(c1_row[0]))
            query = "update gridratio set BottomBC=" + str(bottomBCVal) + " where gridratio_id=" + str(gridratio_id)
            c.execute(query)
            conn.commit()
        conn.close()
        return True


def check_soilDB(soilname,site_id): 
    '''
  Check if soil exist based on soilname.
  Input:
    soilname
  Output:
    id = soil id
    '''  
    rlist = []   
    conn, c = openDB('crop.db')
    if c:
        soiltuple = (soilname,site_id)
        c1= c.execute("SELECT id FROM soil where soilname=? and site_id=?",soiltuple)
        c1row = c1.fetchone()
        if c1row != None:
            rlist.append(c1row[0])
    
        conn.close()
        #print("soilname check", rlist)
        return rlist 			 


def check_and_insert_soilDB(soilname,site_id,gridratio_id):
    '''
  Check if soil already exist based on soilname and if it doesn't exist insert record into soil.
  Input:
    soilname
    gridratio_id
  Output:
    '''  
    rlist = []   
    rlist = check_soilDB(soilname,site_id)
    soiltuple = (soilname,site_id,gridratio_id)
    ###if rlist !=0:
    #print("rlist=",rlist)
    if rlist == []:
        conn, c = openDB('crop.db')
        if c:
            c1= c.execute("insert into soil (soilname, site_id, o_gridratio_id) values (?,?,?)",soiltuple)
            conn.commit()        
            conn.close()
            return True
        else:
            return messageUser("This soilname exists, please use a different name.")


def read_soilDB():    
    '''
  Returns soil list
  Input:
  Output:
    Tuple with soil id and name
    '''  
    rlist = [] #list
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT id, soilname FROM soil order by lower(soilname)")      
        c1_row = c1.fetchall()
    #    if c1_row != None:
     #       for c1_row_record in c1_row:
     #           rlist.append(c1_row_record[1])
        rlist = [c1_row_record[1] for c1_row_record in c1_row if c1_row != None]
        
        conn.close()       
        return rlist


def read_soilgridratioDB(soilname):
    '''
  Returns gridration information based on soilname
  Input:
    soilname
  Output:
    Tuple with gridratio information 
    '''  
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        if len(soilname) > 0:
            c1= c.execute("Select SR1,SR2,IR1,IR2,PlantingDepth,XLimitRoot,BottomBC,GasBCTop,GasBCBottom FROM gridratio where gridratio_id = (SELECT \
                           o_gridratio_id FROM soil where soilname = ? )",[soilname])
            c1row = c1.fetchall()
       #     if c1row != None:
       #         for c1rowrecord in c1row:
        #            rlist.append(c1rowrecord)    
            rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]        
        conn.close()
        return rlist


def read_biologydefault():
    '''
  Returns default biologydefault information to be used in the soil2d biology input file
  Input:
  Output:
    Tuple with biologydefault information
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT dthH, dthL, es, Th_m, tb, QT, dThD, Th_d FROM biologydefault")          
        c1_row = c1.fetchall()
    #    if c1_row != None:
     #       for c1_row_record in c1_row:
      #          rlist.append(c1_row_record)
        rlist = [c1_row_record for c1_row_record in c1_row if c1_row != None]
        conn.close()           
        return rlist


def read_experiment(item):
    '''
  Returns all experiments based on crop name.
  Input:
    item = crop name
  Output:
    Tuple with experiment name and id list
    '''
    rlist =[]
    conn, c = openDB('crop.db')
    if c:
        search_str = item     
        if len(search_str) > 0:
            c1 = c.execute("SELECT exid, name FROM experiment where crop= '%s' order by name;" % (search_str))          
            c1_row = c1.fetchall()
       #     if c1_row != None:
       #         for c1_row_record in c1_row:
       #             rlist.append(c1_row_record[1])     
            rlist = [c1_row_record[1] for c1_row_record in c1_row if c1_row != None]
            conn.close()    
        
        return rlist


def getMulchGeo(nutrient):  
    '''
  Returns tuple with mulch geo information for a particular nutrient
  Input:
    nutrient
  Output:
    Tuple with mulch geo information
    '''
    rlist =() 
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select minHoriSize,diffusionRestriction,longWaveRadiationCtrl,decompositionCtrl,deltaRShort,deltaRLong, \
                        omega,epsilonMulch,alphaMulch,maxStepInPicardIteration,toleranceHead,rhoMulch,poreSpace,maxPondingDepth \
                        from mulchGeo where nutrient=?",[nutrient])
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getMulchDecomp(nutrient):  
    '''
  Returns tuple with mulch decomp information for a particular nutrient
  Input:
    nutrient
  Output:
    Tuple with mulch decomp information
    '''
    rlist =() 
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select contactFraction,alphaFeeding,carbMass,cellMass,lignMass,carbNMass, \
                        cellNMass,lignNMass,carbDecomp,cellDecomp,lignDecomp from mulchDecomp where \
                        nutrient=?",[nutrient])
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist



def getIrrigationData(simulationname, o_t_exid):
    '''
    Returns tuple with amounts of irrigation for a Sprinkler irrigationClass
    Input:
      irrigationClass
    Output:
      Tuple with amounts of irrigation
    '''
    
    rlist=[]
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select o.odate, AmtIrrAppl from operations o, Irrig_pivotOp Ip where o.opID == Ip.opID and o.o_t_exid==? order by o.odate asc", (o_t_exid, ))
        c1row = c1.fetchall()
        if c1row != None:
            rlist = [c1_row_record for c1_row_record in c1row if c1row != None]
        conn.close()
        return rlist
    

def getFloodHData(simulationname, o_t_exid):
    '''
    Returns tuple with amouts of irrigation for Flood_H irrigationClass
    Input:
      irrigationClass
    Output:
      Tuple with amounts of irrigation
    '''
    
    rlist=[]
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select pondDepth, irrStartD, startH, irrStopD, stopH from operations o, Irrig_floodH Ip where o.opID == Ip.opID and o.o_t_exid==? order by o.odate asc", (o_t_exid, ))
        c1row = c1.fetchall()
        if c1row != None:
            rlist = [c1_row_record for c1_row_record in c1row if c1row != None]
        conn.close()
        return rlist
    
def getFloodRData(simulationname, o_t_exid):
    '''
    Returns tuple with amouts of irrigation for Flood_R irrigationClass
    Input:
      irrigationClass
    Output:
      Tuple with amounts of irrigation
    '''
    
    rlist=[]
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select pondDepth, rate, irrStartD, startH, irrStopD, stopH from operations o, Irrig_floodR Ip where o.opID == Ip.opID and o.o_t_exid==? order by o.odate asc", (o_t_exid, ))
        c1row = c1.fetchall()
        if c1row != None:
            rlist = [c1_row_record for c1_row_record in c1row if c1row != None]
        conn.close()
        return rlist
    

def extract_irrigAmtData(simulationname, o_t_exid):
    '''
    Returns tuple with amouts of irrigation for a particular irrigationClass
    Input:
      irrigationClass
    Output:
      Tuple with amounts of irrigation
    '''
   # print("Sim:", simulationname)
    
    rlist=[]
    conn, c = openDB('crop.db')
    if c:
       # c1 = c.execute("SELECT date FROM weather_data where stationtype = ?",(stationtype,)) #order by lower(weather_id)",(stationtype,))
        c1= c.execute("SELECT AmtIrrAppl FROM operations o, Irrig_pivotOp Ip where o.opID == Ip.opID and o.o_t_exid==? order by o.odate asc", (o_t_exid, ))
        c1row = c1.fetchall()
        rlist = [c1_row_record for c1_row_record in c1row if c1row != None]
        conn.close()
        return rlist
    

def read_irrigationDB(o_t_exid):
    rlist=[]
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("select opID, irrigationClass from irrigationDetails where o_t_exid = ?", (o_t_exid, ))
        c1row = c1.fetchall()
        rlist = [c1_row_record for c1_row_record in c1row if c1row != None]
        conn.close()
       # print("reda_irrigationDB: ", rlist)
        return rlist
    

def read_weather_id_forstationtype(stationtype):  
    '''
  Returns weather id list for a specific site name.
  Input:
    stationtype
  Output:
    Tuple with weather id list
    '''
    rlist = []
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT distinct weather_id FROM weather_data where stationtype = ? order by lower(weather_id)",(stationtype,))
        c1_row = c1.fetchall()
     #   if c1_row != None:
        #    for c1_row_record in c1_row:
      #          rlist.append(c1_row_record[0])
        rlist = [c1_row_record[0] for c1_row_record in c1_row if c1_row != None]
        conn.close()            
        return rlist


def read_weatherDate_forstationtype(stationtype, weather_id):  
    '''
    Returns weather date list for a specific site name/stationtype.
    Input:
    stationtype
     Output:
    Tuple with weather date list
    '''

    conn, c = openDB('crop.db')
    if c:
       # c1 = c.execute("SELECT date FROM weather_data where stationtype = ?",(stationtype,)) #order by lower(weather_id)",(stationtype,))
        c1= c.execute("SELECT max(date), min(date) FROM weather_data where stationtype =? and weather_id = ? group by stationtype, weather_id", (stationtype,weather_id))
        c1_row = c1.fetchall()
         
        conn.close()            
        return c1_row[0][0], c1_row[0][1]

def read_weatherDate_forstationtype(stationtype, weather_id):  
    '''
  Returns weather date list for a specific site name/stationtype.
  Input:
    stationtype
  Output:
    Tuple with weather date list
    '''

    conn, c = openDB('crop.db')
    if c:
       # c1 = c.execute("SELECT date FROM weather_data where stationtype = ?",(stationtype,)) #order by lower(weather_id)",(stationtype,))
        c1= c.execute("SELECT max(date), min(date) FROM weather_data where stationtype =? and weather_id = ? group by stationtype, weather_id", (stationtype,weather_id))
        c1_row = c1.fetchall()
         
        conn.close()            
        return c1_row[0][0], c1_row[0][1]

def read_weatheryears_fromtreatment(treatment):  
    '''
  Returns operation date list for a specific treatment name
  Input:
    treatment info
  Output:
    Tuple with operation date list
    '''
    rlist = [] # list {} # dictionary
    conn, c = openDB('crop.db')
    if c:
        experiment_name = treatment.split('/')[1]
        treatment_name = treatment.split('/')[2]

        clause = (experiment_name,treatment_name)
        c1 = c.execute("SELECT distinct odate from operations o, treatment t, experiment e where t.tid = o.o_t_exid \
                        and e.exid=t.t_exid and e.name=? and t.name = ? order by odate",clause) 
        for op in c1:
            if(op[0] != "" and op[0] is not None):
                dd,mon,yy = op[0].split("/")
                rlist.append(int(yy))

        return sorted(set(rlist))


def read_weatherdate_fromtreatment(treatment):  
    '''
  Returns operation date list for a specific treatment name
  Input:
    treatment info
  Output:
    Tuple with operation date list
    '''
    rlist = [] 
    conn, c = openDB('crop.db')
    if c:
        crop_name = treatment.split('/')[0]
        experiment_name = treatment.split('/')[1]
        treatment_name = treatment.split('/')[2]

        clause = (experiment_name,treatment_name,crop_name)
        c1 = c.execute("SELECT distinct odate from operations o, treatment t, experiment e where t.tid = o.o_t_exid \
                        and e.exid=t.t_exid and e.name=? and t.name = ? and e.crop = ? order by odate",clause) 
        for op in c1:
            #print("op=",op["odate"]) 
            if(op[0] != "" and op[0] is not None):
                date = datetime.strptime(op[0],'%m/%d/%Y')
                rlist.append(date)

        return sorted(rlist)


def read_weather_metaDBforsite(site):  
    '''
  Returns tuple with id and stationtype list for a specific site name
  Input:
    site
  Output:
    Tuple with id and stationtype list
    '''
    rlist ={} # dictionary
    conn, c = openDB('crop.db')
    if c:
        if len(site) > 0: 
            c1 = c.execute("SELECT id, stationtype FROM weather_meta where site=? order by lower(stationtype)",[site])  
            c1_row = c1.fetchall()
            if c1_row != None:
                for c1_row_record in c1_row:
                    rlist[str(c1_row_record[0])] =c1_row_record[1]
        
        conn.close()            
        return rlist


def read_weather_metaDB():  
    '''
  Returns tuple with id and stationtype list.
  Input:
  Output:
    Tuple with id and stationtype list
    '''
    rlist ={}
    conn, c = openDB('crop.db')
    if c:
        c1 = c.execute("SELECT id, stationtype FROM weather_meta order by lower(stationtype)")  
        c1_row = c1.fetchall()
        if c1_row != None:
            for c1_row_record in c1_row:
                rlist[str(c1_row_record[0])] =c1_row_record[1]
        
        conn.close()            
        return rlist


def read_weatherlongDB(stationtype):  
    '''
  Returns tuple with complete weather_meta information based on stationtype
  Input:
    stationtype
  Output:
    Tuple with complete weather_meta information
    '''
    rlist =() 
    conn, c = openDB('crop.db')
    if c:
        #print("Debug: stationtype=",stationtype)
        c1 = c.execute("Select rlat,rlon,Bsolar,Btemp,Atemp,BWInd,BIR,AvgWind,AvgRainRate,ChemCOnc,AvgCO2,stationtype,site FROM weather_meta wm, sitedetails s \
                        where wm.site=s.sitename and stationtype = ? ",[stationtype])
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def insert_update_weather(record_tuple,buttontext):
    '''
  Insert or update information on weather_meta table based on buttontext
  Input:
    record_tuple = tuple with weather meta information
    buttontext =  save or update
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        if buttontext.find('SaveAs')==0:
            c.execute("insert into weather_meta (Bsolar,Btemp,Atemp,BWInd,BIR,AvgWind,AvgRainRate,ChemCOnc,AvgCO2,site,stationtype) values (?,?,?,?,?,?,?,?,?,?,?)",record_tuple) 
        else:
            c.execute("update weather_meta SET Bsolar=?, Btemp=?, Atemp=?, BWInd=?, BIR=?, AvgWind=?, AvgRainRate=?, ChemCOnc=?, AvgCO2=?, site=? where stationtype= ? ",record_tuple) 
    
        conn.commit()
        conn.close()
        return True


def delete_weather(site,stationtype):
    '''
  Delete all information on weather_meta and weather_data tables based on site and stationtype
  Input:
    site
    stationtype
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        weathertuple = (stationtype,site)
        c.execute("delete from weather_meta where stationtype=? and site=?",weathertuple) 
        c.execute("delete from weather_data where stationtype=?",[stationtype]) 
        conn.commit()
        conn.close()
        return True

'''
def delete_cultivar(crop,cultivarname):
    
#  Delete record on cultivar table based on cultivarname
#  Input:
 #   cultivarname
#  Output:
    
  #  delete_flag = messageUserDelete("Are you sure you want to delete this record?")

   # if delete_flag:
    conn, c = openDB('crop.db')
    if c:
        if crop == "maize":
            c.execute("delete from cultivar_maize where hybridname=?",[cultivarname])
        elif crop == "potato":
            c.execute("delete from cultivar_potato where hybridname=?",[cultivarname]) 
        elif crop == "soybean":
            c.execute("delete from cultivar_soybean where hybridname=?",[cultivarname]) 
        elif crop == "cotton":
            c.execute("delete from cultivar_cotton where hybridname=?",[cultivarname]) 
        conn.commit()
        conn.close()
        return True
'''

def insertUpdateCultivarMaize(record_tuple,buttontext):
    '''
  Update/insert cultivar table based on buttontext
  Input:
    record_tuple = information that will be ingested on cultivar_maize
    buttontext = Save/update
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        if buttontext == "SaveAs":
            qstatus = c.execute("insert into cultivar_maize (hybridname,juvenileleaves,DaylengthSensitive,Rmax_LTAR,Rmax_LTIR,PhyllFrmTassel,StayGreen,\
                                 LM_min,RRRM,RRRY,RVRL,ALPM,ALPY,RTWL,RTMinWTperArea,EPSI,IUPW,CourMax,Diffx,Diffz,VelZ,lsink,Rroot,Constl_M,ConstK_M,Cmin0_M,\
                                 ConstI_Y,ConstK_Y,Cmin0_Y) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",record_tuple) 
        else:
            #do update        
            record_tuple1 = record_tuple[1:] + (record_tuple[0],)
            qstatus = c.execute("update cultivar_maize SET juvenileleaves=?, DaylengthSensitive=?, Rmax_LTAR=?, Rmax_LTIR=?, PhyllFrmTassel=?, StayGreen=?,\
                                 LM_min=?, RRRM=?, RRRY=?, RVRL=?, ALPM=?, ALPY=?, RTWL=?, RTMinWTperArea=?, EPSI=?, IUPW=?, CourMax=?, Diffx=?, Diffz=?, VelZ=?, \
                                 lsink=?, Rroot=?, Constl_M=?, ConstK_M=?, Cmin0_M=?, ConstI_Y=?, ConstK_Y=?, Cmin0_Y=? where hybridname=? ",record_tuple1) 
        conn.commit()
        conn.close()
        return True


def insertUpdateCultivarPotato(record_tuple,buttontext):
    '''
  Update/insert cultivar table based on buttontext
  Input:
    record_tuple = information that will be ingested on cultivar_potato
    buttontext = Save/update
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        if buttontext == "SaveAs":
            qstatus = c.execute("insert into cultivar_potato (hybridname,A1,A6,A8,A9,A10,G1,G2,G3,G4,RRRM,RRRY,RVRL,ALPM,ALPY,RTWL,\
                                 RTMinWTperArea,EPSI,IUPW,CourMax,Diffx,Diffz,VelZ,lsink,Rroot,Constl_M,ConstK_M,Cmin0_M,ConstI_Y,ConstK_Y,\
                                 Cmin0_Y) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",record_tuple) 
        else:
            #do update        
            record_tuple1 = record_tuple[1:] + (record_tuple[0],)
            qstatus = c.execute("update cultivar_potato SET A1=?, A6=?, A8=?, A9=?, A10=?, G1=?, G2=?, G3=?, G4=?, RRRM=?, RRRY=?, \
                                 RVRL=?, ALPM=?, ALPY=?, RTWL=?, RTMinWTperArea=?, EPSI=?, IUPW=?, CourMax=?, Diffx=?, Diffz=?, VelZ=?, lsink=?, \
                                 Rroot=?, Constl_M=?, ConstK_M=?, Cmin0_M=?, ConstI_Y=?, ConstK_Y=?, Cmin0_Y=? where hybridname=?",record_tuple1) 
        conn.commit()
        conn.close()
        return True


def insertUpdateCultivarSoybean(record_tuple,buttontext):
    '''
  Update/insert cultivar table based on buttontext
  Input:
    record_tuple = information that will be ingested on cultivar_soybean
    buttontext = Save/update
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        if buttontext == "SaveAs":
            qstatus = c.execute("insert into cultivar_soybean (hybridname,matGrp,seedLb,fill,v1,v2,v3,r1,r2,r3,r4,r5,r6,\
                                 r7,r8,r9,r10,r11,r12,g1,g2,g3,g4,g5,g6,g7,g8,g9,RRRM,RRRY,RVRL,ALPM,ALPY,RTWL,\
                                 RTMinWTperArea,EPSI,IUPW,CourMax,Diffx,Diffz,VelZ,lsink,Rroot,Constl_M,ConstK_M,Cmin0_M,\
                                 ConstI_Y,ConstK_Y,Cmin0_Y) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,\
                                 ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",record_tuple) 
        else:
            #do update        
            record_tuple1 = record_tuple[1:] + (record_tuple[0],)
            qstatus = c.execute("update cultivar_soybean SET matGrp=?, seedLb=?, fill=?, v1=?, v2=?, v3=?, r1=?, r2=?, \
                                 r3=?, r4=?, r5=?, r6=?, r7=?, r8=?, r9=?, r10=?, r11=?, r12=?, g1=?, g2=?, g3=?, g4=?, \
                                 g5=?, g6=?, g7=?, g8=?, g9=? , RRRM=?, RRRY=?, RVRL=?, ALPM=?, ALPY=?, RTWL=?, \
                                 RTMinWTperArea=?, EPSI=?, IUPW=?, CourMax=?, Diffx=?, Diffz=?, VelZ=?, lsink=?, Rroot=?, \
                                 Constl_M=?, ConstK_M=?, Cmin0_M=?, ConstI_Y=?, ConstK_Y=?, Cmin0_Y=? where hybridname=?",\
                                 record_tuple1) 
        conn.commit()
        conn.close()
        return True


def insertUpdateCultivarCotton(record_tuple,buttontext):
    '''
  Update/insert cultivar table based on buttontext
  Input:
    record_tuple = information that will be ingested on cultivar_cotton
    buttontext = Save/update
  Output:
    '''
    conn, c = openDB('crop.db')
    if c:
        if buttontext == "SaveAs":
            qstatus = c.execute("insert into cultivar_cotton (hybridname,calbrt11,calbrt12,calbrt13,calbrt15,calbrt16,\
                                 calbrt17,calbrt18,calbrt19,calbrt22,calbrt26,calbrt27,calbrt28,calbrt29,calbrt30,calbrt31,\
                                 calbrt32,calbrt33,calbrt34,calbrt35,calbrt36,calbrt37,calbrt38,calbrt39,calbrt40,calbrt41,\
                                 calbrt42,calbrt43,calbrt44,calbrt45,calbrt47,calbrt48,calbrt49,calbrt50,calbrt52,calbrt57) \
                                 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",record_tuple) 
        else:
            #do update        
            record_tuple1 = record_tuple[1:] + (record_tuple[0],)
            qstatus = c.execute("update cultivar_cotton SET calbrt11=?, calbrt12=?, calbrt13=?, calbrt15=?, calbrt16=?, \
                                 calbrt17=?, calbrt18=?, calbrt19=?, calbrt22=?, calbrt26=?, calbrt27=?, calbrt28=?, \
                                 calbrt29=?, calbrt30=?, calbrt31=?, calbrt32=?, calbrt33=?, calbrt34=?, calbrt35=?, \
                                 calbrt36=?, calbrt37=?, calbrt38=?, calbrt39=?, calbrt40=?, calbrt41=?, calbrt42=?, \
                                 calbrt43=?, calbrt44=?, calbrt45=?, calbrt47=?, calbrt48=?, calbrt49=?, calbrt50=?, \
                                 calbrt52=?, calbrt57=? where hybridname=?",record_tuple1) 
        conn.commit()
        conn.close()
        return True


def extract_cropOutputData(tablename,simulationname):
    '''
  Returns output table for a specific tablename and simulationname
  Input:
    tablename
    simulationname
  Output:
    dataframe with output information
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        query = "select * from " + tablename + " where " + tablename + "_id=" + simulationname
        if tablename == "g01_potato":
            query = "select g01_potato_id, g.Date_Time, g.jday, g.LAI, PFD, SolRad, Tair, Tcan, [Rg+Rm], Pgross, [Tr-Pot], [Tr-Act], \
    Stage, totalDM, leafDM, stemDM, rootDM, tuberDM, deadDM, LWPpd, LWPave, gs_ave, N_uptake, tot_N, \
    leaf_N, stem_N, root_N, tuber_N from g01_potato g, nitrogen_potato n where g.Date_Time=n.Date_Time \
    and g01_potato_id=" + simulationname + " and n.nitrogen_potato_id=" + simulationname
        df = pd.read_sql_query(query,conn)
        conn.close()
        return df


    

def delete_cropOutputSim(id,crop):
    '''
  Returns output table for a specific tablename and simulationname
  Input:
    id
    crop
  Output:
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        #print("crop=",crop)
        if crop == "maize":
            file_ext = ["g01","g03","g04","g05","g07","plantStress"]
        elif crop == "potato" or crop == "soybean":
            file_ext = ["g01","g03","g04","g05","g07","nitrogen","plantStress"]
        elif crop == "fallow":
            file_ext = ["g03","g05","g07"]
        elif crop == "cotton":
            file_ext = ["g01","g03","g04","g05","g07","plantStress"]

        geoQuery = "delete from geometry where simID=" + id
        c.execute(geoQuery)
        for ext in file_ext:
            table_name = ext+"_"+crop
            id_name = table_name+"_id"
            query = "delete from " + table_name + " where " + id_name + "=" + id
            c.execute(query) 

        conn.commit()
        conn.close()
        return True
 

def readSoilInfoCropOutputDB(crop,tablename,simulationname):
    '''
  Returns output table for a specific tablename and simulationname
  Input:
    crop
    tablename
    simulationname
  Output:
    dataframe with output information
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        if tablename == "g03_maize" or tablename == "g03_fallow" or tablename == "g03_soybean" or tablename  == "g03_potato" or tablename == "g03_cotton":
            query = "select Date_Time, X, Y, hNew, abs(hNew) as absHNew, thNew, hNew/abs(hNew) as mult, NO3N, NH4N, Temp from " + tablename + " where " + tablename + "_id=" + simulationname
        else:
            query = "select Date_Time, X, Y, Humus_C, Humus_N, Litter_C, Litter_N, Manure_C, Manure_N, Root_N, Root_C from " + tablename + " where " + tablename + "_id=" + simulationname

        df = pd.read_sql_query(query,conn)
        conn.close()
        return df
 

def extract_date_time(date,time):
    '''
  Split date and returns as a timestamp.
  Input:
    date
    time
  Output:
    date as a timestamp
    '''
  #  print("Date:", date)
  #  print("Time: ", time)
    (m,d,y) = str(date).split('/')
    newDate = pd.Timestamp(int(y),int(m),int(d),time)
    return newDate


def checkNaNInOutputFile(table_name,g_name):
    '''
  Check output data for NaN values.
    table_name
    g_name = input filename with full path
  Output:
    columnList = list with columns with NaN values
    '''
    columnList = []
    spaceStr = ", "
    message = ""

    g_df = pd.read_csv(g_name,skipinitialspace=True,index_col=False)
    # Check for NaN values for each dataframe column
    dates = []
    date = ""
    for col in g_df.columns:
        if g_df[col].isnull().values.any():
            if len(dates)  == 0:
                dates = list(g_df.loc[pd.isna(g_df[col]),:].index)
                if(table_name == "g01_maize" or table_name == "g01_potato" or \
                   table_name == "nitrogen_potato" or table_name == "plantStress_potato" or \
                   table_name == "g01_soybean" or table_name == "nitrogen_soybean" or \
                   table_name == "plantStress_soybean"):
                    # Change date format
                   print("g_df:", g_df) 
                   g_df['Date_Time'] = g_df.apply(lambda row: extract_date_time(row['date'],row['time']), axis=1)

                if(table_name == "g03_maize" or table_name == "g04_maize" or table_name == "g05_maize" or \
                   table_name == "g03_potato" or table_name == "g04_potato" or table_name == "g05_potato" or \
                   table_name == "g03_soybean" or table_name == "g04_soybean" or table_name == "g05_soybean" or\
                   table_name == "g03_fallow" or table_name == "g05_fallow"):
                    # Change date format
                    # 2dsoil start counting the days starting on 12/30/1899.
                   g_df['DateInit'] = pd.Timestamp('1899-12-30')
                   g_df['Date_Time'] = g_df['DateInit'] + pd.to_timedelta(g_df['Date_time'], unit='D')

                g_df['Date_Time'] = g_df['Date_Time'].dt.strftime('%m/%d/%Y')
                date = "Date:"+spaceStr.join(g_df['Date_Time'].loc[dates])+"<br>\n"
            columnList.append(col)

    if len(columnList) > 0:
        message = g_name+": "+spaceStr.join(columnList)+"<br>\n"+date

    return message


def ingestOutputFile(table_name,g_name,simulationname):
    '''
  Ingest file with output data in cropOutput database.
  Input:
    table_name
    g_name = input filename with full path
    simulationname
  Output:
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        id = table_name + "_id"
        g_df = pd.read_csv(g_name,skipinitialspace=True,index_col=False)
        # strip leading and trailing spaces from column names
        for col in g_df.columns: 
            g_df.rename(columns={col:col.strip()},inplace=True)
        g_df[id] = int(simulationname)

        if(table_name == "g01_maize" or table_name == "g01_potato" or table_name == "nitrogen_potato" \
           or table_name == "plantStress_potato" or table_name == "plantStress_maize" or table_name == "g01_soybean" or \
           table_name == "nitrogen_soybean" or table_name == "plantStress_soybean" or table_name == "g01_cotton" or \
           table_name == "plantStress_cotton"):
            # Change date format
            def _safe_extract_date_time(row):
                try:
                    return extract_date_time(row['date'], row['time'])
                except Exception as e:
                    # Log the bad row and return NaT so apply stays 1-D
                    print("extract_date_time error for row:", row, "err:", e)
                    return pd.NaT

          # print(g_df)
          # g_df['Date_Time'] = g_df.apply(lambda row: extract_date_time(row['date'],row['time']), axis=1)
             # Ensure result is a 1-D Series of scalars (Timestamp or NaT)
            g_df['Date_Time'] = g_df.apply(_safe_extract_date_time, axis=1)

            g_df = g_df.drop(columns=['date','time'])

            if(table_name == "g01_potato"):
                g_df.rename(columns={'LA/pl':'LA_pl'},inplace=True)
            if(table_name == "nitrogen_potato"):
                g_df.rename(columns={'Seed N':'seed_N'},inplace=True)
            if(table_name == "nitrogen_potato" or table_name == "plantStress_potato" or \
               table_name == "nitrogen_soybean" or table_name == "plantStress_soybean" or \
               table_name == "g01_cotton" or table_name == "plantStress_cotton"):
                g_df = g_df.drop(columns=['jday'])

        if(table_name == "g03_maize" or table_name == "g04_maize" or table_name == "g05_maize" or \
           table_name == "g07_maize" or table_name == "g03_potato" or table_name == "g04_potato" or \
           table_name == "g05_potato" or table_name == "g07_potato" or table_name == "g03_soybean" or \
           table_name == "g04_soybean" or table_name == "g05_soybean" or table_name == "g07_soybean" or \
           table_name == "g03_fallow" or table_name == "g05_fallow" or  table_name == "g07_fallow" or \
           table_name == "g03_cotton" or table_name == "g04_cotton" or table_name == "g05_cotton" or \
           table_name == "g07_cotton"):
            # Change date format
            # 2dsoil start counting the days starting on 12/30/1899.
            g_df['DateInit'] = pd.Timestamp('1899-12-30')
            g_df['Date_Time'] = g_df['DateInit'] + pd.to_timedelta(g_df['Date_time'], unit='D').dt.round('h')
            g_df = g_df.drop(columns=['DateInit','Date','Date_time'])
            if(table_name == "g03_maize" or table_name == "g03_cotton" or table_name == 'g03_soybean' or \
               table_name == "g03_potato" or table_name == "g03_fallow"):
                g_df = g_df.drop(columns=['Area','Vx','Vy'])

        g_df.to_sql(table_name,conn,if_exists="append",index=False)
        conn.close()
        return True


def ingestGeometryFile(grdFile,g03File,simulation):
    '''
  Ingest file with output data in cropOutput database.
  Input:
    grdFile = .grd filename with full path
    g03File = G03 filename with full path
    simulationname
  Output:
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        # First read the .grd file
        # Find line where this string is located, we don't want to read anything from this line on.
        searchFor = "***************** ELEMENT INFORMATION ******************************************************"
        with open(grdFile,'r') as gf:
            lines = gf.readlines()
            for line in lines:
                # Check for string
                if line.find(searchFor) != -1:
                    lineNum = lines.index(line)
                    totLines = len(lines)
                    footer = totLines - lineNum
                    break
        grd_df = pd.read_csv(grdFile,header=[3],delim_whitespace=True,skipinitialspace=True,skipfooter=footer,engine='python')
        #rename columns
        grd_df = grd_df.rename(columns={'n':'nodeNum','x':'X','y':'Y','MatNum':'Layer'})

        g_df = pd.read_csv(g03File,skipinitialspace=True,index_col=False)
        # strip leading and trailing spaces from column names
        for col in g_df.columns: 
            g_df.rename(columns={col:col.strip()},inplace=True)
        g_df = g_df.drop(columns=['Date_time','Date','hNew','thNew','Vx','Vy','Q','NO3N','NH4N','Temp','CO2Conc','O2Conc', 'N2OConc'])
        # Get unique value for each row
        g_df = g_df.drop_duplicates(keep="first")

        id = "simID"
        g_df[id] = int(simulation)

        result = pd.merge(grd_df,g_df,how='inner',left_on=['X','Y'],right_on=['X','Y'])
        result.to_sql('geometry',conn,if_exists="append",index=False)
        conn.close()
        return True


def readGeometrySimID(simulationname):
    '''
  Returns geometry information for a given simulation
  Input:
    simulationname
  Output:
    dataframe with output information
    '''
    conn, c = openDB('cropOutput.db')
    if c:
        query = "select X, Y, Layer, Area from geometry where simID = " + simulationname
        df = pd.read_sql_query(query,conn)
        conn.close()
        return df
 

def getMaizeDateByDev(sim_id,maizePhase):
    '''
  Returns date for tuber initiation date.
  Input:
    sim_id = simulation id
    maizePhase = maize development phase keyword
  Output:
    tuber initiation date
    '''
    rlist = "" 

    conn, c = openDB('cropOutput.db')
    if c:
        maizetuple = (sim_id,maizePhase)
        c2 = c.execute("select min(Date_Time) from g01_maize where g01_maize_id=? and Note=?",maizetuple)
        c2_row = c2.fetchone()
        if c2_row[0] != None:  
            date_time_obj = dt.strptime(c2_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            rlist = date_time_obj
        else:
            rlist = "N/A"
        conn.close()   

        return rlist


def getMaxDateG01BySimID(crop, sim_id):
    '''
  Returns max date for G01 file when plat doesn't reach maturity date
  Input:
    crop
    sim_id = simulation id
  Output:
    last date
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        query = "select max(Date_Time) from g01_" + crop + " where g01_" + crop + "_id=" + sim_id
        c2 = c.execute(query)
        c2_row = c2.fetchone()
        date_time_obj = dt.strptime(c2_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
        rlist = date_time_obj
        conn.close()   

        return rlist


def getTuberInitDate(sim_id):
    '''
  Returns date for tuber initiation date.
  Input:
    sim_id = simulation id
  Output:
    tuber initiation date
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        c2 = c.execute("select min(Date_Time) from g01_potato where (tuberDM > 0 or Stage > 2.01) and g01_potato_id=?",[sim_id])
        c2_row = c2.fetchone()
        if c2_row[0] != None:  
            date_time_obj = dt.strptime(c2_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            rlist = date_time_obj
        else:
            rlist = "N/A"
        conn.close()   

        return rlist


def getMaturityDate(sim_id):
    '''
  Returns date for maturity date.
  Input:
    sim_id = simulation id
  Output:
    maturity date
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        c2 = c.execute("select min(Date_Time) from g01_potato where Stage > 10 and g01_potato_id=?",[sim_id])
        c2_row = c2.fetchone()
        if c2_row[0] != None:  
            date_time_obj = dt.strptime(c2_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            rlist = date_time_obj
        else:
            rlist = "N/A"
        conn.close()   

        return rlist


def getPotatoAgronomicData(sim_id, date):
    '''
  Returns agronomical date.
  Input:
    sim_id = simulation id
    date = maturity date
  Output:
    tuberDM = yield
    totalDM = total biomass
    Tr-Act = transpiration
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        harvestDate = dt.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        querytuple = (sim_id,harvestDate+'%')

        c1 = c.execute("select max(tuberDM), max(totalDM), sum(\"Tr-Act\") from g01_potato where g01_potato_id=? and Date_Time <= ?",querytuple)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getMaizeAgronomicData(sim_id, date):
    '''
  Returns maize agronomical date.
  Input:
    sim_id = simulation id
    date = maturity date
  Output:
    earDM = yield
    shootDM = total biomass
    NUpt
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        harvestDate = dt.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        querytuple = (sim_id,harvestDate+'%')

        c1 = c.execute("select (max(earDM)*.86), max(shootDM), max(NUpt) from g01_maize where g01_maize_id=? and Date_Time <= ?",querytuple)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
     #   print("getMaizeAgronomicData: ",rlist)
        return rlist


def getCottonAgronomicData(sim_id):
    '''
  Returns cotton agronomic data.
  Input:
    sim_id = simulation id
  Output:
    date
    yield
    PlantDM (total biomass)
    NUpt
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        querytuple = (sim_id,)

        c1 = c.execute("select max(Date_time), Yield, PlantDM, NUpt from g01_cotton where g01_cotton_id=?",querytuple)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getCottonDevDate(sim_id, stage):
    '''
  Returns the date for a cotton plant development stage.
  Input:
    sim_id = simulation id
    rstage = development stage
  Output:
    date
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        query = "select max(Date_time), Note from g01_cotton where Note like '" + stage + "%' and g01_cotton_id=" + sim_id

        c1 = c.execute(query)
        c1_row = c1.fetchone()
        if c1_row[0] != None:  
            date_time_obj = dt.strptime(c1_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            rlist = date_time_obj
        else:
            rlist = "N/A"

        conn.close()
        return rlist


def getSoybeanDevDate(sim_id, rstage):
    '''
  Returns the date for a soybean plant development stage.
  Input:
    sim_id = simulation id
    rstage = index that will corespond with a development stage
  Output:
    date
    '''
    rlist = None # list   

    conn, c = openDB('cropOutput.db')
    if c:
        querytuple = (rstage,sim_id)

        c1 = c.execute("select min(Date_Time) from g01_soybean where RSTAGE >= ? and g01_soybean_id=?",querytuple)
        c1_row = c1.fetchone()
        if c1_row[0] != None:  
            date_time_obj = dt.strptime(c1_row[0], '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            rlist = date_time_obj
        else:
            rlist = "N/A"

        conn.close()
        return rlist


def getSoybeanAgronomicData(sim_id, date):
    '''
  Returns soybean agronomical date.
  Input:
    sim_id = simulation id
    date = maturity date
  Output:
    seedDM = yield
    totalDM = total biomass
    Tr_act = transpiration
    '''
    rlist = None

    conn, c = openDB('cropOutput.db')
    if c:
        harvestDate = dt.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        querytuple = (sim_id,harvestDate+'%')

        c1 = c.execute("select max(seedDM), max(totalDM), sum(Tr_act) from g01_soybean where g01_soybean_id=? and Date_Time <= ?",querytuple)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getEnvironmentalData(sim_id, date, crop):
    '''
  Returns environmental data.
  Input:
    sim_id = simulation id
    date = maturity date
    crop
  Output:
    SeasPTran
    SeasATran 
    SeasASoEv
    SeasPSoEv
    SeasInfil
    Runoff
    SeasRain
    Drainage
    WaterFromDeepSoil
    CO2Flux
    O2Flux
    N_Leach
    '''
    rlist = None 

    conn, c = openDB('cropOutput.db')
    if c:
        if crop == "maize" or crop == "soybean" or crop == "potato":
             maturityDate = dt.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
             query = "select max(SeasPTran), max(SeasATran), max(SeasASoEv), max(SeasPSoEv), max(SeasInfil), sum(Runoff), \
                     max(SeasRain), sum(case when Drainage<=0 then Drainage else 0 end) as Drainage, \
                     sum(case when Drainage>0 then abs(Drainage) else 0 end) as WaterFromDeepSoil, sum(CO2Flux), sum(O2Flux), \
                     sum(N_Leach) from g05_" + crop + " where g05_" + crop + "_id=" + sim_id + " and Date_Time <= '" + maturityDate + "%'"
        elif crop == "cotton" or crop == "fallow":
             query = "select max(SeasPTran), max(SeasATran), max(SeasASoEv), max(SeasPSoEv), max(SeasInfil), sum(Runoff), \
                      max(SeasRain), sum(case when Drainage<=0 then Drainage else 0 end) as Drainage, \
                      sum(case when Drainage>0 then abs(Drainage) else 0 end) as WaterFromDeepSoil , sum(CO2Flux), sum(O2Flux), \
                      sum(N_Leach) from g05_" + crop + " where g05_" + crop + "_id=" + sim_id
        c1 = c.execute(query)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getNitrogenUptake(sim_id, date, crop):
    '''
  Returns nitrogen uptake.
  Input:
    sim_id = simulation id
    date = maturity date
    crop
  Output:
    NUpt = nitrogen uptake
    '''
    rlist = None  

    conn, c = openDB('cropOutput.db')
    if c:
        harvestDate = dt.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
        querytuple = (sim_id,harvestDate+'%')

        query = "select max(N_uptake) from nitrogen_" + crop + " where nitrogen_" + crop + "_id=" + sim_id + " and \
                Date_Time <= '" + harvestDate + "%'"
        c1 = c.execute(query)
        c1row = c1.fetchone()
        if c1row != None:
            rlist = c1row

        conn.close()
        return rlist


def getNitroWaterStressDates(sim_id):
    '''
  Returns dates where nitrogen and water (<=0.75) stress were present.
  Input:
    sim_id = simulation id
  Output:
    Tuple containing
    Date_Time = date
    PSIEffect_leaf = Water stress on leaf expansion
    NEffect_leaf = Nitrogen stress on leaf expansion
    PSIEffect_Pn = Water stress on leaf photosynthesis
    NEffect_Pn = Nitrogen stress on photosynthesis
    '''

    rlist = [] # list   

    conn, c = openDB('cropOutput.db')
    if c:
        c1 = c.execute("select distinct Date_Time, PSIEffect_leaf, NEffect_leaf, PSIEffect_Pn, NEffect_Pn from plantStress_potato where \
                        (PSIEffect_leaf <= 0.75 or NEffect_leaf <= 0.75 or PSIEffect_Pn <= 0.75 or NEffect_Pn <= 0.75) and \
                        plantStress_potato_id=? order by Date_Time",[sim_id])
        c1row = c1.fetchall()
  #      if c1row != None:
    #        for c1rowrecord in c1row:
    #            rlist.append(c1rowrecord)
        rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def getMaizePlantStressDates(sim_id):
    '''
  Returns dates where nitrogen and water (<=0.75) stress were present.
  Input:
    sim_id = simulation id
  Output:
    Tuple containing
    Date_Time = date
	waterstress = Water Stress
	N_stress = N Stress
	Shade_Stress = C Stress
	PotentialArea = Potential Area
    '''

    rlist = []

    conn, c = openDB('cropOutput.db')
    if c:
        c1 = c.execute("select distinct Date_Time, waterstress, N_stress, Shade_Stress, PotentialArea from plantStress_maize where \
                        (waterstress >= 0.25 or N_stress >= 0.25 or Shade_Stress >= 0.25 or PotentialArea >= 0.25) and \
                        plantStress_maize_id=? order by Date_Time",[sim_id])
        c1row = c1.fetchall()
     #   if c1row != None:
      #      for c1rowrecord in c1row:
      #          rlist.append(c1rowrecord)
        rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def getSoybeanPlantStressDates(sim_id):
    '''
  Returns dates where nitrogen, carbon  and water (<=0.75) stress were present.
  Input:
    sim_id = simulation id
  Output:
    Tuple containing
    Date_Time = date
	wstress = Water Stress
	Nstress = N Stress
	Cstress = C Stress
	Limit = predominant factor limiting growth
    '''

    rlist = [] 

    conn, c = openDB('cropOutput.db')
    if c:
        c1 = c.execute("select distinct ps.Date_Time, ps.wstress, ps.Nstress, ps.Cstress, g1.'Limit' from plantStress_soybean ps, \
                        g01_soybean g1 where (ps.wstress <= 0.75 or ps.Nstress <= 0.75 or ps.Cstress <= 0.75) and \
                        ps.plantStress_soybean_id=?  and ps.plantStress_soybean_id=g1.g01_soybean_id  and ps.Date_Time=g1.Date_Time \
                        order by ps.Date_Time",[sim_id])
        c1row = c1.fetchall()
   #     if c1row != None:
   #         for c1rowrecord in c1row:
    #            rlist.append(c1rowrecord)
        rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist


def getCottonPlantStressDates(sim_id):
    '''   
  Returns dates where nitrogen, carbon  and water (<=0.75) stress were present.
  Input:
    sim_id = simulation id
  Output:
    Tuple containing
    Date_Time = date
	W_stress = Water Stress
	N_Veg_Str = N Stress (vegetative)
	N_Fru_Str = N Stress (fruit)
	N_Rt_Str = N Stress (root)
	C_Stress = C Stress
    '''
    rlist = []

    conn, c = openDB('cropOutput.db')
    if c:
        c1 = c.execute("select distinct Date_Time, W_stress, N_Veg_Str, N_Fru_Str, N_Rt_Str, C_Stress from plantStress_cotton where \
                        (W_stress<0.8 or N_Veg_Str<0.8 or N_Fru_Str<0.8 or N_Rt_Str<0.8 or C_Stress<0.8) and \
                        plantStress_cotton_id=? order by Date_Time",[sim_id])
        c1row = c1.fetchall()
     #   if c1row != None:
     #       for c1rowrecord in c1row:
      #          rlist.append(c1rowrecord)
        rlist = [c1rowrecord for c1rowrecord in c1row if c1row != None]
        conn.close()
        return rlist
'''
def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length-1)]
    return cu_list[:]   
'''
def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length+1)]
    return cu_list[1:]   


def delete_cultivar(crop, cultivarname, askUserFlag):
        delete_flag = False
      
        if askUserFlag:
                delete_flag = messageUserDelete("Are you sure you want to delete this record?")
        else:
            delete_flag = True

        if delete_flag:
            conn, c = openDB('crop.db')
            if c:
                if crop == "maize":
                    c.execute("delete from cultivar_maize where hybridname=?",[cultivarname])
                elif crop == "potato":
                    c.execute("delete from cultivar_potato where hybridname=?",[cultivarname]) 
                elif crop == "soybean":
                    c.execute("delete from cultivar_soybean where hybridname=?",[cultivarname]) 
                elif crop == "cotton":
                    c.execute("delete from cultivar_cotton where hybridname=?",[cultivarname]) 
                conn.commit()
                conn.close()



def insert_cultivarDB(crop, record_tuple):
   # print(crop, record_tuple[0])
    cultivarname = record_tuple[0]
    rlist = []
    rlist = check_cultivarDB(crop, cultivarname)

    if rlist == []:
        conn, c = openDB('crop.db')

        if c:
            if crop == 'maize':
                c.execute('insert into cultivar_maize (hybridname, juvenileleaves, Rmax_LTAR, Rmax_LTIR, PhyllFrmTassel, StayGreen) values (?,?,?,?,?,?)', record_tuple)
            elif crop == 'soybean':
                c.execute('insert into cultivar_soybean(hybridname,seedLb, fill, v1, v2, v3, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, g1, g2, g3, g4, g5, g6, g7, g8, g9) \
               values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', record_tuple)
            elif crop == 'potato':
                c.execute('insert into cultivar_potato (hybridname, A1, A6, A8, A9, A10, G1, G2, G3, G4) values (?,?,?,?,?,?,?,?,?,?)', record_tuple)
            elif crop == 'cotton':
                c.execute('insert into cultivar_cotton (hybridname, calbrt11, calbrt12, calbrt13, calbrt15, calbrt16, calbrt17, calbrt18, calbrt19, calbrt22, calbrt26, calbrt27, \
                calbrt28, calbrt29, calbrt30, calbrt31, calbrt32, calbrt33, calbrt34, calbrt35, calbrt36, calbrt37, calbrt38, calbrt39, calbrt40, calbrt41, calbrt42, calbrt43,  \
                calbrt44, calbrt45, calbrt47, calbrt48, calbrt49, calbrt50, calbrt52, calbrt57) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', record_tuple)
            conn.commit()
            conn.close()
        return True
    else:
        return messageUser("This cultivarname exists, please use a different name.")

      
        
def check_cultivarDB(crop, cultivarname): 
    '''
  Check if cultivar exists.
  Input:
    crop, cultivarname
  Output:
    id = cultivar id
    '''  
    rlist = []   
    conn, c = openDB('crop.db')
    if c:
        if crop == 'maize':
            c1= c.execute("SELECT id FROM cultivar_maize where hybridname=?", (cultivarname,))
        elif crop == 'soybean':
            c1= c.execute("SELECT id FROM cultivar_soybean where hybridname=?", (cultivarname,))
        elif crop == 'potato':
            c1= c.execute("SELECT id FROM cultivar_potato where hybridname=?", (cultivarname,))
        elif crop == 'cotton':
            c1= c.execute("SELECT id FROM cultivar_cotton where hybridname=?", (cultivarname,))

        c1row = c1.fetchone()
        if c1row != None:
            rlist.append(c1row[0])   
        conn.close()
        return rlist

            
def update_cultivarDB(crop, record_tuple):
    (crop,cultivarname) =record_tuple[0].split(":")
    updated_tuple = record_tuple[1:] + (cultivarname,)
    conn, c = openDB('crop.db')
    if c:
        if crop == 'maize':
            c.execute('update cultivar_maize set juvenileleaves=?, Rmax_LTAR=?, Rmax_LTIR=?, PhyllFrmTassel=?, StayGreen=? where hybridname = ?', updated_tuple)
        elif crop == 'soybean':
            c.execute('update cultivar_soybean set seedLb=?, fill=?, v1=?, v2=?, v3=?, r1=?, r2=?, r3=?, r4=?, r5=?, r6=?, r7=?, r8=?, r9=?, r10=?, r11=?, r12=?, g1=?, g2=?, g3=?, g4=?, \
           g5=?, g6=?, g7=?, g8=?, g9=? where hybridname = ?', updated_tuple)
        elif crop == 'potato':
            c.execute('update cultivar_potato set A1=?, A6=?, A8=?, A9=?, A10=?, G1=?, G2=?, G3=?, G4=? where hybridname = ?', updated_tuple)
        elif crop == 'cotton':
            c.execute('update cultivar_cotton set calbrt11=?, calbrt12=?, calbrt13=?, calbrt15=?, calbrt16=?, calbrt17=?, calbrt18=?, calbrt19=?, calbrt22=?, calbrt26=?, calbrt27=?, \
            calbrt28=?, calbrt29=?, calbrt30=?, calbrt31=?, calbrt32=?, calbrt33=?, calbrt34=?, calbrt35=?, calbrt36=?, calbrt37=?, calbrt38=?, calbrt39=?, calbrt40=?, calbrt41=?, \
                     calbrt42=?, calbrt43=?,  calbrt44=?, calbrt45=?, calbrt47=?, calbrt48=?, calbrt49=?, calbrt50=?, calbrt52=?, calbrt57=? where hybridname = ?', updated_tuple)
        conn.commit()
        conn.close()
    return True


def expSysOutput(id, irr, yld):
	conn, c = openDB('cropOutput.db')
	if c:
		c.execute("insert into expSys_output (simID, irri, yield) values(?,?,?)", (id, irr, yld,))

	conn.commit()
	conn.close()
	return True

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def read_nitrogenDB(simulationname, cropname):
    '''
    Returns the nitrogen data
    input:
        simulationname
    Output:
        nitrogen data as uptake and leached
    '''   
    conn, c = openDB('cropOutput.db')
    croptable1 = "g01_" + cropname
    croptable2 = "g05_" + cropname
    
    id1 = croptable1 + "_id"
    id2 = croptable2 + "_id"
    
    if c:
        query1 = f"SELECT Date_Time, NUpt FROM {croptable1} WHERE {id1} = ?"
        query2 = f"SELECT Date_Time, N_Leach FROM {croptable2} WHERE {id2} = ?"
        param=(simulationname,)
        df1 = pd.read_sql_query(query1,conn, params = param)
        df2 = pd.read_sql_query(query2, conn, params= param)
        conn.close()
        return df1, df2
    



def findNAppldB(cropname, experimentname, treatmentname, inseasondate):
    """
    Backwards-compatible wrapper: return total management (fertilizer) N up to inseasondate.
    Uses get_management_n_map(...) so logic is centralized.
    """
    # resolve ids
    t_exid = read_experimentDB_id(cropname, experimentname)
    tid = read_treatmentDB_id(t_exid, treatmentname)
    if tid is None:
        return 0.0
    # sum management N up to in-season date
    mgmt_map = get_management_n_map(tid, up_to_date=inseasondate) if inseasondate else get_management_n_map(tid)
    return sum(mgmt_map.values())

def get_management_n_map(tid, up_to_date=None):
    """
    Return dict mapping date (YYYY-MM-DD) -> total management-applied N for a given treatment id (tid).
    If up_to_date provided (YYYY-MM-DD) only returns fertilizer operations with date <= up_to_date.
    """
    conn, c = openDB('crop.db')
    try:
        q = """
            SELECT o.odate, fn.nutrient, fn.nutrientQuantity
            FROM operations o
            JOIN fertNutOp fn ON o.opID = fn.opID
            WHERE o.o_t_exid = ? AND o.name = 'Fertilizer'
        """
        c.execute(q, (tid,))
        rows = c.fetchall()
        mgmt_map = {}
        for odate, nutrient, qty in rows:
            if odate is None or qty is None:
                continue
            # parse date in operations (stored like 'MM/DD/YYYY')
            try:
                date_iso = datetime.strptime(odate.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            except Exception:
                # skip malformed dates
                continue

            # filter by up_to_date if provided
            if up_to_date and date_iso > up_to_date:
                continue

            # Relax nutrient filter: accept anything that looks like N, or if you know you only ever
            # have one nutrient per fertilizer op, just count all rows.
            try:
                nu = (nutrient or "").strip().lower()
            except Exception:
                nu = ""

            is_n = False
            if isinstance(nutrient, str):
                if "n" == nu or "n " in nu or "nitro" in nu:
                    is_n = True
                elif " n)" in nu or "(n" in nu:
                    is_n = True
                # if your DB stores things like "Urea" but you still want to count it as N, you could:
                # elif nu in ("urea", "nh4no3", "nh4-n", "no3-n"):
                #     is_n = True

            # If you know there is only N in fertNutOp, you can skip the check entirely:
            # is_n = True

            if not is_n:
                continue

            try:
                val = float(qty)
            except Exception:
                continue
            mgmt_map[date_iso] = mgmt_map.get(date_iso, 0.0) + val
        return mgmt_map
    finally:
        try:
            conn.close()
        except:
            pass

           
 
# Min-Max Scaling function
def min_max_scale(arr):
    scaler = (arr - arr.min()) / (arr.max() - arr.min())
    return scaler

# Create the table when the Simulation starts at the Seasonal tab
def create_simulation_table():
    conn,c = openDB('cropOutput.db')
    if c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS N_simulation_ES (
                Simulation_id INTEGER,
                Date TEXT,
                Min_N REAL,
                NUpt REAL,
                N_Dem REAL,
                N_Leach REAL
            )
        ''')
        conn.commit()
        conn.close()

# Erase the table when the Application close
def erase_simulation_data():
    conn,c = openDB('cropOutput.db')
    if c:
        c.execute('DELETE FROM N_simulation_ES')
        conn.commit()
        conn.close()

# Save N_simulation_data to the N_simulation_ES table. 

def save_simulation_data(simulation_id, date, min_n, nupt, n_dem, n_leach):
    conn,c = openDB('cropOutput.db')
    if c:
        try:
            # Ensure a single row per (Simulation_id, Date) to avoid duplicates from repeated parsing.
            c.execute("DELETE FROM N_simulation_ES WHERE Simulation_id = ? AND Date = ?", (simulation_id, date))
            c.execute('''
                INSERT INTO N_simulation_ES (Simulation_id, Date, Min_N, NUpt, N_Dem, N_Leach)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (simulation_id, date, min_n, nupt, n_dem, n_leach))
            conn.commit()
        except Exception as e:
            print("DEBUG save_simulation_data error:", e)
            try:
                conn.rollback()
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass

# Read the N- data from the MassBI.ou, .g01, and .g05 tables.
def read_simulation_outputs(fieldpath, sitename):
    # MassBI.out: Date, Min_N
    massbi_file = os.path.join(fieldpath, 'MassBI.out')
    df_massbi = pd.read_csv(massbi_file, dtype=str)
    df_massbi.columns = df_massbi.columns.str.strip()
    df_massbi = df_massbi[['Date', 'Min_N']][1:]
    df_massbi['Date'] = pd.to_datetime(df_massbi['Date'].str.strip(), format='%m/%d/%Y')
    df_massbi['Min_N'] = pd.to_numeric(df_massbi['Min_N'].str.strip(), errors='coerce')

    # .g01: NUpt, N_Dem
    g01_file = os.path.join(fieldpath, f"{sitename}.g01")
    df_g01 = pd.read_csv(g01_file, dtype=str)
    df_g01.columns = df_g01.columns.str.strip()
    df_g01['date'] = pd.to_datetime(df_g01['date'].str.strip(), format='%m/%d/%Y')
    df_g01['NUpt'] = pd.to_numeric(df_g01['NUpt'].str.strip(), errors='coerce')
    df_g01['N_Dem'] = pd.to_numeric(df_g01['N_Dem'].str.strip(), errors='coerce')

    # .g05: N_Leach
    g05_file = os.path.join(fieldpath, f"{sitename}.g05")
    df_g05 = pd.read_csv(g05_file, dtype=str)
    df_g05.columns = df_g05.columns.str.strip()
    df_g05['Date'] = pd.to_datetime(df_g05['Date'].str.strip(), format='%m/%d/%Y')
    df_g05['N_Leach'] = pd.to_numeric(df_g05['N_Leach'].str.strip(), errors='coerce')

    # Merge all on Date
    df = pd.merge(df_massbi, df_g01, left_on='Date', right_on='date', how='outer')
    df = pd.merge(df, df_g05, left_on='Date', right_on='Date', how='outer')

    # Fill missing values with None
    df = df[['Date', 'Min_N', 'NUpt', 'N_Dem', 'N_Leach']].fillna(None)
    return df


# DB helpers to insert/update and sum applied N - 1
'''
def insert_or_update_nitrogen_applied(tid, t_exid, date_iso, n_app):
    """
    Insert or update a record in nitrogen_applied (crop.db).
    - tid: treatment id (int)
    - t_exid: experiment id (int)
    - date_iso: 'YYYY-MM-DD' string
    - n_app: numeric amount
    """
    conn, c = openDB('crop.db')
    if c:
        try:
            # Requires UNIQUE(tid, date) in table schema; uses SQLite UPSERT syntax
            c.execute("""
                INSERT INTO nitrogen_applied (tid, t_exid, date, n_app)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tid, date) DO UPDATE SET n_app = excluded.n_app, t_exid = excluded.t_exid
            """, (tid, t_exid, date_iso, float(n_app)))
            conn.commit()
            return True
        except Exception as e:
            # Optional: log or notify
            print("insert_or_update_nitrogen_applied error:", e)
            return False
        finally:
            conn.close()
    return False
'''
def insert_or_update_nitrogen_applied(tid, t_exid, date_iso, n_app):
    """
    Insert or update a record in nitrogen_applied (crop.db).
    Robust implementation that does not rely on a UNIQUE constraint or SQLite UPSERT syntax.
    """
    conn, c = openDB('crop.db')
    if not c:
        return False
    try:
        # Check if row exists for (tid, date)
        c.execute("SELECT 1 FROM nitrogen_applied WHERE tid = ? AND date = ? LIMIT 1", (tid, date_iso))
        exists = c.fetchone() is not None

        if exists:
            c.execute("UPDATE nitrogen_applied SET n_app = ?, t_exid = ? WHERE tid = ? AND date = ?",
                      (float(n_app), t_exid, tid, date_iso))
        else:
            c.execute("INSERT INTO nitrogen_applied (tid, t_exid, date, n_app) VALUES (?, ?, ?, ?)",
                      (tid, t_exid, date_iso, float(n_app)))

        conn.commit()
        return True
    except Exception as e:
        print("insert_or_update_nitrogen_applied error:", e)
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

# DB helpers to insert/update and sum applied N - 2
def sum_n_applied_until_date(tid, date_iso):
    """
    Return sum(n_app) for a given tid up to and including date_iso (YYYY-MM-DD).
    """
    conn, c = openDB('crop.db')
    total = 0.0
    if c:
        try:
            c.execute("SELECT SUM(n_app) FROM nitrogen_applied WHERE tid = ? AND date <= ?", (tid, date_iso))
            row = c.fetchone()
            if row and row[0] is not None:
                total = float(row[0])
        finally:
            conn.close()
    return total

# Read max allowed N 
def maxAllowedNdB(cropname, experimentname, treatmentname, allowedN, simulation_id=None):
    """
    Saves the maximum allowed nitrogen to allowedNitrogen table.
    If the allowedNitrogen table has a simulation_id column and simulation_id is provided,
    insert a simulation-scoped row. Otherwise fall back to existing (tid, t_exid, allowedN).
    """
    conn, c = openDB('crop.db')
    if not c:
        return False
    try:
        t_exid = read_experimentDB_id(cropname, experimentname)
        tid = read_treatmentDB_id(t_exid, treatmentname)

        # Inspect allowedNitrogen schema to check for simulation_id column
        c.execute("PRAGMA table_info(allowedNitrogen)")
        cols = [r[1] for r in c.fetchall()]

        if 'simulation_id' in cols and simulation_id is not None:
            record_tuple = (tid, t_exid, simulation_id, allowedN)
            c.execute("INSERT INTO allowedNitrogen (tid, t_exid, simulation_id, allowedN) VALUES (?, ?, ?, ?)", record_tuple)
        else:
            record_tuple = (tid, t_exid, allowedN)
            c.execute("INSERT INTO allowedNitrogen (tid, t_exid, allowedN) VALUES (?, ?, ?)", record_tuple)

        conn.commit()
        return True
    except Exception as e:
        print("maxAllowedNdB error:", e)
        conn.rollback()
        return False
    finally:
        try:
            conn.close()
        except:
            pass

def get_max_allowed_n(tid, t_exid, simulation_id=None):
    """
    Return the latest allowedN value.
    Behavior:
      - If simulation_id provided and allowedNitrogen contains simulation_id column,
        return latest row filtered by simulation_id.
      - Otherwise return latest row filtered by tid and t_exid (backwards compatible).
    Returns float or None.
    """
    conn, c = openDB('crop.db')
    try:
        c.execute("PRAGMA table_info(allowedNitrogen)")
        cols = [r[1] for r in c.fetchall()]

        if simulation_id is not None and 'simulation_id' in cols:
            c.execute("SELECT allowedN FROM allowedNitrogen WHERE simulation_id = ? ORDER BY rowid DESC LIMIT 1", (simulation_id,))
            row = c.fetchone()
            if row and row[0] is not None:
                return float(row[0])

        # fallback to tid + t_exid lookup
        c.execute("SELECT allowedN FROM allowedNitrogen WHERE tid = ? AND t_exid = ? ORDER BY rowid DESC LIMIT 1", (tid, t_exid))
        row = c.fetchone()
        return float(row[0]) if row and row[0] is not None else None
    except Exception as e:
        print("get_max_allowed_n error:", e)
        return None
    finally:
        try:
            conn.close()
        except:
            pass

def get_nitrogen_applied_map(tid, up_to_date=None, t_exid=None):
    """
    Return dict mapping date (YYYY-MM-DD) -> n_app for entries in nitrogen_applied for given tid.
    If up_to_date provided (YYYY-MM-DD), only returns rows with date <= up_to_date.
    If t_exid provided, restrict results to that experiment id (prevents picking values from other experiments/runs).
    Backwards-compatible: callers that pass only (tid) or (tid, up_to_date=...) still work.
    """
    conn, c = openDB('crop.db')
    try:
        params = [tid]
        q = "SELECT date, n_app FROM nitrogen_applied WHERE tid = ?"
        if t_exid is not None:
            q += " AND t_exid = ?"
            params.append(t_exid)
        if up_to_date:
            q += " AND date <= ?"
            params.append(up_to_date)
        q += " ORDER BY date ASC"
        c.execute(q, tuple(params))
        rows = c.fetchall()
        return {r[0]: float(r[1]) for r in rows} if rows else {}
    finally:
        try:
            conn.close()
        except:
            pass

# Read existing expert entries
def get_nitrogen_applied_by_tid(tid, up_to_date=None):
    """
    Return dict mapping date (YYYY-MM-DD) -> n_app for entries in nitrogen_applied for given tid.
    If up_to_date provided (YYYY-MM-DD), only returns rows with date <= up_to_date.
    """
    conn, c = openDB('crop.db')
    try:
        if up_to_date:
            q = "SELECT date, n_app FROM nitrogen_applied WHERE tid = ? AND date <= ?"
            c.execute(q, (tid, up_to_date))
        else:
            q = "SELECT date, n_app FROM nitrogen_applied WHERE tid = ?"
            c.execute(q, (tid,))
        rows = c.fetchall()
        return {r[0]: float(r[1]) for r in rows} if rows else {}
    finally:
        try:
            conn.close()
        except:
            pass 



def delete_n_applied(tid, t_exid, date_iso, askUserFlag=True):
    """
    Delete a single nitrogen_applied row by (tid, date).
    - tid: treatment id (int)
    - t_exid: experiment id (int)
    - date_iso: 'YYYY-MM-DD' string
    - askUserFlag: if True, prompt user for confirmation via messageUserDelete()
    Returns True on success, False otherwise.
    """
    if askUserFlag:
        if not messageUserDelete(f"Delete Applied N entry for {date_iso}?"):
            return False

    conn, c = openDB('crop.db')
    if not c:
        return False
    try:
        # Use t_exid as additional safety if provided
        if t_exid is not None:
            c.execute("DELETE FROM nitrogen_applied WHERE tid = ? AND t_exid = ? AND date = ?", (tid, t_exid, date_iso))
        else:
            c.execute("DELETE FROM nitrogen_applied WHERE tid = ? AND date = ?", (tid, date_iso))
        conn.commit()
        return True
    except Exception as e:
        print("delete_nitrogen_applied error:", e)
        conn.rollback()
        return False
    finally:
        try:
            conn.close()
        except:
            pass


