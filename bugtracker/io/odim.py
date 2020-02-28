"""
This file is part of Bugtracker
Copyright (C) 2020  McGill Radar Group

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

import os

import pyart


class OdimManager:

    """
    The OdimManager class is responsible for getting 
    """

    def __init__(self, config, radar_id):

        pass


class OdimData(ScanData):

    """
    Data wrapper for OdimH5
    """

    def __init__(self, odim_file, metadata, grid_info):

        scan_dt = metadata.scan_dt

        super().__init__(metadata, grid_info, datetime)

        if not os.path.isfile(odim_file):
            raise FileNotFoundError("Odim file does not exist")

        self.handle = pyart.aux_io.read_odim_h5(odim_file)


        self.dbz_unfiltered = self.init_field()
        self.velocity = self.init_field()
        self.cross_correlation_ratio = self.init_field()
        self.diff_reflectivity = self.init_field()


    def __str__(self):

        rep = "OdimData:\n"

        rep += f"Dimensions: {self.reflectivity.shape}"

        return rep


    def check_field_dims(self, field_name):

        if field_name not in self.handle.fields:
            raise KeyError(f"Missing field {field_name}")

        # Can't reliably check azims, because they are 
        # bundled into the vertical direction.

        field_dims = self.handle.fields[field_name]['data'].shape

        if len(field_dims) != 2:
            raise ValueError(f"Invalid field_dims: {field_dims}")

        if self.grid_info.gates != field_dims[1]:
            raise ValueError("Invalid gate number")


    def check_consistency(self):
        
        template_msg = "\nYou may need to call the method 'build_template()' from the NexradManager"

        # Check that all data grids initialized

        if self.metadata is None:
            raise ValueError(f"metadata not initialized {template_msg}")

        if self.grid_info is None:
            raise ValueError(f"product_grid not initialized {template_msg}")

        # check field dimensions

        self.check_field_dims("reflectivity")
        self.check_field_dims("velocity")
        self.check_field_dims("cross_correlation_ratio")
        self.check_field_dims("differential_reflectivity")