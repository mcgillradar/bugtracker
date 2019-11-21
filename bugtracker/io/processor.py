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
Currently unused processor class
"""
import os
import abc

import numpy as np
import netCDF4 as nc

import bugtracker


class Processor(abc.ABC):

    def __init__(self, metadata, grid_info):

        self.metadata = metadata
        self.grid_info = grid_info
        self.calib_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)

        if not os.path.isfile(self.calib_file):
            raise FileNotFoundError("Missing calib file")

        self.load_universal_calib()
        self.verify_universal_calib()


    def load_universal_calib(self):
        """
        Load parts of the calibration file that are universal
        to all data types (i.e. lats, lons, altitude)
        """
        
        calib_file = self.calib_file

        dset = nc.Dataset(calib_file, mode='r')

        self.lats = dset.variables['lats'][:,:]
        self.lons = dset.variables['lons'][:,:]
        self.altitude = dset.variables['altitude'][:,:]

        dset.close()

    def verify_universal_calib(self):
        """
        Make sure all the dimensions are correct
        """

        polar_dims = (self.grid_info.azims, self.grid_info.gates)

        if self.lats.shape != polar_dims:
            raise ValueError(f"Lat grid invalid dims: {self.lats.shape}")
        
        if self.lons.shape != polar_dims:
            raise ValueError(f"Lon grid invalid dims: {self.lons.shape}")

        if self.altitude.shape != polar_dims:
            raise ValueError(f"Altitude grid invalid dims: {self.altitude.shape}")


    @abc.abstractmethod
    def load_specific_calib(self):
        """
        Load parts of calib file that are specific to a particular
        filetype.
        """
        pass

    @abc.abstractmethod
    def verify_specific_calib(self):
        """
        Verify the dimensions are correct for filetype specific
        parts of the calibration
        """
        pass


class IrisProcessor(Processor):

    def __init__(self, metadata, grid_info):
        super().__init__(metadata, grid_info)
        self.load_specific_calib()
        self.verify_specific_calib()

    def load_specific_calib(self):
        """
        Iris-specific calibration data includes CONVOL/DOPVOL
        """

        calib_file = self.calib_file
        dset = nc.Dataset(calib_file, mode='r')

        self.convol_angles = dset.variables['convol_angles'][:]
        self.dopvol_angles = dset.variables['dopvol_angles'][:]
        self.convol_clutter = dset.variables['convol_clutter'][:,:,:]
        self.dopvol_clutter = dset.variables['dopvol_clutter'][:,:,:]

        dset.close()

    def verify_specific_calib(self):
        
        num_convol = len(self.convol_angles)
        num_dopvol = len(self.dopvol_angles)

        if num_convol <= 1:
            raise ValueError("Not enough CONVOL angles in calib")

        if num_dopvol <= 1:
            raise ValueError("Not enough DOPVOL angles in calib")

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        convol_dim = (num_convol, azims, gates)
        dopvol_dim = (num_dopvol, azims, gates)

        if self.convol_clutter.shape != convol_dim:
            raise ValueError(f"Invalid convol dimensions: {self.convol_clutter.shape}")

        if self.dopvol_clutter.shape != dopvol_dim:
            raise ValueError(f"Invalid dopvol dimensions: {self.dopvol_clutter.shape}")


class OdimProcessor(Processor):
    """
    Processor for Odim H5 files (new Environment Canada format)
    """

    def __init__(self):

        super().__init__()
        raise NotImplmentedError("OdimProcessor")


class NexradProcessor(Processor):
    """
    Processor for US Weather Service NEXRAD file format
    """

    def __init__(self):

        super().__init__()
        raise NotImplmentedError("NexradProcessor")