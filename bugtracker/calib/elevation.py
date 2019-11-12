"""
Manages elevation
"""

import os
import math
import time

import numpy as np
import pyart

import bugtracker


def get_key(lat, lon):
    """
    Corresponds to the SRTM3 notation. Keep in mind
    this refers to the bottom left corner.
    """

    int_lat = int(math.floor(lat))
    int_lon = int(math.floor(lon))

    lat_str = ""
    lon_str = ""
    
    abs_lat = int(abs(int_lat))
    abs_lon = int(abs(int_lon))

    if int_lat < 0:
        lat_str = f"S{abs_lat:02}"
    else:
        lat_str = f"N{abs_lat:02}"

    if int_lon < 0:
        lon_str = f"W{abs_lon:03}"
    else:
        lon_str = f"E{abs_lon:03}"

    return f"{lat_str}{lon_str}"


def get_idx(lat, lon):
    idx_tuple = (100,100)
    return idx_tuple


class SRTM3Reader:
    """
    
    """

    def __init__(self, metadata, grid_info):
        """
        GridInfo is an class referring to the (azim,gates) grid
        of the upscaled polar radar.
        """

        self.config = bugtracker.config.load('./bugtracker.json')
        self.metadata = metadata
        self.grid_info = grid_info
        coords = bugtracker.core.utils.latlon(grid_info, metadata)
        self.radar_lats = coords['lats']
        self.radar_lons = coords['lons']
        self.polar_points = dict()

        bugtracker.core.utils.arr_info(self.radar_lats, "radar_lats")
        bugtracker.core.utils.arr_info(self.radar_lons, "radar_lons")


    def get_active_cells(self):
        """
        Which SRTM3 grid tiles are required?
        """

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        for x in range(0,azims):
            for y in range(0,gates):
                lat = self.radar_lats[x,y]
                lon = self.radar_lons[x,y]
                current_key = get_key(lat,lon)
                if current_key in self.polar_points:
                    self.polar_points[current_key] += 1
                else:
                    self.polar_points[current_key] = 1


    def get_active_keys(self):
        return list(self.polar_points.keys())


    def load_elevation(self):
        azims = self.grid_info.azims
        gates = self.grid_info.gates
        return np.zeros((azims, gates), dtype=float)


class SRTM3Cell:
    """
    SRTM3 grid cell object
    """

    def __init__(self, lat_bl, lon_bl):
        """
        Here lat_bl and lon_bl are "bottom left" of the grid.
        """

        N = 1201
        dims = (N, N)

        self.N = N
        self.lat_bl = lat_bl
        self.lon_bl = lon_bl

        self.lats = np.zeros(dims, dtype=float)
        self.lons = np.zeros(dims, dtype=float)

        t0 = time.time()
        self.slow_fill()
        t1 = time.time()

        print("Time for slow fill:", t1 - t0)


    def slow_fill(self):
        """
        There are fast numpy methods for this, this is a not for production.
        """

        min_lat = self.lat_bl
        min_lon = self.lon_bl
        max_lat = min_lat + 1.0
        max_lon = min_lon + 1.0

        # assuming rows are latitude
        lat_col = np.linspace(min_lat, max_lat, num=self.N)
        lon_row = np.linspace(min_lon, max_lon, num=self.N)

        print(lat_col)
        print(lon_row)

        for x in range(0, self.N):
            self.lats[x,:] = lat_col

        for y in range(0, self.N):
            self.lons[y,:] = lon_row[y]



def read(srtm3_file):
    """

    """

    if not os.path.isfile(srtm3_file):
        raise FileNotFoundError(srtm3_file)

    test_array = np.fromfile(srtm3_file, dtype=np.int16)
    swapped_array = test_array.byteswap()

    N = 1201
    new_dims = (N, N)
    np_2dim_array = np.reshape(swapped_array, new_dims)

    t0 = time.time()

    new_2d_array = np.zeros(new_dims, dtype=float)

    for x in range(0, N):
        for y in range(0, N):
            new_2d_array[y,x] = np_2dim_array[N - x - 1, N - y - 1]

    t1 = time.time()
    print("Reshaping time:", t1-t0)

    final = np.rot90(new_2d_array, k=3)

    return new_2d_array
