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
This module provides a standardized way of dumping a PyART
radar object to NETCDF4

The radar objects are created with the 'dbz' field, and
have lat/lon of radar as data fields.

We should also include radar title as some kind of metadata.
"""

import os
import glob
import datetime

import numpy as np
import netCDF4 as nc


def get_output_filename(scan_dt, output_folder):
    """
    Creates standardized output netCDF4 filename, based
    on datetime.

    TODO: Should filename also include radar id to avoid conflicts?
    """

    fmt = "%Y%m%d_%H%M.nc"
    basename = scan_dt.strftime(fmt)
    return os.path.join(output_folder, basename)


def check_dims(dbz_array, grid):
    """
    Verify numpy output array corresponds to GridInfo dims
    """

    shape = dbz_array.shape
    azims = shape[0]
    gates = shape[1]

    if azims != grid.azims:
        raise ValueError(f"Grid azims do not correspond: {azims} != {grid.azims}")

    if gates != grid.gates:
        raise ValueError(f"Grid gates do not correspond: ")


def save_netcdf(grid, metadata, dbz_array, output_folder):

    output_name = get_output_filename(metadata.scan_dt, output_folder)
    print("Saving NETCDF4 output:", output_name)

    check_dims(dbz_array, grid)

    dset = nc.Dataset(output_name, 'w', format='NETCDF4')

    dset.createDimension('azims', grid.azims)
    dset.createDimension('gates', grid.gates)
    dbz = dset.createVariable('dbz', 'f4', ('azims','gates'))
    
    dbz[:,:] = dbz_array[:,:]

    # Adding metadata
    dset.latitude = metadata.lat
    dset.longitude = metadata.lon
    dset.radar_id = metadata.radar_id
    dset.datetime = metadata.scan_dt.strftime("%Y%m%d%H%M")
    dset.name = metadata.name

    dset.close()