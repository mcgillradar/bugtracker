# <img alt="Bugtracker" src="bugtracker_logo.png" height="60">

Bugtracker is a Python 3 package, as well as a set of command-line applications, which collectively provide a software suite for analyzing biological echoes from radar data.

This README contains the installation instructions and a quick start guide. A more in-depth user manual can be found in [MANUAL.md](https://github.com/mcgillradar/bugtracker/blob/master/MANUAL.md)

As of v1.5.0, Bugtracker is supported for the following operating systems:
* Linux (CentOS 7, RHEL 7, Ubuntu, Fedora)
* Windows 10

We provide support for the following Radar filetypes:
* IRIS (old Environment Canada format)
* ODIM_H5 (new Environment Canada format)
* NEXRAD (US Weather Service radar format)

## Installation (Windows)

1. Clone the repository to a local folder

```sh
git clone https://github.com/mcgillradar/bugtracker.git
```

2. Install [miniconda3](https://docs.conda.io/en/latest/miniconda.html)
Select the version marked "Python3.7 Miniconda3 Windows 64-bit" and run the installer.

3. Run the miniconda3 command line, and change directory into the bugtracker repository folder. Run the following commands to create and activate the environment:

```sh
conda env create --name bugtracker --file=environment_windows.yml
conda activate bugtracker
```

4. Build the application by running the following script

```sh
python rebuild.py
```

5. Generate the configuration file using the following:
```sh
python generate_config.py
```

This command will prompt the user for a root directory to save application data.

6. Run unit tests (optional)
```sh
cd tests
pytest
```

## Installation (Linux)

1. Clone the repository to a local folder

```sh
git clone https://github.com/mcgillradar/bugtracker.git
```

2. Install [miniconda3](https://docs.conda.io/en/latest/miniconda.html)
Select the version marked "Python3.7 Miniconda3 Linux 64-bit" and run the installer.

3. Open a terminal, and change directory into the bugtracker repository folder. Run the following commands to create and activate the environment:

```sh
conda env create --name bugtracker --file=environment_linux.yml
conda activate bugtracker
```

4. Build the application by running the following script

```sh
python rebuild.py
```

5. Generate the configuration file using the following:
```sh
python generate_config.py
```

This command will prompt the user for a root directory to save application data.

6. Run unit tests (optional)
```sh
cd tests
pytest
```

## Updating

These instructions work for both Linux and Windows.

1. Get the latest version of Bugtracker by running the following command inside the repository:

```sh
git pull
```

2. Run the rebuild script again

```sh
python rebuild.py
```

## Overview of the apps

Apps are run from within the /apps folder.

There are currently 4 command-line applications. To get help for each application, run the application with the '-h' flag. For example:

```sh
python nexrad_aws.py -h
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
python nexrad_aws.py 20190728 20190730 kcbw

# create calibration file (by default will run over a 6 hour period)
python calib.py 201907280300 nexrad kcbw

# run processing algorithm (by default will only do one timestamp, but can be extended)
python tracker.py 201907300300 nexrad kcbw
```
