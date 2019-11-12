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
Miscellaneous utility functions/classes thrown into
a utility module. If this grows too big, split it up
into multiple modules.
"""

import datetime

import numpy as np
import geopy
import pyart


class DateRange:

    def __init__(self, start, end):

        if not isinstance(start, datetime.datetime):
            raise ValueError(f"{start} is not datetime object.")

        if not isinstance(end, datetime.datetime):
            raise ValueError(f"{end} is not datetime object.")

        if start >= end:
            raise ValueError("start cannot be after end of DateRange.")

        self.start = start
        self.end = end



def maskgen(grid_info):
    """
    Generate an empty mask
    """
    dims = (grid_info.azims, grid_info.gates)
    mask = np.full(dims, True, dtype=bool)
    return mask



def dbz_mask(metadata, grid_info):
    """
    Don't necessarily need elevation info for this section.
    """
    
    dbz_mask = bugtracker.core.utils.maskgen(grid_info)

    return dbz_mask



def arr_info(np_array, label):

    print("*************************************")
    print(label)
    print("shape:", np_array.shape)
    print("max:", np_array.max())
    print("min:", np_array.min())
    print(np_array)


class BoundingBox:

    def __init__(self, lat_0, lon_0, km_distance):

        origin = geopy.Point(lat_0, lon_0)
        dist = geopy.distance.distance(kilometers=km_distance)
 
        west = dist.destination(origin, 270.0)
        north = dist.destination(origin, 0.0)
        east = dist.destination(origin, 90.0)
        south = dist.destination(origin, 180.0)

        self.min_lat = south.latitude
        self.max_lat = north.latitude
        self.min_lon = west.longitude
        self.max_lon = east.longitude


    def __str__(self):
        return f"{self.min_lat} < lat < {self.max_lat}\n{self.min_lon} < lon < {self.max_lon}\n"


def latlon(grid_info, metadata):
    """
    This code should not be duplicated in multiple places
    """

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
    
    grid_coords = dict()
    grid_coords['lats'] = lats
    grid_coords['lons'] = lons

    return grid_coords


