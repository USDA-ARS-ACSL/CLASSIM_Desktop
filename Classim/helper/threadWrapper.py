import subprocess
import time
import os
import pandas as pd
import sys
from PyQt5.QtCore import pyqtSignal, QThread
from CustomTool.getClassimDir import *
from DatabaseSys.Databasesupport import *

import traceback
#from helper.config import classimDir, runDir, storeDir

# this class used for threading the simullation models  
class SimulationWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int)
  

    def __init__(self, exe_path, runname, simulation_id, parent=None):
        super().__init__(parent)
        self.exe_path = exe_path
        self.runname = runname
        self.simulation_id = simulation_id

    def run(self):
        import subprocess
        import re
        self.progress.emit("Starting simulation...")

        self.simulation_id_str = self.simulation_id[0] if isinstance(self.simulation_id, list) else str(self.simulation_id)

      
        try: 
            p = subprocess.Popen(
                [str(self.exe_path), str(self.runname), str(self.simulation_id_str)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True
            )
            for line in iter(p.stdout.readline, b''):
                if not line:
                    break

                decoded = line.strip()   
                if isinstance(decoded, str):
                    self.progress.emit(decoded)
                else:
                    self.progress.emit(str(decoded))   

   
                # Optionally, parse progress and emit only progress lines
                if 'Progress' in decoded:
                    prog = re.findall(r"[-+]?\d*\.\d+|\d+", decoded)
                    if prog:
                        self.progress.emit(f"Simulation Progress: {prog[0]}%")  

            p.stdout.close()
            p.wait()
            self.finished.emit(p.returncode)   

        except Exception as e:
            error_details = traceback.format_exc()
            print("Exception occurred during simulation execution:")
            print(error_details)
            self.progress.emit(f"Error: {e}")
            self.progress.emit(traceback.format_exc())  # add this line to emit the full traceback
            self.finished.emit(-1)



 # next three functions for threading:
def start_simulation(exe_path, runname, result, simStatus, simulation_name, widget_instance,controller= None):
    # Store the worker reference on the widget to prevent premature garbage collection
   # from helper.threadWrapper import SimulationWorker
    simWorker = SimulationWorker(exe_path, runname, simulation_name)
    widget_instance.simWorker = simWorker
    
    simWorker.progress.connect(lambda msg: on_simulation_progress(msg, widget_instance.simStatus))  # on_simulation_progress)
    simWorker.finished.connect(lambda code: on_simulation_finished(widget_instance, code, result, simStatus, simulation_name, controller))
    simWorker.finished.connect(lambda _: cleanup_worker(widget_instance))  # Ensure cleanup
    simWorker.finished.connect(lambda code: print(f"FINISHED SIGNAL RECEIVED: {code}"))

    simWorker.start()

def on_simulation_progress(text, simStatus):
    
    if text.strip():
        if 'Progress=' in text and 'Simulation Progress' not in text:                     
            return              
        # Terminal Print
        print(text)   
        if 'Simulation Progress' in text:
            formatted_text = f"<b>{text}</b>"  
            simStatus.setText(formatted_text)  # Update GUI
            simStatus.repaint()         
    else:
        print(text)


def on_simulation_finished(widget_instance, returncode, result, simStatus, simulation_name, controller=None):
    sitename = result[0] if result else None # If result is a list or tuple
    crop = result[1] 
    fieldpath = result[2]
    expSystem_flag = result[3]

    missingRec = ""
    if returncode == 0 and missingRec == "":
        simStatus.setText("Simulation completed successfully.")

    #Check for NaN on output files
        file_ext = ["g01","G03","G04","G05","G07"] 
        for ext in file_ext:
            g_name2 = fieldpath+"\\\\"+sitename+"."+ext
            table_name = ext.lower()+"_"+crop

            if not os.path.exists(g_name2):
                msg = f"Missing file: {g_name2}"
                print(msg.strip())
                missingRec += msg
                continue
   
            missingRec += checkNaNInOutputFile(table_name,g_name2)
          # print(missingRec)

        if crop != "fallow":
            ps_file = os.path.join(fieldpath, "plantstress.crp")
            if os.path.exists(ps_file):
                 missingRec += checkNaNInOutputFile("plantStress_" + crop, ps_file)
            else:
                missingRec += f"Missing file: {ps_file}"

            if crop in ("potato", "soybean"):
                n_file = os.path.join(fieldpath, "nitrogen.crp")
                if os.path.exists(n_file):
                    missingRec += checkNaNInOutputFile("nitrogen_" + crop, n_file)
                else:
                    missingRec += f"Missing file: {n_file}"

        if missingRec != "":
            sim_id = simulation_name[0] if isinstance(simulation_name, (list, tuple)) else simulation_name
            delete_pastrunsDB(str(simulation_name), crop)
            simStatus.setText("<b>Something went wrong with this run.  The details are shown below.  We are unable to store results of this run until the problem can be resolved.  Additional details shown below.  The following file/columns displayed NaN values:</b><br>"+missingRec)
        else:
        # Ingesting table  into cropOutput database
            
            simStatus.setText("<b>Ingesting output files in the database.")
            simStatus.repaint()

            sim_id = simulation_name[0] if isinstance(simulation_name, (list, tuple)) else simulation_name
            for ext in file_ext:
             #  g_name = fieldpath+"\\"+sitename+"."+ext
                g_name2 = fieldpath+"\\\\"+sitename+"."+ext
                table_name = ext.lower()+"_"+crop
            # Ingest .grd file and Area from G03 file on the geometry table
                sim_id = simulation_name[0] if isinstance(simulation_name, (list, tuple)) else simulation_name
                if ext == 'G03' or ext == 'g03':
                    ingestGeometryFile(fieldpath + "\\\\" + sitename + ".grd", g_name2, str(sim_id))
                ingestOutputFile(table_name, g_name2, str(sim_id))

            ingestOutputFile("plantStress_"+crop,fieldpath+"\\\\plantstress.crp",str(sim_id))
    #        if remOutputFilesFlag:
    #            os.remove(fieldpath+"\\\\plantstress.crp")

            if crop == "soybean" or crop == "potato":
                ingestOutputFile("nitrogen_"+crop,fieldpath+"\\\\nitrogen.crp",str(sim_id))
       #         if remOutputFilesFlag:
     #               os.remove(fieldpath+"\\\\nitrogen.crp")
                    
            from TabbedDialog.SeasonalTab import signal_instance
            
            if expSystem_flag == True:
                signal_instance.exsystemsig.emit(int(sim_id))
                simStatus.setText("<b>Check your simulation results on Expert System tab.</b>")
            else:
                signal_instance.seasonalsig.emit(int(sim_id)) #emitting the simulation id (integer)
                simStatus.setText("<b>Check your simulation results on Output tab.</b>")
    elif returncode == 0 and missingRec != "":
         simStatus.setText("<b>Simulation finished, but output is invalid or incomplete.</b><br>" + missingRec)
    else:
        simStatus.setText(f"Simulation failed to execute (code {returncode}).")     

     # --- notify nitrogen controller that the full run is complete ---
    try:
        if controller is not None and hasattr(controller, "NFullSimulationComplete"):
            controller.NFullSimulationComplete()
    except Exception as e:
        print("DEBUG: NFullSimulationComplete raised:", e)

    cleanup_worker(widget_instance)


def cleanup_worker(widget_instance):
    worker = getattr(widget_instance, "simWorker", None)
    if worker and worker.isRunning():
        worker.quit()
        worker.wait()
    widget_instance.simWorker = None  # Clear reference


        

