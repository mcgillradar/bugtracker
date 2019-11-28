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
from bugtracker.calib.clutter import ClutterFilter

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


    def export(self, output_file, args):
        """
        Save netCDF4 output file
        """

        timestamp = args.timestamp
        calib_hours = args.data_hours

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dset = nc.Dataset(output_file, mode="w")

        dset.setncattr_string("calib_start", timestamp)
        dset.setncattr("calib_hours", calib_hours)

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

    def __init__(self, args, metadata, grid_info):

        self.args = args
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
        self.data.export(output_file, self.args)

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

    def __init__(self, args, metadata, grid_info):

        super().__init__(args, metadata, grid_info)
        self.config = bugtracker.config.load("./bugtracker.json")
        self.convol_clutter = ClutterFilter(metadata, grid_info)
        self.dopvol_clutter = ClutterFilter(metadata, grid_info)


    def init_angles(self, sample_set):

        dopvol_angles = sample_set.get_elevs("dopvol")
        convol_angles = sample_set.get_elevs("convol")

        self.convol_clutter.setup(convol_angles)
        self.dopvol_clutter.setup(dopvol_angles)


    def set_calib_data(self, calib_sets):

        self.calib_sets = calib_sets

        if len(calib_sets) < 1:
            raise ValueError("Invalid number of calib sets")

        self.init_angles(calib_sets[0])


    def count_instances(self, iris_set):
        """
        Takes in a IrisSet object and counts up all instances
        above a threshold, adding to instances counters.
        """

        iris_data = bugtracker.core.iris.IrisData(iris_set)
        iris_data.fill_grids()

        dbz_threshold = self.config['clutter']['dbz_threshold']

        dopvol_dims = self.dopvol_clutter.get_dims()
        convol_dims = self.convol_clutter.get_dims()

        if iris_data.dopvol.shape != dopvol_dims:
            raise ValueError(f"Incompatible shape: {dopvol_dims}")

        if iris_data.convol.shape != convol_dims:
            raise ValueError(f"Incompatible shape: {convol_dims}")

        print("dopvol type:", type(iris_data.dopvol))
        print("convol type:", type(iris_data.convol))

        dopvol_above = iris_data.dopvol > dbz_threshold
        convol_above = iris_data.convol > dbz_threshold

        dopvol_above = dopvol_above.filled(fill_value=False)
        convol_above = convol_above.filled(fill_value=False)

        self.dopvol_instances = self.dopvol_instances + dopvol_above.astype(int)
        self.convol_instances = self.convol_instances + convol_above.astype(int)


    def create_masks(self, threshold):
        
        dopvol_dims = self.dopvol_clutter.get_dims()
        convol_dims = self.convol_clutter.get_dims()

        # Counters for number of dopvol/convol above threshold
        self.dopvol_instances = np.zeros(dopvol_dims, dtype=int)
        self.convol_instances = np.zeros(convol_dims, dtype=int)

        num_timeseries = len(self.calib_sets)
        if num_timeseries == 0:
            raise ValueError("No files in calibration set.")

        for iris_set in self.calib_sets:
            self.count_instances(iris_set)

        # Normalization
        self.norm_dopvol = self.dopvol_instances / float(num_timeseries)
        self.norm_convol = self.convol_instances / float(num_timeseries)

        bugtracker.core.utils.arr_info(self.dopvol_instances, "dopvol_instances")
        bugtracker.core.utils.arr_info(self.convol_instances, "convol_instances")

        bugtracker.core.utils.arr_info(self.norm_dopvol, "norm_dopvol")
        bugtracker.core.utils.arr_info(self.norm_convol, "norm_convol")

        prev_shape_dopvol = self.dopvol_clutter.filter_3d.shape
        prev_shape_convol = self.convol_clutter.filter_3d.shape

        print("Coverage threshold:", threshold)

        self.dopvol_clutter.filter_3d = self.norm_dopvol >= threshold
        self.convol_clutter.filter_3d = self.norm_convol >= threshold

        post_shape_dopvol = self.dopvol_clutter.filter_3d.shape
        post_shape_convol = self.convol_clutter.filter_3d.shape

        bugtracker.core.utils.arr_info(self.dopvol_clutter.filter_3d, "dopvol_clutter")
        bugtracker.core.utils.arr_info(self.convol_clutter.filter_3d, "convol_clutter")

        if prev_shape_dopvol != post_shape_dopvol:
            raise ValueError("Incompatible shapes: {prev_shape_dopvol} != {post_shape_dopvol}")

        if prev_shape_convol != post_shape_convol:
            raise ValueError("Incompatible shapes: {prev_shape_convol} != {post_shape_convol}")


    def print_mask(self, label, clutter_filter):
        
        print("Showing stats for filter:", label)

        num_angles = len(clutter_filter.vertical_angles)
        for x in range(0, num_angles):
            print("Current angle:", clutter_filter.vertical_angles[x])
            current_level = (clutter_filter.filter_3d[x,:,:]).astype(int)
            above = current_level.sum()
            total = current_level.size
            percent = above / float(total)
            print(f"Num above threshold: {above}/{total}")
            print(f"Percentage: {percent}")

    def print_masks(self):
        
        self.print_mask("dopvol", self.dopvol_clutter)
        self.print_mask("convol", self.convol_clutter)

    def save_masks(self):
        """
        Geometry/clutter/dbz masks are Iris-specific
        This could probably be refactored to avoid repeating
        """

        dopvol_angles = self.dopvol_clutter.vertical_angles
        convol_angles = self.convol_clutter.vertical_angles

        num_dopvol_angles = len(dopvol_angles)
        num_convol_angles = len(convol_angles)

        print("Dopvol angles:", dopvol_angles)
        print("Convol angles:", convol_angles)

        output_file = bugtracker.core.cache.calib_filepath(self.metadata, self.grid_info)

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dset = nc.Dataset(output_file, mode="r+")
        dset.createDimension("dopvol_angles", num_dopvol_angles)
        dset.createDimension("convol_angles", num_convol_angles)

        dopvol_dims = ('dopvol_angles', 'azims', 'gates')
        convol_dims = ('convol_angles', 'azims', 'gates')

        nc_convol_angles = dset.createVariable("convol_angles", float, ('convol_angles'))
        nc_dopvol_angles = dset.createVariable("dopvol_angles", float, ('dopvol_angles'))

        nc_convol_angles[:] = convol_angles[:]
        nc_dopvol_angles[:] = dopvol_angles[:]

        # Unsigned integer 1 bytes, to save space.
        # 0 corresponds to no mask, 1 corresponds to mask (Filter)
        nc_convol_clutter = dset.createVariable("convol_clutter", 'u1', convol_dims)
        nc_dopvol_clutter = dset.createVariable("dopvol_clutter", 'u1', dopvol_dims)

        print("convol shape:", self.convol_clutter.filter_3d.shape)
        print("dopvol_shape:", self.dopvol_clutter.filter_3d.shape)

        nc_convol_clutter[:,:,:] = self.convol_clutter.filter_3d[:,:,:]
        nc_dopvol_clutter[:,:,:] = self.dopvol_clutter.filter_3d[:,:,:]

        dset.close()


class OdimController(Controller):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)
        raise NotImplementedError("OdimH5 filetype not currently supported.")


class NexradController(Controller):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)
        raise NotImplementedError("NEXRAD filetype not currently supported.")

