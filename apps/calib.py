"""
Bugtracker - A radar utility for tracking insects
Copyright (C) 2020 Frederic Fabry, Daniel Hogg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
There is a combined grid, which for IRIS is of dimension
(720, 512).

On this grid, we need to have:
*) Altitude
*) Latitude
*) Longitude
*) Geometry mask
*) Clutter mask
"""

import os
import sys
import math
import datetime
import argparse
from contextlib import contextmanager

import numpy as np
import netCDF4 as nc

@contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        valid_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = valid_stdout

with suppress_stdout():
    import pyart

import bugtracker


def get_srtm(metadata, grid_info):
    """
    This function calls the SRTM3Reader and the Downloader.
    The Reader is responsible for IO for SRTM3 files, and the Downloader
    is responsible for figuring out which files (if any) need to be
    downloaded from US Government servers.
    """

    # For the moment, I have commented out the altitude code, because
    # we are not actually using the elevation, and I am getting some
    # bugs from the SRTM extraction code.

    """
    reader = bugtracker.calib.elevation.SRTM3Reader(metadata, grid_info)

    reader.get_active_cells()
    active_keys = reader.get_active_keys()
    print(active_keys)

    downloader = bugtracker.calib.srtm3_download.Downloader(active_keys)
    downloader.set_missing_cells()
    num_to_download = len(downloader.missing)

    if num_to_download > 0:
        print("Number of files to download:", num_to_download)
        downloader.self_test()
        downloader.set_missing_cells()
        downloader.download()
        downloader.extract()
        downloader.final_check()
    else:
        print("All SRTM3 files already downloaded, skipping.")


    altitude_grid = reader.load_elevation()
    """

    final_grid = bugtracker.calib.calib.Grid()
    coords = bugtracker.core.utils.latlon(grid_info, metadata)

    final_grid.lats = coords['lats']
    final_grid.lons = coords['lons']

    grid_dims = final_grid.lons.shape
    final_grid.altitude = np.zeros(grid_dims, dtype=float)

    return final_grid


def plot_calib_graph(args, metadata, radial_plotter, plot_type, angle, data):
    time_start = datetime.datetime.strptime(args.timestamp, "%Y%m%d%H%M")
    label = f"clutter_{plot_type}_{angle}_"
    max_range = 150
    print("Plot label:", label)
    print("data", data)

    radial_plotter.set_data(data, label, time_start, metadata, max_range)
    radial_plotter.save_plot(min_value=0, max_value=1)


def plot_calib_iris(args, config):

    iris_dir = os.path.join(config['input_dirs']['iris'], args.station)
    iris_collection = bugtracker.io.iris.IrisCollection(iris_dir, args.station)
    if len(iris_collection.sets) == 0:
        raise ValueError("Invalid length")

    metadata = bugtracker.core.metadata.from_iris_set(iris_collection.sets[0])
    grid_info = bugtracker.io.iris.iris_grid()

    nc_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)

    plot_dir = config['plot_dir']
    plot_subdir = os.path.join(plot_dir, "calib_plots")

    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)

    if not os.path.isdir(plot_subdir):
        os.mkdir(plot_subdir)

    dset = nc.Dataset(nc_file, mode='r')

    convol_clutter = dset.variables['convol_clutter'][:,:,:]
    dopvol_clutter = dset.variables['dopvol_clutter'][:,:,:]

    convol_angles = dset.variables['convol_angles']
    dopvol_angles = dset.variables['dopvol_angles']

    lats = dset.variables['lats'][:,:]
    lons = dset.variables['lons'][:,:]

    radial_plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, plot_subdir, grid_info)

    print("Plotting convol")
    for x in range(0, len(convol_angles)):
        angle = convol_angles[x]
        slice_data = convol_clutter[x,:,:]
        plot_calib_graph(args, metadata, radial_plotter, "convol", angle, slice_data)

    print("Plotting dopvol")
    for x in range(0, len(dopvol_angles)):
        angle = dopvol_angles[x]
        slice_data = dopvol_clutter[x,:,:]
        plot_calib_graph(args, metadata, radial_plotter, "dopvol", angle, slice_data)

    dset.close()


def plot_calib_nexrad(args, config):
    date_format = "%Y%m%d%H%M"

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.timestamp, date_format)

    # Initializing manager class
    manager = bugtracker.io.nexrad.NexradManager(config, station_id)
    manager.populate(start_time)

    metadata = manager.metadata
    grid_info = manager.grid_info

    nc_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)

    plot_dir = config['plot_dir']
    plot_subdir = os.path.join(plot_dir, "calib_plots")

    if not os.path.isdir(plot_dir):
        os.mkdir(plot_dir)

    if not os.path.isdir(plot_subdir):
        os.mkdir(plot_subdir)

    dset = nc.Dataset(nc_file, mode='r')

    clutter = dset.variables['clutter'][:,:,:]
    clutter_angles = dset.variables['angles']

    lats = dset.variables['lats'][:,:]
    lons = dset.variables['lons'][:,:]

    radial_plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, plot_subdir, grid_info)

    print("Plotting clutter")
    for x in range(0, len(clutter_angles)):
        angle = clutter_angles[x]
        slice_data = clutter[x,:,:]
        plot_calib_graph(args, metadata, radial_plotter, "nexrad", angle, slice_data)

    dset.close()

def plot_calib_odim(args, config):

    raise NotImplementedError("Odim plotting not implemented")

def plot_calib_graphs(args, config):
    """
    Plot output graphs
    """
    dtype = args.dtype.lower()

    if dtype == 'iris':
        plot_calib_iris(args, config)
    elif dtype == 'nexrad':
        plot_calib_nexrad(args, config)
    elif dtype == 'odim':
        plot_calib_odim(args, config)
    else:
        raise ValueError(f"Invalid dtype {dtype}")

  
def run_iris_calib(args, config):

    iris_dir = os.path.join(config['input_dirs']['iris'], args.station)
    iris_collection = bugtracker.io.iris.IrisCollection(iris_dir, args.station)
    if len(iris_collection.sets) == 0:
        raise ValueError("Invalid length")

    metadata = bugtracker.core.metadata.from_iris_set(iris_collection.sets[0])
    grid_info = bugtracker.io.iris.iris_grid()

    calib_grid = get_srtm(metadata, grid_info)

    calib_controller = bugtracker.calib.calib.IrisController(args, metadata, grid_info)
    calib_controller.set_grids(calib_grid)

    time_start = datetime.datetime.strptime(args.timestamp, "%Y%m%d%H%M")
    data_mins = args.data_hours * 60

    print("Time start:", time_start.strftime("%Y%m%d%H%M"))
    print("Data mins:", data_mins)

    # Let's get a list of 
    iris_dir = os.path.join(config['input_dirs']['iris'], args.station)
    print(iris_dir)

    calib_sets = iris_collection.time_range(time_start, data_mins)

    for data_set in calib_sets:
        print("Calib set:", data_set.datetime)

    threshold = config['clutter']['coverage_threshold']

    calib_controller.set_calib_data(calib_sets)
    calib_controller.create_masks(threshold)
    calib_controller.print_masks()
    calib_controller.save()
    calib_controller.save_masks()


def run_nexrad_calib(args, config):

    date_format = "%Y%m%d%H%M"

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.timestamp, date_format)
    end_time = start_time + datetime.timedelta(hours=args.data_hours)

    start_string = start_time.strftime(date_format)
    end_string = end_time.strftime(date_format)
    print(f"NEXRAD calibration time range {start_string}-{end_string}")

    # Initializing manager class
    manager = bugtracker.io.nexrad.NexradManager(config, station_id)
    manager.populate(start_time)

    calib_grid = get_srtm(manager.metadata, manager.grid_info)

    calib_files = manager.get_range(start_time, end_time)

    for calib_file in calib_files:
        if not os.path.isfile(calib_file):
            raise FileNotFoundError(calib_file)

    threshold = config['clutter']['coverage_threshold']

    calib_controller = bugtracker.calib.calib.NexradController(args, manager)
    calib_controller.set_grids(calib_grid)
    calib_controller.set_calib_data(calib_files)
    calib_controller.create_masks(threshold)
    calib_controller.save()
    calib_controller.save_masks()


def run_odim_calib(args, config):

    date_format = "%Y%m%d%H%M"

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.timestamp, date_format)
    end_time = start_time + datetime.timedelta(hours=args.data_hours)

    start_string = start_time.strftime(date_format)
    end_string = end_time.strftime(date_format)
    print(f"ODIM calibration time range {start_string}-{end_string}")

    # Initializing manager class
    manager = bugtracker.io.odim.OdimManager(config, station_id)
    manager.populate(start_time)

    calib_grid = get_srtm(manager.metadata, manager.grid_info)

    calib_files = manager.get_range(start_time, end_time)

    for calib_file in calib_files:
        if not os.path.isfile(calib_file):
            raise FileNotFoundError(calib_file)

    threshold = config['clutter']['coverage_threshold']

    calib_controller = bugtracker.calib.calib.OdimController(args, manager)
    calib_controller.set_grids(calib_grid)
    calib_controller.set_calib_data(calib_files)
    calib_controller.create_masks(threshold)
    calib_controller.save()
    calib_controller.save_masks()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("dtype", help="Data type (either iris, nexrad, or odim)")
    parser.add_argument("station", help="Station code")
    parser.add_argument("-dt", "--data_hours", type=int, default=6)
    parser.add_argument('-d', '--debug', action='store_true', help="Debug plotting")
    parser.add_argument('-c', '--clear', action='store_true', help="Clear cache")
    parser.add_argument('-p', '--plot', action='store_true', help="Plot diagnostic graphs")
    # Reset

    args = parser.parse_args()
    dtype = args.dtype.lower()

    cache_manager = bugtracker.core.cache.CacheManager()

    if args.clear:
        print("Clearing cache")
        cache_manager.reset()

    cache_manager.make_folders()
    config = bugtracker.config.load("./bugtracker.json")


    if args.plot:
        plot_calib_graphs(args, config)
    else:
        if dtype == 'iris':
            run_iris_calib(args, config)
        elif dtype == 'nexrad':
            run_nexrad_calib(args, config)
        elif dtype == 'odim':
            run_odim_calib(args, config)
        else:
            raise ValueError(f"Invalid dtype {dtype}")


main()
