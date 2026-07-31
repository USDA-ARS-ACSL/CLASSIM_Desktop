import subprocess
import traceback
import re
import os
import pandas as pd
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from CustomTool.getClassimDir import *
from DatabaseSys.Databasesupport import *
import shutil

# --- Worker class (now based on QObject) ---
class SimulationWorkerES(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int, object, object)
    simulation_failed = pyqtSignal(object, str) # Emit simulation_name, error_message


    def __init__(self, exe_path, runname, simulation_id, result_data, parent=None):
        super().__init__(parent)
        self.exe_path = exe_path
        self.runname = runname
        self.simulation_id = simulation_id
        self.result_data = result_data # Store result data to pass back
        self.sim_process = None # To hold the subprocess instance

   #     print(f"[WORKER INIT] EXE: {exe_path}, Runname: {runname}, ID: {simulation_id}")

    def run(self):
        try:
            self.progress.emit("Starting simulation...")

            # Ensure simulation_id is a string or appropriate type for command line
            sim_id_str = str(self.simulation_id[0]) if isinstance(self.simulation_id, list) else str(self.simulation_id)
            # Extract the directory of the runname to set as cwd for the subprocess
            run_directory = os.path.dirname(self.runname)

            # Command list should be clean strings
            command = [str(self.exe_path), str(self.runname), str(sim_id_str)]
            print(f"[DEBUG] About to run subprocess: {command} in CWD: {run_directory}")

            try:
                self.sim_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    text=True,
                    cwd=run_directory # Set the current working directory for the subprocess
                )
            except Exception as e:
                print(f"[ERROR] Failed to start subprocess: {e}")
                self.progress.emit(f"Subprocess error: {e}")
                self.finished.emit(-1, self.result_data, self.simulation_id)
                self.simulation_failed.emit(self.simulation_id, f"Failed to start subprocess: {e}")
                return

            # Read output
            for line in iter(self.sim_process.stdout.readline, ''):
                if not line:
                    break
                decoded = line.strip()
                self.progress.emit(decoded)

                if 'Progress' in decoded:
                    prog = re.findall(r"[-+]?\d*\.\d+|\d+", decoded)
                    if prog:
                        self.progress.emit(f"Simulation Progress: {prog[0]}%")

            self.sim_process.stdout.close()
            stderr_output = self.sim_process.stderr.read() # Read all stderr
            self.sim_process.stderr.close()
            self.sim_process.wait() # Wait for the process to terminate

            return_code = self.sim_process.returncode
            print(f"[DEBUG] Subprocess finished with return code {return_code}")
            if return_code != 0:
                print(f"[ERROR] Simulation exited with non-zero code: {return_code}. Stderr: {stderr_output}")
                self.progress.emit(f"Simulation failed. Error: {stderr_output}")
                self.simulation_failed.emit(self.simulation_id, stderr_output)

            self.finished.emit(return_code, self.result_data, self.simulation_id)

        except Exception as e:
            error_details = traceback.format_exc()
            print("[FATAL ERROR] Exception occurred during simulation execution:")
            print(error_details)
            self.progress.emit(f"Error: {e}")
            self.progress.emit(error_details)
            self.finished.emit(-1, self.result_data, self.simulation_id)
            self.simulation_failed.emit(self.simulation_id, f"Unhandled exception: {e}\n{error_details}")

    def stop(self):
        if self.sim_process and self.sim_process.poll() is None:
            self.sim_process.terminate()
            self.sim_process.wait(timeout=5)
            if self.sim_process.poll() is None:
                self.sim_process.kill()



# --- Start simulation with thread management ---
def start_simulationES(exe_path, runname, result, simStatus, simulation_name, widget_instanceES, controller):
    simWorker = SimulationWorkerES(exe_path, runname, simulation_name, result, parent=widget_instanceES) # Pass result data to worker
    widget_instanceES.activeSimWorkers.append(simWorker) # Add to list for tracking

    # Connect signals
    simWorker.progress.connect(lambda msg: on_simulation_progressES(msg, simStatus))
    simWorker.finished.connect(lambda code, res, sim_name: on_simulation_finishedES(widget_instanceES, code, res, simStatus, sim_name, controller))
    simWorker.simulation_failed.connect(lambda sim_name, error_msg: print(f"Simulation {sim_name} failed: {error_msg}"))

    simWorker.start() # Start the thread
    print(f"Simulation {simulation_name} worker started.")

# --- Progress update handler ---
def on_simulation_progressES(text, simStatus):
    if text.strip():
      #  print(f"PROGRESS: {text}")
        if 'Progress=' in text and 'Simulation Progress' not in text:
            return
        print(text)
        if 'Simulation Progress' in text:
            formatted = f"<b>{text}</b>"
            simStatus.setText(formatted)
            simStatus.repaint()
    else:
        print(text)

# --- Post-simulation result handling ---
def on_simulation_finishedES(widget_instanceES, returncode, result, simStatus, simulation_name, controller):
    sitename, crop, fieldpath, expSystem_flag = result
    missingRec = ""

    print(f"Simulation {simulation_name} finished with return code {returncode}")

    if returncode == 0:
        # Check for missing files and NaNs
        file_exts = ["g01", "G03", "G04", "G05", "G07"]
        for ext in file_exts:
            g_name2 = os.path.join(fieldpath, f"{sitename}.{ext}")
            table_name = ext.lower() + "_" + crop

            if not os.path.exists(g_name2):
                missingRec += f"Missing file: {g_name2}<br>"
                print(f"File not found: {g_name2}")
                continue

            missingRec += checkNaNInOutputFile(table_name, g_name2)

        if crop != "fallow":
            missingRec += checkNaNInOutputFile("plantStress_" + crop, os.path.join(fieldpath, "plantstress.crp"))
            if crop in ("potato", "soybean"):
                missingRec += checkNaNInOutputFile("nitrogen_" + crop, os.path.join(fieldpath, "nitrogen.crp"))

        if missingRec:
            delete_pastrunsDB(str(simulation_name[0]), crop) # Assuming simulation_name is [ID]
            simStatus.setText(f"<b>Simulation finished, but some output is invalid or incomplete.</b><br>{missingRec}")
        else:
            simStatus.setText("<b>Ingesting output files into the database.</b>")
            simStatus.repaint()

            for ext in file_exts:
                g_name2 = os.path.join(fieldpath, f"{sitename}.{ext}")
                table_name = ext.lower() + "_" + crop
                if ext.lower() == "g03":
                    ingestGeometryFile(os.path.join(fieldpath, f"{sitename}.grd"), g_name2, str(simulation_name[0]))
                ingestOutputFile(table_name, g_name2, str(simulation_name[0]))

            ingestOutputFile("plantStress_" + crop, os.path.join(fieldpath, "plantstress.crp"), str(simulation_name[0]))
            if crop in ("potato", "soybean"):
                ingestOutputFile("nitrogen_" + crop, os.path.join(fieldpath, "nitrogen.crp"), str(simulation_name[0]))

            simStatus.setText(f"<b>Simulation {simulation_name[0]} completed successfully.</b>")
    else:
        simStatus.setText(f"Simulation {simulation_name[0]} failed with code {returncode}.")


    controller.increment_completed_count() # Notify the controller

    # Remove the finished worker from the active list
    for i, worker in enumerate(widget_instanceES.activeSimWorkers):
        if worker.simulation_id == simulation_name:
            worker.quit()
            worker.wait() # Ensure thread truly finishes
            del widget_instanceES.activeSimWorkers[i]
            break

       