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
import abc
import time

import numpy as np
import netCDF4 as nc

import bugtracker.config
import bugtracker.core.utils

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


class Controller(abc.ABC):

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

    @abc.abstractmethod
    def create_masks(self):
        """
        Geometry/clutter/dbz masks are filetype-specific
        """
        pass

    @abc.abstractmethod
    def set_calib_data(self):
        pass


class IrisController(Controller):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)


    def set_calib_data(self, calib_sets):

        self.calib_sets = calib_sets

        print("Num calib sets:", len(calib_sets))

        timesteps = len(calib_sets)
        grid_cells = self.grid_info.azims * self.grid_info.gates

        convol_levels = 5
        dopvol_levels = 3
        bytes_per_float = 8
        requested_mem = bytes_per_float * convol_levels * len(calib_sets) * grid_cells

        bugtracker.core.utils.check_memory(requested_mem)

        dopvol_dims = None
        convol_dims = None

        self.dopvol_timeseries = np.ma.zeros(dopvol_dims, dtype=float)
        self.convol_timeseries = np.ma.zeros(convol_dims, dtype=float)

        c = input("Unexpected? (y/n)")


    def process_convol(self):
        
        convol_levels = 5

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        time_steps = len(self.calib_sets)
        dims = (time_steps, convol_levels, azims, gates)
        convol = np.zeros(dims, dtype=float)

        print("Item size:", convol.itemsize)
        print("%d bytes" % (convol.size * convol.itemsize))




    def process_dopvol(self):
        pass


    def create_masks(self):
        """
        Geometry/clutter/dbz masks are Iris-specific
        """



        convol_elevs = 5
        dopvol_elevs = 4


        #dims = (self.grid_info.azims, self.grid_info.gates)

        #self.data.geometry_mask = np.zeros(dims, dtype=float)
        #self.data.clutter_mask = np.zeros(dims, dtype=float)


class OdimController(Controller):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)
        raise NotImplementedError("OdimH5 filetype not currently supported.")


class NexradController(Controller):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)
        raise NotImplementedError("NEXRAD filetype not currently supported.")

