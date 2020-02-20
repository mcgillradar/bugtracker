# <img alt="Bugtracker" src="bugtracker_logo.png" height="60">

Bugtracker is a Python 3 package, as well as a set of command-line applications, which collectively provide a software suite for analyzing biological echoes from radar data.

For the moment, Bugtracker only supports Linux systems.

We provide support for the following Radar filetypes:
* IRIS (old Environment Canada format)
* ODIM_H5 (new Environment Canada format)
* NEXRAD (US Weather Service radar format)

## Installation procedures

1. Clone the repository to a local folder

```sh
git clone https://github.com/mcgillradar/bugtracker.git
```

2. Install the system-level dependency wget. Install it through your system package manager (i.e. 'sudo apt-get install wget' or 'sudo yum install wget')

3. As bugtracker is not yet publicly available on the PyPI package index, you will need to build the package from sources.

Run the following script in the top level of the repository.
```sh
./update.sh
```

4. Verify that the package is installed by running 'pip list'

5. Create the configuration file. The application expects a configuration file called 'bugtracker.json' to be present in the /bugtracker/apps folder. There is a sample file in /examples/bugtracker .
This will need to be copied to /bugtracker/apps.

This configuration file allows you to adjust some of the algorithm parameters and the location of the data input sources and outputs. Ensure that the folders specified map to directories that exist on your local machine.

6. Run unit tests on bugtracker package (optional)

Navigate to the /tests directory and run the following command:

```sh
pytest
```

## Overview of the apps

There are currently 4 command-line applications. To get help for each application, run the application with the '-h' flag. For example:

```sh
python3 nexrad_aws.py -h
```

1. nexrad_aws.py
	This application allows automated downloading of NEXRAD data from the Amazon Web Services servers provided by the US Weather Service.
2. calib.py
	This calibration application must be run prior to the processing. This generates a calibration file which is specific to each radar. This must be run prior to the main tracker.py application.
3. tracker.py
	This is the main data processing application. It takes as input raw data files, and outputs NETCDF4 containing the filtered bug data.
4. animate.py
	This application creates a series of .avi animations. This must be run after tracker.py, as it uses the output images created by it.

## Quick Start Guide

A quick way to get started would be the following:

```sh
cd /your/local/path/bugtracker/apps

# download 3 days worth of NEXRAD files for testing
python3 nexrad_aws.py 20190728 20190730 kcbw

# create calibration file (by default will run over a 6 hour period)
python3 calib.py 201907280300 nexrad kcbw

# run processing algorithm (by default will only do one timestamp, but can be extended)
python3 tracker.py 201907300300 nexrad kcbw
```


## Design Philosophy

Makes heavy use of object-oriented programming in Python.

    Reusable components, inheritance Processor -> IrisProcessor For calibration, Controller -> IrisController Filter -> ClutterFilter, PrecipFilter
    metadata, grid_info These objects crop up throughout the code.
