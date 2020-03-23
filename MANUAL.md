# Bugtracker Manual

## Miniconda

Miniconda3 is the distribution of Python 3 that was chosen for this application. It was chosen for two reasons:

1. Cross-platform development (runs the same on Windows and Linux)
2. Ease of deployment

Although the steps in the [README.md](https://github.com/mcgillradar/bugtracker/blob/master/README.md) describe how to set up the Bugtracker conda environment, I highly recommend checking out the miniconda [manual](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html). It describes in detail a lot of edge cases (how to delete environments, create new ones, install new packages, etc.)


## NETCDF System library (optional)

The application itself uses the python netcdf4 module to process radar data inputs and outputs. However, I would recommend installing the system NETCDF library as well, for the the simple reason that it provides access to the 'ncdump' command line tool.


### Installation

Steps for Fedora/RHEL/CentOS

```sh
sudo dnf install netcdf
```

Steps for Ubuntu:

```sh
sudo apt-get install netcdf-bin
```

Steps for [installing NETCDF on Windows 10](https://www.unidata.ucar.edu/software/netcdf/docs/winbin.html). 

### Using ncdump

**ncdump** is a command-line utility that allows you to quickly view the contents of netCDF4 files. This is particularily useful for this application, as the output of the calibration procedure is a netCDF4 file, as well as the output of the main data routine.

To view just the file metadata:

```sh
ncdump -h your_netcdf_file.nc
```
In order to view the output of a particular variable:

```sh
ncdump -v varname your_netcdf_file.nc
```

This utility provides a quick and easy way to look at the file contents without having to write more code.


## Calibration tips

The calibration utility 'calib.py' must be run once per radar. The calibration code accomplishes two tasks:

1. Generates the lat/lon grid in radial coordinates.
2. Creates a 'clutter filter' that masks out ground clutter.

For the clutter filter, there are two input parameters that can be adjusted in the bugtracker.json file:

1. dbz_threshold
2. coverage_threshold

The default values are 10.0 dBZ and 0.30, which means that over the period of the calibration (which is by default 6 hours), if a particular pixel has reflectivity greater than 10.0 dBZ for more than 30% of the time, we consider this a 'clutter pixel'. These values can be adjusted.

Note that we **highly** recommend running the calibration for at least 12 hours during a period of time where there is zero precipitation.


## Encountering Errors

I have tried to make the error messages in this application as descriptive as possible, so the first step would be to look at the error message and see if it's something that can easily be fixed. A few things to check:

* Is there a missing folder / incorrect path name?
* Does the error specify a missing Python 3 module? In this case, missing modules can be installed using 'conda install packagename'

In the event of an error that doesn't have a clear solution, please paste the stack trace and error message into a new issue in the [issue tracker](https://github.com/mcgillradar/bugtracker/issues), so the application developers can look into it.


## Developer Guide

We welcome pull requests and contributions to this project. In this section, I will explain the general philosphy behind the development, so the codebase is more clear, and to give a better idea of how to extend the code.

This program makes heavy use of object-oriented programming in Python. Since the application needed to support IRIS, NEXRAD and ODIM_H5 files, I make use of inheritance to allow for resusable code.

So there is a pattern that you will see repeated throughout the codebase where there is a **base class** that corresponds to a generic data structure, and then each of the IRIS/NEXRAD/ODIM_H5 have a **child class** that inherits properties from the base class.

Here are a few important examples:

1. ScanData -> IrisData, NexradData, OdimData
	* This class contains the data from a particular scan.
2. Controller -> IrisController, NexradController, OdimController
	* This class controls the calibration code for creating the calibration netCDF4 file via the 'calib.py' application.
3. Processor -> IrisProcessor, NexradProcessor, OdimProcessor
	* This is the main data processor that generates the output files as well as output plots.
4. Filter -> ClutterFilter, PrecipFilter
	* A big component of the application is filtering out non-biological echoes. In order to facilitate code reuse, each of these filters inherits from the base Filter class.

Another important note: Although the application uses the Radar class taken from the [pyart](https://arm-doe.github.io/pyart/API/generated/pyart.core.Radar.html#pyart.core.Radar) project, we use two classes to keep track of important infromation about a specific radar:

1. **Metadata**
2. **GridInfo**

These classes are ubiquitous throughout the application, so if you are going to develop or extend Bugtracker, I highly recommend checking out these two files, as they are a base for much of the application:

1. bugtracker/core/metadata.py
2. bugtracker/core/grid.py

A common design pattern throughout this application is, instead of passing around dozens of parameters, we put all the information in a Metadata object and a GridInfo object, and pass it around instead.
