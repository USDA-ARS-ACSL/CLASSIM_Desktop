import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from datetime import date, timedelta, datetime
from time import mktime
from shutil import copyfile

'''
Generates dictionaries that will be used on outputTab.py and RotOutputTab.py.  The dictionaries correpond to 
tables on cropOutput database.
'''

def genDictOutput(cropArr,tabName,rotFlag):

    ########## plantTab ##########
    # g01_cropname table 
    # Maize
    varDescMaiDict = {'Leaves':'Number of leaves (appeared) (crop)','MaturLvs':'Number of mature leaves (crop)',
                      'Dropped':'Number of dropped leaves (crop)','LA_pl':'Green leaf area per plant (crop)',
                      'LA_dead':'Dead leaf area (crop)','LAI':'Leaf area index (crop)','RH':'Relative humidity (crop)',
                      'LeafWP':'Leaf water potential (crop)','PFD':'Photosynthetic photon flux density (crop)',
                      'SolRad':'Solar radiation (crop)','SoilT':'Soil temperature at soil surface (crop)',
                      'Tair':'Air temperture at 2m (crop)','Tcan':'Canopy temperature (crop)','ETdmd':'Potential Transpiration (crop)',
                      'ETsply':'Actual Transpiration (crop)','Pn':'Net Photosynthesis (crop)','Pg':'Gross photosynthesis (crop)',
                      'Respir':'Respiration (crop)','av_gs':'Average stomatal conductance (crop)','VPD':'Vapor pressure deficit (crop)',
                      'Nitr':'gr N per m2 leaf (crop)','N_Dem':'Nitrogen demand (crop)','NUpt':'Nitrogen uptake (crop)',
                      'LeafN':'Leaf nitrogen content (crop)','PCRL':'Carbon allocated to roots (crop)','totalDM':'Total dry matter (crop)',
                      'shootDM':'Shoot dry matter (crop)','earDM':'Ear dry matter (crop)','TotLeafDM':'Leaf dry matter (crop)',
                      'DrpLfDM':'Dropped leaf dry matter (crop)','stemDM':'Stem dry matter (crop)','rootDM':'Root dry matter (crop)',
                      'SoilRt':'Carbon in soil roots (crop)','MxRtDep':'Maximum root depth (crop)','AvailW':'Available water in root zone (crop)',
                      'solubleC':'Soluble sugars as carbon (crop)'}
    varDescUnitMaiDict = {'Leaves':'Number of leaves (appeared) (crop)','MaturLvs':'Number of mature leaves (crop)',
                          'Dropped':'Number of dropped leaves (crop)','LA_pl':'Green leaf area per plant (crop) (cm2)',
                          'LA_dead':'Dead leaf area (crop) (cm2)','LAI':'Leaf area index (crop)',
                          'RH':'Relative humidity (crop) (%)','LeafWP':'Leaf water potential (crop) (bars)',
                          'PFD':'Photosynthetic photon flux density (crop) (mol photons/day/m2)','SolRad':'Solar radiation (crop) (W/m2)',
                          'SoilT':'Soil temperature at soil surface (crop) (oC)','Tair':'Air temperture at 2m (crop) (oC)',
                          'Tcan':'Canopy temperature (crop) (oC)','ETdmd':'Potential Transpiration (crop) (g/plant)',
                          'ETsply':'Actual Transpiration (crop) (g/plant)','Pn':'Net Photosynthesis (crop) (g carbohydrate/plant/day)',
                          'Pg':'Gross photosynthesis (crop) (g carbohydrate/plant/day)','Respir':'Respiration (crop) (g carbohydrate/plant/day)',
                          'av_gs':'Average stomatal conductance (crop) (micro-mol/m2/s)','VPD':'Vapor pressure deficit (crop) (kPa)',
                          'Nitr':'grams nitrogen per m2 leaf (crop) (g/m2)','N_Dem':'Nitrogen demand (crop) (g/plant)',
                          'NUpt':'Nitrogen uptake (crop) (g/plant)','LeafN':'Leaf nitrogen content (crop) (%)',
                          'PCRL':'Carbon allocated to roots (crop) (g/plant)','totalDM':'Total dry matter (crop) (g/plant)',
                          'shootDM':'Shoot dry matter (crop) (g/plant)','earDM':'Ear dry matter (crop) (g/plant)',
                          'TotLeafDM':'Leaf dry matter (crop) (g/plant)','DrpLfDM':'Dropped leaf dry matter (crop) (g/plant)',
                          'stemDM':'Stem dry matter (crop) (g/plant)','rootDM':'Root dry matter (crop) (g/plant)',
                          'SoilRt':'Carbon in soil roots (crop) (g/plant)','MxRtDep':'Maximum root depth (crop) (cm)',
                          'AvailW':'Available water in root zone (crop) (g)','solubleC':'Soluble sugars as carbon (crop) (g/plant)'}
    varFuncMaiDict = {'Leaves':'max','MaturLvs':'max','Dropped':'max','LA_pl':'max','LA_dead':'max','LAI':'max',
                      'RH':'mean','LeafWP':'mean','PFD':'sum','SolRad':'mean','SoilT':'mean','Tair':'mean',
                      'Tcan':'mean','ETdmd':'sum','ETsply':'sum','Pn':'sum','Pg':'sum','Respir':'sum',
                      'av_gs':'mean','VPD':'mean','Nitr':'max','N_Dem':'max','NUpt':'max','LeafN':'max',
                      'PCRL':'sum','totalDM':'max','shootDM':'max','earDM':'max','TotLeafDM':'max','DrpLfDM':'max',
                      'stemDM':'max','rootDM':'max','SoilRt':'max','MxRtDep':'max','AvailW':'max','solubleC':'max'}

    # Potato
    varDescPotDict = {'LAI':'Leaf area index (crop)','PFD':'Photosynthetic photon flux density (crop)','SolRad':'Solar radiation (crop)',
                      'Tair':'Air temperture at 2m (crop)','Tcan':'Canopy temperature (crop)','Pgross':'Gross photosynthesis (crop)',
                      'Rg+Rm':'Respiration (crop)','Tr-Pot':'Potential transpiration (crop)','Tr-Act':'Actual transpiration (crop)',
                      'Stage':'Stage (crop)','totalDM':'Total dry matter (crop)','leafDM':'Leaf dry matter (crop)',
                      'stemDM':'Stem dry matter (crop)','rootDM':'Root dry matter (crop)','tuberDM':'Tuber dry matter (crop)',
                      'deadDM':'Dead dry matter (crop)','LWPave':'Leaf water potential (crop)','gs_ave':'Average stomatal conductance (crop)',
                      'N_uptake':'Nitrogen Uptake (crop)','tot_N':'Total Nitrogen in the Plant (crop)','leaf_N':'Leaf nitrogen content (crop)',
                      'stem_N':'Stem nitrogen (crop)','root_N':'Root nitrogen (crop)','tuber_N':'Tuber nitrogen (crop)'}
    varDescUnitPotDict = {'LAI':'Leaf area index (crop)','PFD':'Photosynthetic photon flux density (crop) (mol photons/day/m2)',
                          'SolRad':'Solar radiation (crop) (W/m2)','Tair':'Air temperture at 2m (crop) (oC)',
                          'Tcan':'Canopy temperature (crop) (oC)','Pgross':'Gross photosynthesis (crop) (g carbohydrate/plant/day)',
                          'Rg+Rm':'Respiration (crop) (g carbohydrate/plant/day)','Tr-Pot':'Potential transpiration (crop) (g/plant)',
                          'Tr-Act':'Actual transpiration (crop) (g/plant)','Stage':'Stage (crop)',
                          'totalDM':'Total dry matter (crop) (g/plant)','leafDM':'Leaf dry matter (crop) (g/plant)',
                          'stemDM':'Stem dry matter (crop) (g/plant)','rootDM':'Root dry matter (crop) (g/plant)',
                          'tuberDM':'Tuber dry matter (crop) (g/plant)','deadDM':'Dead dry matter (crop) (g/plant)',
                          'LWPave':'Leaf water potential (crop) (bars)','gs_ave':'Average stomatal conductance (crop) (micro-mol/m2/s)',
                          'N_uptake':'Nitrogen Uptake (crop) (g/plant)','tot_N':'Total Nitrogen in the Plant (crop) (g/plant)',
                          'leaf_N':'Leaf nitrogen content (crop) (g/plant)','stem_N':'Stem nitrogen (crop) (g/plant)',
                          'root_N':'Root nitrogen (crop) (g/plant)','tuber_N':'Tuber nitrogen (crop) (g/plant)'}
    varFuncPotDict = {'LAI':'max','PFD':'sum','SolRad':'mean','Tair':'mean','Tcan':'mean','Pgross':'sum',
                      'Rg+Rm':'sum','Tr-Pot':'sum','Tr-Act':'sum','Stage':'max','totalDM':'max','leafDM':'max',
                      'stemDM':'max','rootDM':'max','tuberDM':'max','deadDM':'max','LWPave':'mean','gs_ave':'mean',
                      'N_uptake':'mean','tot_N':'mean','leaf_N':'mean','stem_N':'mean','root_N':'mean','tuber_N':'mean'}

    # Soybean
    varDescSoyDict = {'PFD':'Photosynthetic photon flux density (crop)','SolRad':'Solar radiation (crop)','Tair':'Air temperture at 2m (crop)',
	                  'Tcan':'Canopy temperature (crop)','Pgross':'Gross photosynthesis (crop)','Pnet':'Net photosynthesis (crop)',
	                  'gs':'Maximum stomatal conductance (crop)','PSIL':'Leaf water potential (crop)','LAI':'Leaf area index (crop)',
	                  'LAREAT':'Leaf area (crop)','totalDM':'Total dry matter (crop)','rootDM':'Root dry matter (crop)',
                      'stemDM':'Stem dry matter (crop)','leafDM':'Leaf dry matter (crop)','seedDM':'Seed dry matter (crop)',
	                  'podDM':'Pod dry matter (crop)','DeadDM':'Dead dry matter (crop)','Tr_pot':'Potential transpiration (crop)',
	                  'Tr_act':'Actual transpiration (crop)'}
    varDescUnitSoyDict = {'PFD':'Photosynthetic photon flux density (crop) (mol photons/day/m2)','SolRad':'Solar radiation (crop) (W/m2)',
                          'Tair':'Air temperture at 2m (crop) (oC)','Tcan':'Canopy temperature (crop) (oC)',
                          'Pgross':'Gross photosynthesis (crop) (g carbon/plant/day)','Pnet':'Net photosynthesis (crop) (g carbon/plant/day)',
                          'gs':'Maximum stomatal conductance (crop)','PSIL':'Leaf water potential (crop) (bars)',
                          'LAI':'Leaf area index (crop)','LAREAT':'Leaf area (crop) (cm2)',
                          'totalDM':'Total dry matter (crop) (g/plant)','rootDM':'Root dry matter (crop) (g/plant)',
                          'stemDM':'Stem dry matter (crop) (g/plant)','leafDM':'Leaf dry matter (crop) (g/plant)',
                          'seedDM':'Seed dry matter (crop) (g/plant)','podDM':'Pod dry matter (crop) (g/plant)',
                          'DeadDM':'Dead dry matter (crop) (g/plant)','Tr_pot':'Potential Transpiration (crop) (mg/plant)',
                          'Tr_act':'Actual Transpiration (crop) (mg/plant)'}
    varFuncSoyDict = {'PFD':'sum','SolRad':'mean','Tair':'mean','Tcan':'mean','Pgross':'sum','Pnet':'sum',
                      'gs':'mean','PSIL':'mean','LAI':'max','LAREAT':'max','totalDM':'max','rootDM':'max',
                      'stemDM':'max','leafDM':'max','seedDM':'max','podDM':'max','DeadDM':'max','Tr_pot':'sum',
                      'Tr_act':'sum'}

    # Cotton
    varDescCotDict = {'PlantH':'Plant height (crop)','LAI':'Leaf area index (crop)','LInt':'Canopy light interception (crop)','Nodes':'Number of main stem nodes (crop)',
                      'Sites':'Number of fruiting sites (crop)','N_Squares':'Number of squares (crop)','N_GB':'Number of green bolls (crop)',
                      'NLvsLoss':'Total number of leaves lost (crop)','NSqLoss':'Total number of squares lost (crop)','NBollsLoss':'Total number of bolls lost (crop)',
                      'NFruitShed':'Total number of abscised fruits (crop)','PetShd_DM':'Petal shed dry matter (crop)','GB_lossDM':'Green bolls lost dry matter (crop)',
                      'Lf_lossDM':'Leaves abscised dry matter (crop)','Rt_lossDM':'Root lost dry matter (crop)','Dd_WtDM':'Dead tissue lost dry matter (crop)',
                      'SquareDM':'Squares dry matter (crop)','GB_DM':'Green boll dry matter (crop)','OB_DM':'Open boll dry matter (crop)','LeafDM':'Leaf dry matter (crop)',
                      'StemDM':'Stem dry matter (crop)','RootDM':'Root dry matter (crop)','ResC':'Reserved dry matter (crop)','PlantDM':'Total plant dry matter (crop)',
                      'R_S':'Root shoot ratio (crop)','Yield':'Total yield (crop)','Temp':'Average temperature (crop)','L_Temp':'Average leaf temperature (crop)',
                      'Rain':'Rain+irrigation (crop)','SRad':'Solar radiation (crop)','PFD':'Photosynthetic photon flux density (crop)','RH':'Relative humidity (crop)',
                      'LeafN':'Leaf nitrogen content (crop)','StemN':'Stem nitrogen (crop)','SeedN':'Seed nitrogen (crop)','BurrN':'Burr nitrogen (crop)','RootN':'Root nitrogen (crop)',
                      'Nloss':'Nitrogen lost abscission (crop)','PlantN':'Total Nitrogen in the Plant (crop)','N_uptake':'Total nitrogen uptake (crop)',
                      'S_Psi':'Average soil water potential in the root zone (crop)','L_Psi':'Leaf water potential (crop)','LArea':'Leaf area (crop)',
                      'VPD':'Vapor pressure deficit (crop)','StCond':'Average stomatal conductance (crop)','Pnet':'Net photosynthesis (crop)','PGross':'Gross photosynthesis (crop)',
                      'L_Res':'Light respiration (crop)', 'Main_Res':'Maintenance respiration (crop)','Resp':'Total respiration (crop)','SPnet':'Cumulative net photosynthesis (crop)', 
                      'C_Bal':'Plant C balance (crop)','Nstress_Pn':'Nitrogen stress on the photosynthesis (crop)' }
    varDescUnitCotDict = {'PlantH':'Plant height (crop) (cm)','LAI':'Leaf area index (crop)','LInt':'Canopy light interception (crop)','Nodes':'Number of main stem nodes (crop)',
                          'Sites':'Number of fruiting sites (crop)','N_Squares':'Number of squares (crop)','N_GB':'Number of green bolls (crop)',
                          'NLvsLoss':'Total number of leaves lost (crop)','NSqLoss':'Total number of squares lost (crop)','NBollsLoss':'Total number of bolls lost (crop)',
                          'NFruitShed':'Total number of abscised fruits (crop)','PetShd_DM':'Petal shed dry matter (crop) (g carbon/plant)',
                          'GB_lossDM':'Green bolls lost dry matter (crop) (g carbon/plant)','Lf_lossDM':'Leaves absciseddry matter (crop) (g carbon/plant)',
                          'Rt_lossDM':'Root lost dry matter (crop) (g carbon/plant)','Dd_WtDM':'Dead tissue lost dry matter (crop) (g/plant)',
                          'SquareDM':'Squares dry matter (crop) (g/plant)','GB_DM':'Green boll dry matter (crop) (g/plant)','OB_DM':'Open boll dry matter (crop) (g/plant)',
                          'LeafDM':'Leaf dry matter (crop) (g/plant)','StemDM':'Stem dry matter (crop) (g/plant)','RootDM':'Root dry matter (crop) (g/plant)',
                          'ResC':'Reserved dry matter (crop) (g carbon/plant)','PlantDM':'Total plant dry matter (crop) (g carbon/plant)','R_S':'Root shoot ratio (crop)',
                          'Yield':'Total yield (crop) (kg/ha)','Temp':'Average temperature (crop) (oC)','L_Temp':'Average leaf temperature (crop) (oC)',
                          'Rain':'Rain+irrigation (crop) (mm/day)','SRad':'Solar radiation (crop) (W/m2)','PFD':'Photosynthetic photon flux density (crop) (mol photons/m2/day)',
                          'RH':'Relative humidity (crop) (%)','LeafN':'Leaf nitrogen content (crop) (g Nitrogen/plant)','StemN':'Stem nitrogen (crop) (g Nitrogen/plant)',
                          'SeedN':'Seed nitrogen (crop) (g Nitrogen/plant)','BurrN':'Burr nitrogen (crop) (g Nitrogen/plant)','RootN':'Root nitrogen (crop) (g Nitrogen/plant)',
                          'Nloss':'Nitrogen lost abscission (crop) (g Nitrogen/plant)','PlantN':'Total Nitrogen in the Plant (crop) (g/plant)',
                          'N_uptake':'Total nitrogen uptake (crop) (g Nitrogen/plant)','S_Psi':'Average soil water potential in the root zone (crop) (bar)',
                          'L_Psi':'Leaf water potential (crop) (bar)','LArea':'Leaf area (crop) (cm2)','VPD':'Vapor pressure deficit (crop) (k Pa)',
                          'StCond':'Average stomatal conductance (crop) (micro-mol/m2/sec)','Pnet':'Net photosynthesis (crop) (g carbon/plant)',
                          'PGross':'Gross photosynthesis (crop) (g carbon/plant)','L_Res':'Light respiration (crop) (g carbon/plant)','Main_Res':'Maintenance respiration (crop) (g carbon/plant)', 'Resp':'Total respiration (crop) (g carbon/plant)',
                          'SPnet':'Cumulative net photosynthesis (crop) (g carbon/plant)', 'C_Bal':'Plant C balance (crop) (g carbon/plant)',
                          'Nstress_Pn':'Nitrogen stress on the photosynthesis (crop)'}
    varFuncCotDict = {'PlantH':'max','LAI':'max','LInt':'max','Nodes':'max','Sites':'max','N_Squares':'max','N_GB':'max','NLvsLoss':'max','NSqLoss':'max','NBollsLoss':'max',
                      'NFruitShed':'max','PetShd_DM':'max','GB_lossDM':'max','Lf_lossDM':'max','Rt_lossDM':'max','Dd_WtDM':'max','SquareDM':'max','GB_DM':'max','OB_DM':'max',
                      'LeafDM':'max','StemDM':'max','RootDM':'max','ResC':'max','PlantDM':'max','R_S':'max','Yield':'max','Temp':'max','L_Temp':'max','Rain':'max','SRad':'max',
                      'PFD':'max','RH':'max','LeafN':'max','StemN':'max','SeedN':'max','BurrN':'max','RootN':'max','Nloss':'max','PlantN':'max','N_uptake':'max','S_Psi':'max',
                      'L_Psi':'max','LArea':'max','VPD':'max','StCond':'max','Pnet':'max','PGross':'max','L_Res':'max','Main_Res':'max','Resp':'max','SPnet':'max', 'C_Bal':'max',
                      'Nstress_Pn':'max'}

    ########## Soil Carbon Nitrogen tab ##########
    # g07_cropname table 
    varSoilCNDescDict = {'Humus_N':'Amount of Nitrogen in Humus','Humus_C':'Amount of Carbon in Humus',
                         'Litter_N':'Amount of Nitrogen in Litter','Litter_C':'Amount of Carbon in Litter',
                         'Manure_N':'Amount of Nitrogen in Manure','Manure_C':'Amount of Carbon in Manure',
                         'Root_N':'Amount of Nitrogen in Root','Root_C':'Amount of Carbon in Root'}
    varSoilCNDescUnitDict = {'Humus_N':'Amount of Nitrogen in Humus (kg/ha)','Humus_C':'Amount of Carbon in Humus (kg/ha)',
                             'Litter_N':'Amount of Nitrogen in Litter (kg/ha)','Litter_C':'Amount of Carbon in Litter (kg/ha)',
                             'Manure_N':'Amount of Nitrogen in Manure (kg/ha)','Manure_C':'Amount of Carbon in Manure (kg/ha)',
                             'Root_N':'Amount of Nitrogen in Root (kg/ha)','Root_C':'Amount of Carbon in Root (kg/ha)'}
    varSoilCNFuncDict = {'Humus_N':'sum','Humus_C':'sum','Litter_N':'sum','Litter_C':'sum','Manure_N':'sum','Manure_C':'sum',
                         'Root_N':'sum','Root_C':'sum'}

    ########## Soil Water Heat Nitrogen components 2D ##########
    # g03_cropname table 
    # Same variables for all crops
    varSoilwhn2DDescDict = {"hNew":"Soil Matric Potential","thNew":"Soil Water Content",
                            "NO3N":"Nitrogen Concentration","Temp":"Average Temperature"} 
    varSoilwhn2DDescUnitDict = {"hNew":"Soil Matric Potential\n(cm suction)","thNew":"Soil Water Content\n(cm3/cm3)",
                                "NO3N":"Nitrogen Concentration\n(mg/L)","Temp":"Average Temperature\n(oC)"} 
    varSoilwhn2DFuncDict = {'hNew':'mean','thNew':'mean','NO3N':'mean','Temp':'mean'} 

    ########## Soil Time Series ##########
    # g03_cropname table 
    # Same variables for all crops
    varSoilTSDescDict = {"hNew":"Soil Matric Potential","thNew":"Soil Water Content",
                         "NO3N":"Nitrogen Concentration","Temp":"Average Temperature"}
    varSoilTSDescUnitDict = {"hNew":"Soil Matric Potential\n(cm suction)","thNew":"Soil Water Content\n(cm3/cm3)",
                             "NO3N":"Nitrogen Concentration\n(mg/L)","Temp":"AverageTemperature\n(oC)"}
    varSoilTSFuncDict = {'hNew':'mean','thNew':'mean','NO3N':'sum','Temp':'mean'}

    ########## Root tab ##########
    # g04_cropname table 
    # Same variables for all crops

    varRootDescDict = {"RDenT":"Root Density Total","RMassT":"Root Mass Total"}
    varRootDescUnitDict = {"RDenT":"Root Density Total (cm/cm2)","RMassT":"Root Mass Total (g/cm2)"}
    varRootFuncDict = {'RDenT':'max','RMassT':'max'}
    
    ### Surface Characteristics tab ###
    # g05_cropname table 
    # Same variables for all crops
    varSurfChaDescDict = {'PSoilEvap':'Potential soil evaporation','ASoilEVap':'Actual Soil evaporation',
                          'PE_T_int':'Potential transpiration by leaf energy balance','transp':'Transpiration',
                          'SeasPSoEv':'Seasonal potential soil evaporation','SeasASoEv':'Seasonal actual soil evaporation',
                          'SeasPTran':'Seasonal potential transpiration','SeasATran':'Seasonal actual transpiration',
                          'SeasRain':'Seasonal rainfall','SeasInfil':'Seasonal infiltration','Runoff':'Runoff', 'ThetaAvail':'ThetaAvail',
                          'CO2Flux':'Carbon Dioxide Flux','O2Flux':'Oxygen Flux','TotIrrig':'Total Irrigation'}
    varSurfChaDescUnitDict = {'PSoilEvap':'Potential soil evaporation (mm/cm2)','ASoilEVap':'Actual Soil evaporation (mm/cm2)',
                              'PE_T_int':'Potential transpiration by leaf energy balance (mm/cm2)','transp':'Transpiration (mm/cm2)',
                              'SeasPSoEv':'Seasonal potential soil evaporation (mm/cm2)','SeasASoEv':'Seasonal actual soil evaporation (mm/cm2)',
                              'SeasPTran':'Seasonal potential transpiration (mm/cm2)','SeasATran':'Seasonal actual transpiration (mm/cm2)',
                              'SeasRain':'Seasonal rainfall (mm/cm2)','SeasInfil':'Seasonal infiltration (mm/cm2)','Runoff':'Runoff (mm/cm2)', 'ThetaAvail':'ThetaAvail (%)',
                              'CO2Flux':'Carbon Dioxide Flux (kg CO2/ha)','O2Flux':'Oxygen Flux (kg O2/ha)','TotIrrig':'Total Irrigation (mm/day)'}
    varSurfChaFuncDict = {'PSoilEvap':'sum','ASoilEVap':'sum','PE_T_int':'sum','transp':'sum','SeasPSoEv':'max',
                          'SeasASoEv':'max','SeasPTran':'max','SeasATran':'max','SeasRain':'max','SeasInfil':'max',
                          'Runoff':'sum', 'ThetaAvail':'max','CO2Flux':'sum','O2Flux':'sum','TotIrrig':'sum'}

    # The dictionary for plant will not be the same for simulation and rotation
    if tabName  == "plant":  
        # Single simulation
        if rotFlag == 0:
            finalVarDescDict = dict()
            finalVarDescUnitDict = dict()
            finalVarFuncDict = dict()
            if cropArr[0] == "maize":
                finalVarDescDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescMaiDict.items()}
                finalVarDescUnitDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescUnitMaiDict.items()}
                finalVarFuncDict = {f"{key}": str(val).replace("(crop)","") for key, val in varFuncMaiDict.items()}
            elif cropArr[0] == "potato":
                finalVarDescDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescPotDict.items()}
                finalVarDescUnitDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescUnitPotDict.items()}
                finalVarFuncDict = {f"{key}": str(val).replace("(crop)","") for key, val in varFuncPotDict.items()}
            elif cropArr[0] == "soybean":
                finalVarDescDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescSoyDict.items()}
                finalVarDescUnitDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescUnitSoyDict.items()}
                finalVarFuncDict = {f"{key}": str(val).replace("(crop)","") for key, val in varFuncSoyDict.items()}
            elif cropArr[0] == "cotton":
                finalVarDescDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescCotDict.items()}
                finalVarDescUnitDict = {f"{key}": str(val).replace("(crop)","") for key, val in varDescUnitCotDict.items()}
                finalVarFuncDict = {f"{key}": str(val).replace("(crop)","") for key, val in varFuncCotDict.items()}

            return finalVarDescDict, finalVarDescUnitDict, finalVarFuncDict
        else:
            finalVarDescDict = dict()
            finalVarDescUnitDict = dict()
            finalVarFuncDict = dict()
            for runNum in range(len(cropArr)):
                tempVarDescDict = dict()
                tempVarDescUnitDict = dict()
                tempVarFuncDict = dict()

                if cropArr[runNum] == "maize":
                    tempVarDescDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescMaiDict.items()}
                    tempVarDescUnitDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescUnitMaiDict.items()}
                    tempVarFuncDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varFuncMaiDict.items()}
                elif cropArr[runNum] == "potato":
                    tempVarDescDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescPotDict.items()}
                    tempVarDescUnitDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescUnitPotDict.items()}
                    tempVarFuncDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varFuncPotDict.items()}
                elif cropArr[runNum] == "soybean":
                    tempVarDescDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescSoyDict.items()}
                    tempVarDescUnitDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescUnitSoyDict.items()}
                    tempVarFuncDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varFuncSoyDict.items()}
                elif cropArr[runNum] == "cotton":
                    tempVarDescDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescCotDict.items()}
                    tempVarDescUnitDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varDescUnitCotDict.items()}
                    tempVarFuncDict = {f"{key}__{cropArr[runNum][0:3]}": str(val).replace("crop",cropArr[runNum]) for key, val in varFuncCotDict.items()}

                finalVarDescDict.update(tempVarDescDict) 
                finalVarDescUnitDict.update(tempVarDescUnitDict) 
                finalVarFuncDict.update(tempVarFuncDict) 

            return finalVarDescDict, finalVarDescUnitDict, finalVarFuncDict
    elif tabName  == "soilCN":
        return varSoilCNDescDict, varSoilCNDescUnitDict, varSoilCNFuncDict
    elif tabName  == "soilwhn2D":
        return varSoilwhn2DDescDict, varSoilwhn2DDescUnitDict, varSoilwhn2DFuncDict
    elif tabName  == "soilTS":
        return varSoilTSDescDict, varSoilTSDescUnitDict, varSoilTSFuncDict
    elif tabName  == "root":
        return varRootDescDict, varRootDescUnitDict, varRootFuncDict
    elif tabName  == "surfCha":
        return varSurfChaDescDict, varSurfChaDescUnitDict, varSurfChaFuncDict
