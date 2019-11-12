# Bugtracker

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


conda activate bugtracker

Now there are two command-line utilities.

calib.py <-- calibration step
tracker.py <-- main application

Configure bugtracker.json


## Developer Guide

Explain a bit more in detail the architecture of the application.


import bugtracker


pyart
geopy
numpy
cartopy

