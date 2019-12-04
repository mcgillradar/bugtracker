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
MODULE DESCRIPTION

This module provides test data of various types (auto-generated
dbz grids, Metadata, GridInfo, ...)

The utility of this module is primarily for development and unit
testing. Production software should *NOT* be using these test
functions.
"""

import os
import datetime

import numpy as np

import bugtracker


def sin_dbz(grid_info):
    """
    Creates a radially sinusoidal pattern for dBZ
    """

    dims = (grid_info.azims, grid_info.gates)
    dbz_array = np.zeros(dims, dtype=float)

    min_range = 0
    max_range = (grid_info.gates - 1) * grid_info.gate_step

    distances = np.linspace(min_range, max_range, num=grid_info.gates)
    print("Distances:", distances)

    scale_factor = 20000
    scaled_distances = distances / scale_factor
    dbz_scale = 30.0
    sin_values = np.sin(scaled_distances) * dbz_scale

    for x in range(0, grid_info.azims):
        dbz_array[x,:] = sin_values

    return dbz_array



def metadata():
    test_lat = 44.45
    test_lon = -110.081
    now = datetime.datetime.utcnow()
    metadata = bugtracker.core.metadata.Metadata('test', now, test_lat, test_lon, 'test_radar')
    return metadata


def grid_info():

    azims = 720
    gates = 512
    gate_step = 500.0
    azim_step = 0.5
    grid = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step)
    return grid



def iris_set(config):
    """
    Return sample IrisSet from some XAM radar set
    """

    radar_id = "xam"
    archive_dir = config['archive_dir']
    radar_dir = os.path.join(archive_dir, radar_id)
    iris_collection = bugtracker.io.iris.IrisCollection(radar_dir, radar_id)

    sample_datetime = datetime.datetime(2013, 7, 17, 19, 50, 0)
    sample_set = iris_collection.closest_set(sample_datetime)

    if sample_set is None:
        raise ValueError("Cannot find sample IrisSet")

    return sample_set


def iris_set_wgj(config):
    """
    Return sample IrisSet from some XAM radar set
    """

    radar_id = "wgj"
    archive_dir = config['archive_dir']
    radar_dir = os.path.join(archive_dir, radar_id)
    iris_collection = bugtracker.io.iris.IrisCollection(radar_dir, radar_id)

    sample_datetime = datetime.datetime(2014, 4, 16, 2, 30, 20)
    sample_set = iris_collection.closest_set(sample_datetime)

    if sample_set is None:
        raise ValueError("Cannot find sample IrisSet")

    return sample_set