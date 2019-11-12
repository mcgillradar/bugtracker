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
The clutter mask 
"""

import os

import numpy as np
import netCDF4 as nc

import bugtracker.config


class Grid:

    def __init__(self):

        self.lats = None
        self.lons = None
        self.altitude = None


class Data:

    def __init__(self, metadata, grid_info):

        self.metadata = metadata
        self.grid_info = grid_info

        self.lats = None
        self.lons = None
        self.altitude = None

        self.geometry_mask = None
        self.clutter_mask = None



    def check_data(self):
        """
        Check if the data is valid and can be exported to
        netCDF4 file.
        """

        dims = (self.grid_info.azims, self.grid_info.gates)

        if self.lats is None or self.lats.shape != dims:
            raise ValueError("self.lats invalid")

        if self.lons is None or self.lons.shape != dims:
            raise ValueError("self.lons invalid")

        if self.altitude is None or self.altitude.shape != dims:
            raise ValueError("self.altitude invalid")

        # For now, not checking geometry and clutter masks.


    def export(self, output_file):
        """
        Save netCDF4 output file
        """

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dset = nc.Dataset(output_file, mode="w")
        dset.createDimension("azims", azims)
        dset.createDimension("gates", gates)

        nc_lat = dset.createVariable("lats", float, ('azims','gates'))
        nc_lon = dset.createVariable("lons", float, ('azims', 'gates'))
        nc_altitude = dset.createVariable("altitude", float, ('azims', 'gates'))

        nc_lat[:,:] = self.lats[:,:]
        nc_lon[:,:] = self.lons[:,:]
        nc_altitude[:,:] = self.altitude[:,:]

        # For now, not saving masks

        dset.close()


class Controller():

    def __init__(self, metadata, grid_info):

        self.config = bugtracker.config.load("./bugtracker.json")
        self.metadata = metadata
        self.grid_info = grid_info

        self.data = Data(metadata, grid_info)


    def save(self):
        """
        Save to NETCDF4, check if data is valid.
        Determine calib netCDF4 filename using cache module.
        """

        output_file = bugtracker.core.cache.calib_filepath(self.metadata, self.grid_info)

        self.data.check_data()
        self.data.export(output_file)

        if not os.path.isfile(output_file):
            raise FileNotFoundError(f"Error saving output file: {output_file}")
        else:
            print(f"Saved output calib file: {output_file}")


    def set_grids(self, calib_grid):
        # Check that it's a calib.calib.Grid object

        self.data.lats = calib_grid.lats
        self.data.lons = calib_grid.lons
        self.data.altitude = calib_grid.altitude


    def create_masks(self):
        """
        Geometry/clutter/dbz masks are Iris-specific
        """

        #dims = (self.grid_info.azims, self.grid_info.gates)

        #self.data.geometry_mask = np.zeros(dims, dtype=float)
        #self.data.clutter_mask = np.zeros(dims, dtype=float)

        pass