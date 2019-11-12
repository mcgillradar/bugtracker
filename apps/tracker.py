"""
This file is part of Bugtracker
Copyright (C) 2019  McGill Radar Group

Bugtracker is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Bugtracker is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Bugtracker.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import glob
import argparse
import datetime
import time

# To avoid spamming console every time the utility is run.
from contextlib import contextmanager

import numpy as np

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


def test_radial_plot(bug_dbz, grid_info, metadata, output_folder, max_range):
    azims = grid_info.azims
    gates = grid_info.gates
    dims = (azims, gates)

    ranges = np.zeros(dims, dtype=float)
    azimuths = np.zeros(dims, dtype=float)
    elevations = np.zeros(1, dtype=float)

    for x in range(0,azims):
        azimuths[x,:] = (grid_info.azim_step) * x

    for y in range(0, gates):
        # rescaling to meters from kilometers
        ranges[:,y] = (grid_info.gate_step / 1000.0) * y

    x_arr, y_arr, z_arr = pyart.core.antenna_to_cartesian(ranges, azimuths, elevations)

    lon_0 = metadata.lon
    lat_0 = metadata.lat

    lons, lats = pyart.core.cartesian_to_geographic_aeqd(x_arr, y_arr, lon_0, lat_0)

    plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, output_folder)
    plot_time = metadata.scan_dt
    plotter.set_data(bug_dbz, "dbz", plot_time, metadata, max_range)
    plotter.save_plot()



def iris_plot(filename, scan_dt, output_folder, args):

    radar = pyart.io.read_sigmet(filename)
    bugtracker.plots.simple.debug_plot(scan_dt, radar, output_folder, args)



def bug_filter(iris_set):
    pass


def plot_one_set(iris_set, output_folder, args):

    iris_plot(iris_set.convol, iris_set.datetime, output_folder, args)
    iris_plot(iris_set.dopvol_1A, iris_set.datetime, output_folder, args)
    iris_plot(iris_set.dopvol_1B, iris_set.datetime, output_folder, args)
    iris_plot(iris_set.dopvol_1C, iris_set.datetime, output_folder, args)
    iris_plot(iris_set.dopvol_2,  iris_set.datetime, output_folder, args)
    bug_filter(iris_set)


def check_args(args):

    valid_stations = ['xam', 'wgj']

    if args.station.lower() not in valid_stations:
        raise ValueError(f"Invalid station {args.station}")


def main():

    config = bugtracker.config.load("./bugtracker.json")

    # First step "minimal", create a batch from command-line inputs
    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("station", help="3 letter station code")
    parser.add_argument("-r", "--range", default=100, type=int, help="Maximum range (km)")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug plotting")

    args = parser.parse_args()
    check_args(args)

    station_code = args.station.lower()
    archive_dir = config['archive_dir']
    iris_current_dir = os.path.join(archive_dir, station_code)
    if not os.path.isdir(iris_current_dir):
        raise FileNotFoundError(iris_current_dir)

    iris_coll = bugtracker.io.iris.IrisCollection(iris_current_dir, args.station)
    iris_coll.check_sets()


    pattern = "%Y%m%d%H%M"
    search_datetime = datetime.datetime.strptime(args.timestamp, pattern)
    closest_set = iris_coll.closest_set(search_datetime)
    datestamp = closest_set.datetime.strftime(pattern)

    print("Closest time:", datestamp)
    print("Max plot range:", args.range)

    output_folder = os.path.join(config['plot_dir'], station_code, datestamp)
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    if args.debug:
        plot_one_set(closest_set, output_folder, args)

    iris_data = bugtracker.core.iris.IrisData(closest_set)
    iris_data.print_sizes()
    print("Filling grids")
    t0 = time.time()
    iris_data.fill_grids()
    t1 = time.time()


    if args.debug:
        iris_data.plot_all_levels(output_folder, args.range)


    calib_data = None

    processor = bugtracker.core.iris.IrisProcessor(iris_data, calib_data, output_folder)
    bug_dbz = processor.execute()



    processor.plot(bug_dbz, args.range)

    max_range = 150
    test_radial_plot(bug_dbz, iris_data.grid, iris_data.metadata, output_folder, max_range)

    metadata = bugtracker.core.metadata.from_iris_set(closest_set)
    radar_grid = iris_data.grid
    bugtracker.io.output.save_netcdf(radar_grid, metadata, bug_dbz, output_folder)


main()