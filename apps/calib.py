
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



def run_calib(metadata, grid_info, calib_grid):

    calib_controller = bugtracker.calib.calib.Controller(metadata, grid_info)
    calib_controller.set_grids(calib_grid)
    calib_controller.create_masks()
    calib_controller.save()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("station", help="3 letter station code")
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

    run_calib(metadata, grid_info, calib_grid)


main()
