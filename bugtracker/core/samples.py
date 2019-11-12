"""
This module provides test data of various types (auto-generated
dbz grids, Metadata, GridInfo, ...)

The utility of this module is primarily for development and unit
testing. Production software should *NOT* be using these test
functions.
"""

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