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
    final_grid = bugtracker.calib.calib.Grid()
    coords = bugtracker.core.utils.latlon(grid_info, metadata)

    final_grid.lats = coords['lats']
    final_grid.lons = coords['lons']
    final_grid.altitude = altitude_grid

    return final_grid



def run_calib(args, metadata, grid_info, calib_grid):

    config = bugtracker.config.load("./bugtracker.json")

    calib_controller = bugtracker.calib.calib.IrisController(metadata, grid_info)
    calib_controller.set_grids(calib_grid)

    time_start = datetime.datetime.strptime(args.timestamp, "%Y%m%d%H%M")
    data_mins = args.data_hours * 60

    print("Time start:", time_start.strftime("%Y%m%d%H%M"))
    print("Data mins:", data_mins)

    # Let's get a list of 
    iris_dir = os.path.join(config['archive_dir'], args.station)
    print(iris_dir)
    iris_collection = bugtracker.io.iris.IrisCollection(iris_dir, args.station)
    calib_sets = iris_collection.time_range(time_start, data_mins)

    for data_set in calib_sets:
        print(data_set.datetime)

    calib_controller.set_calib_data(calib_sets)
    calib_controller.process_convol()
    calib_controller.process_dopvol()

    calib_controller.save()
    calib_controller.save_masks()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("station", help="3 letter station code")
    parser.add_argument("-dt", "--data_hours", type=int, default=6)
    parser.add_argument('-d', '--debug', action='store_true', help="Debug plotting")
    parser.add_argument('-c', '--clear', action='store_true', help="Clear cache")
    # Reset

    args = parser.parse_args()

    cache_manager = bugtracker.core.cache.CacheManager()

    if args.clear:
        print("Clearing cache")
        cache_manager.reset()

    cache_manager.make_folders()

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()
    calib_grid = get_srtm(metadata, grid_info)

    run_calib(args, metadata, grid_info, calib_grid)


main()
