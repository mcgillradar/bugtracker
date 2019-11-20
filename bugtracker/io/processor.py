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
import netcdf4 as nc

import bugtracker


class Processor(abc.ABC):

    def __init__(self, metadata, grid_info):

        self.metadata = metadata
        self.grid_info = grid_info
        self.calib_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)

        if not os.path.isfile(self.calib_file):
            raise FileNotFoundError("Missing calib file")

        self.load_universal_calib()


    def load_universal_calib(self):
        """
        Load parts of the calibration file that are universal
        to all data types (i.e. lats, lons, altitude)
        """
        
        calib_file = self.calib_file
        dset = nc.Dataset()


    @abc.abstractmethod
    def load_specific_calib(self):
        """
        Load parts of calib file that are specific to a particular
        filetype.
        """
        pass


class IrisProcessor(Processor):

    def __init__(self, metadata, grid_info):
        super().__init__(metadata, grid_info)
        self.load_specific_calib()


    def load_specific_calib(self):
        pass

class OdimProcessor(Processor):
    """
    Processor for Odim H5 files (new Environment Canada format)
    """

    def __init__(self):

        super().__init__()


class NexradProcessor(Processor):
    """
    Processor for US Weather Service NEXRAD file format
    """

    def __init__(self):

        super().__init__()