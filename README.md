# <img alt="Bugtracker" src="bugtracker_logo.png" height="60">

What is this application?

## Installation procedures

This program was written for Linux systems. This application is completely untested on Windows/MacOS.

Requirements:
* Miniconda3 (Python 3.6+)

Steps:
1. Create a 'spruce' user *without* root permissions using useradd.
2. Create a \~/repos directory
3. Clone the spruce-budworm repository
4. Create a 'bugtracker' environment using miniconda (conda env create ...)
5. Activate the bugtracker environment
6. Run the ./update.sh script in the top level of the repo. It will install bugtracker. If it complains about missing dependencies, install the dependencies using conda and re-run the ./update.sh script.

Bugtracker is now installed!

Optional but important step:
7. Change directory to tests, and run "pytest -m" to confirm that everything works correctly. This will run all of the unit tests for the application.


## Quick Start Guide

Bugtracker depends also on one external utility
1. wget


Both can be installed using your linux package manager.


conda activate bugtracker

Now there are two command-line utilities.

calib.py <-- calibration step
tracker.py <-- main application

Configure bugtracker.json


## Developer Guide

Bugtracker is a python project which tracks the migration of insects using input radar data. It works by filtering out non-meterological radar echoes.

We provide support for the following Radar filetypes:
* IRIS (old Environment Canada format)
* ODIM_H5 (new Environment Canada format)
* NEXRAD (US Weather Service radar format)


Bugtracker provides a suite of command-line applications for analyzing radar data:

1. nexrad_aws.py
	This application allows automated downloading of NEXRAD data from the Amazon Web Services servers provided by the US Weather Service.
2. calib.py
	This calibration application must be run prior to the processing. This generates a calibration file which is specific to each radar.
3. tracker.py
	This is the main data processing application. It takes as input raw data files, and outputs NETCDF4 containing the filtered bug data.


## Design philosophy

Makes heavy use of object-oriented programming in Python.

1. Reusable components, inheritance
	Processor -> IrisProcessor
	For calibration, Controller -> IrisController
	Filter -> ClutterFilter, PrecipFilter
2. metadata, grid_info
	These objects crop up throughout the code.





Depenedencies: Python packages and 1 system package
* wget