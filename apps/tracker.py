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


def check_args(args):
    """
    Performing validation on the command-line arguments
    provided by argparse
    """

    valid_stations = ['xam', 'wgj', 'kcbw']

    if args.station.lower() not in valid_stations:
        raise ValueError(f"Invalid station {args.station}")

    valid_dtypes = ['iris', 'nexrad', 'odim']

    if args.dtype.lower() not in valid_dtypes:
        msg = f"Unsupported dtype {args.dtype}\n"
        msg += f"Supported types are {valid_dtypes}\n"
        raise ValueError(msg)


def get_closest_set(args, config):
    """
    Returns an IrisSet object that we wish to analyze, which
    is closest to the specified datetime.
    """

    station_code = args.station.lower()
    archive_dir = config['input_dirs']['iris']
    iris_current_dir = os.path.join(archive_dir, station_code)
    if not os.path.isdir(iris_current_dir):
        raise FileNotFoundError(iris_current_dir)

    iris_coll = bugtracker.io.iris.IrisCollection(iris_current_dir, args.station)
    iris_coll.check_sets()

    pattern = "%Y%m%d%H%M"
    search_datetime = datetime.datetime.strptime(args.start, pattern)
    closest_set = iris_coll.closest_set(search_datetime)

    if closest_set is None:
        raise ValueError("Closest set not found")

    datestamp = closest_set.datetime.strftime(pattern)
    print("Closest time:", datestamp)
    return closest_set


def iris_tracker(args, config):

    iris_set_list = []

    # If time is 0, that means get only the closest
    if args.data_hours == 0:
        closest_set = get_closest_set(args, config)
        iris_set_list.append(closest_set)
    else:
        time_start = datetime.datetime.strptime(args.start, "%Y%m%d%H%M")
        data_mins = args.data_hours * 60
        iris_dir = os.path.join(config['input_dirs']['iris'], args.station)
        iris_collection = bugtracker.io.iris.IrisCollection(iris_dir, args.station)
        iris_set_list = iris_collection.time_range(time_start, data_mins)

    first_set = iris_set_list[0]
    metadata = bugtracker.core.metadata.from_iris_set(first_set)
    grid_info = bugtracker.core.iris.iris_grid()
    print("metadata:", metadata)
    print("grid_info:", grid_info)

    processor = bugtracker.io.processor.IrisProcessor(metadata, grid_info)
    processor.process_sets(iris_set_list)


def nexrad_tracker(args, config):

    date_format = "%Y%m%d%H%M"

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.start, date_format)
    end_time = start_time + datetime.timedelta(hours=args.data_hours)

    # Initializing manager class
    manager = bugtracker.io.nexrad.NexradManager(config, station_id)
    manager.populate(start_time)

    """
    The NEXRAD manager uses a list of files, rather than the IrisSet
    that is required for IRIS files. This is because it has a much simpler
    file structure (1 file per scan)
    """
    nexrad_files = []

    if args.data_hours == 0:
        closest_file = manager.get_closest(start_time)
        nexrad_files.append(closest_file)
    else:
        nexrad_files = manager.get_range(start_time, end_time)

    processor = bugtracker.io.processor.NexradProcessor(manager.metadata, manager.grid_info)
    processor.process_sets(nexrad_files)


def odim_tracker(args, config):

    raise NotImplementedError(args.dtype)


def main():

    t0 = time.time()

    config = bugtracker.config.load("./bugtracker.json")

    # First step "minimal", create a batch from command-line inputs
    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("dtype", help="Data type (either iris, nexrad, or odim)")
    parser.add_argument("station", help="3 letter station code")
    parser.add_argument("-dt", "--data_hours", type=int, default=0)
    parser.add_argument("-r", "--range", default=100, type=int, help="Maximum range (km)")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug plotting")

    args = parser.parse_args()
    check_args(args)

    dtype = args.dtype.lower()

    if dtype == 'iris':
        iris_tracker(args, config)
    elif dtype == 'nexrad':
        nexrad_tracker(args, config)
    elif dtype == 'odim':
        odim_tracker(args, config)
    else:
        # Unreachable code, given the previous check_args()
        raise ValueError(f"Invalid dtype {dtype}")


main()