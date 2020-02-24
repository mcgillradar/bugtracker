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
Miscellaneous utility functions/classes thrown into
a utility module. If this grows too big, split it up
into multiple modules.
"""

import os
import sys
import datetime

import psutil
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


def arr_info(np_array, label):

    print("*************************************")
    print(label)
    print("shape:", np_array.shape)
    print("max:", np_array.max())
    print("min:", np_array.min())


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
        azimuths[x,:] = (grid_info.azim_step) * x + grid_info.azim_offset

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



def check_memory(requested_bytes):
    """
    This ensures you do
    """

    print(f"Requesting: {requested_bytes} bytes")

    vm = psutil.virtual_memory()
    available = vm.available

    print(f"Available memory: {available} bytes")

    if available < requested_bytes:
        raise MemoryError(f"Requested bytes {requested_bytes} greater than available: {available}")


def iris_scan_stats(radar_file, label):

    print("*******************************************")

    if radar_file is None or not os.path.isfile(radar_file):
        raise FileNotFoundError(radar_file)

    print("Iris statistics for scan type:", label)
    radar = pyart.io.read_sigmet(radar_file)

    ngates = radar.ngates
    nrays = radar.nrays
    nsweeps = radar.nsweeps

    print(f"ngates: {ngates}, nrays: {nrays}, nsweeps: {nsweeps}")

    gate_ranges = radar.range['data']
    num_gates = len(gate_ranges)
    max_distance = gate_ranges[num_gates - 1] / 1000.0
    print(f"Max distance: {max_distance} km")

    field_keys = radar.fields.keys()

    for key in field_keys:
        field_dims = radar.fields[key]['data'].shape
        print(f"Field: {key} - dims: {field_dims}")


def lower_compare(str1, str2):

    str1 = str1.strip().lower()
    str2 = str2.strip().lower()

    return str1 == str2