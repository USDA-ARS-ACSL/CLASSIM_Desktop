# CLASSIM
*Currently Release 2.4.0.3*

Interface program for our crop models
This is the interface for our crop models. it is written in Python, version 10.0.8 and utilizes QT for the interface
We use Anaconda Python
use the yml file to create the environment. 
Conda env create -f classim22.yml -p /your/path/here

The interface requires a database for input (crop.db) and output (cropoutput.db) as well as the crop models
The databases are in the database folder. The models are in the CLASSIMDirectoryStructure.zip file

You must create a folder called Classim in your documents folder. Copy the databases from databases.zip and 
all the files in the CLASSIMDIrectoryStructure.zip file to this folder

open a command window in the environment created above. Run the model as --  Python Classim.py

## this folder contains the python source code for classim
   We used anaconda python for the distribution
   Visual Studio Professional for the development 
   Windows 11 is the OS
   
# Environment:
   use classim22.yml to create the environment
   conda env create -f classim22.yml
   or
   conda env create --name classim22 -f classim22.yml

# Running the interface
  if using a development too, you can start it inside the tool
   from the command line, navigate to the folder that contains classim.py
   and type python classim.py
   make sure you have activated the classim22 environment:
   conda activate classim22
   create a folder called 'Classim' in your default documents folder
   create a folder called 'run' inside the classim folder
   Copy all the exectuables and databases listed below to your classim folder
   

# databases and executables
  classim uses two databases crop.db and cropOutput.db
  both are sqlite and  are serverless
  by default, classim uses the documents folder  under the username. if the user has a onedrive documents
  folder, classim will find this.
  Create a folder called classim under your documents folder and copy the databases to it
  also copy the executables:
   2dmaizsim.exe
   maizsim.dll
   2dglycim.exe
   glycim.dll
   glycim_GasEx.dll
   2dgossym.exe
   gossym.dll
   gossym_Gas_ex.dll
   2dspudsim.exe
   spudsim2-1.dll
   gridgen.dll
   Rosetta.exe
   CreateSoilFiles.exe
   
  These executables and databases will be in the release location in GitHub
  

 Classim uses a run folder to hold input and output from each of the runs
 
 There is an SQL folder that contains some helper sql files. 
 cropOutputDB.sql will recreate an empty cropoutput databases
 Delete and recreate pastruns table will clear the past runs and reset the counter to 0
 when the past runs and cropoutput db's are reset, you must clear all the numbered folders
 from the run folder 