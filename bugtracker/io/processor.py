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
Currently unused processor class
"""
import os
import abc
import datetime
import time
import math

import numpy as np
import netCDF4 as nc
from scipy import stats

import bugtracker
import bugtracker.core.precip

class Processor(abc.ABC):

    def __init__(self, metadata, grid_info):

        self.config = bugtracker.config.load("./bugtracker.json")

        self.metadata = metadata
        self.grid_info = grid_info
        self.calib_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)
        self.plotter = None

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

        print(f"Loading calib file: {calib_file}")

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


    def output_filename(self, scan_dt):
        """
        TODO: This should specialize to different folders based on
        metadata.radar_id
        """

        output_folder = self.config['netcdf_dir']

        if not os.path.isdir(output_folder):
            raise FileNotFoundError(output_folder)

        radar_id = self.metadata.radar_id
        subfolder = os.path.join(output_folder, radar_id)

        if not os.path.isdir(subfolder):
            os.mkdir(subfolder)

        pattern = "dbz_%Y%m%d%H%M.nc"
        output_filename = scan_dt.strftime(pattern)

        return os.path.join(subfolder, output_filename)


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

    @abc.abstractmethod
    def impose_filter(self):
        pass


    @abc.abstractmethod
    def set_joint_product(self):
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


    def impose_filter(self, iris_data, np_convol, np_dopvol):
        """
        Standin method for applying joint filters
        """

        raw_dopvol_shape = iris_data.dopvol.shape
        raw_convol_shape = iris_data.convol.shape

        raw_dopvol_mask = np.ma.getmask(iris_data.dopvol)
        raw_convol_mask = np.ma.getmask(iris_data.convol)

        dopvol_mask = np.ma.mask_or(np_dopvol, raw_dopvol_mask)
        convol_mask = np.ma.mask_or(np_convol, raw_convol_mask)

        iris_data.dopvol = np.ma.array(iris_data.dopvol, mask=dopvol_mask)
        iris_data.convol = np.ma.array(iris_data.convol, mask=convol_mask)

        filtered_dopvol_shape = iris_data.dopvol.shape
        filtered_convol_shape = iris_data.convol.shape

        if raw_dopvol_shape != filtered_dopvol_shape:
            raise ValueError("Error in DOPVOL array size")

        if raw_convol_shape != filtered_convol_shape:
            raise ValueError("Error in new CONVOL array size")


    def set_joint_product(self, iris_data):
        """
        Collapsing 3D dbz product into a 2D flat grid.
        """

        # Let's mask out anything over 30, first
        bug_threshold = self.config['processing']['joint_cutoff']
        final_dbz = np.ma.masked_where(iris_data.dbz_filtered >= bug_threshold, iris_data.dbz_filtered)

        iris_data.joint_product = np.amax(final_dbz, axis=0)
        print(type(iris_data.joint_product))
        print("joint shape:", iris_data.joint_product.shape)


    def fill_clutter(self, init_elevs, init_data, iris_data):

        num_dbz_elevs = len(iris_data.dbz_elevs)
        combined_dims = (num_dbz_elevs, self.grid_info.azims, self.grid_info.gates)

        clutter_grid = np.zeros(combined_dims, dtype=bool)

        if len(init_elevs) != init_data.shape[0]:
            raise ValueError(f"Incompatible array shape: {init_data.shape}")

        for x in range(0, len(init_elevs)):
            current_angle = init_elevs[x]
            idx = iris_data.dbz_elevs.index(current_angle)
            clutter_grid[idx,:,:] = init_data[x,:,:]

        return clutter_grid


    def combine_clutter(self, convol, dopvol, iris_data):
        # Returns numpy boolean array

        print("dopvol_elevs:", iris_data.dopvol_elevs)
        print("convol_elevs:", iris_data.convol_elevs)
        print("dbz_elevs:", iris_data.dbz_elevs)

        clutter_convol = self.fill_clutter(iris_data.convol_elevs, convol, iris_data)
        clutter_dopvol = self.fill_clutter(iris_data.dopvol_elevs, dopvol, iris_data)

        combined = np.logical_or(clutter_convol, clutter_dopvol)
        return combined


    def combine_precip(self, convol, dopvol, iris_data):

        num_dbz_elevs = len(iris_data.dbz_elevs)
        combined_dims = (num_dbz_elevs, self.grid_info.azims, self.grid_info.gates)
        combined_filter = np.zeros(combined_dims, dtype=bool)

        # For precip, the filter is uniform over elevation.
        for x in range(0, num_dbz_elevs):
            combined_filter[x,:,:] = convol[0,:,:]

        return combined_filter


    def process_set(self, iris_set):
        """
        The logic in this function is a bit too complicated, and
        should be refactored at some point. This method should not
        be handling the internal data of the Filter objects.
        """

        t0 = time.time()

        iris_data = bugtracker.io.iris.IrisData(iris_set)
        iris_data.fill_grids()
        
        t1 = time.time()

        # construct the PrecipFilter from iris_set
        convol_precip = PrecipFilter(self.metadata, self.grid_info, self.convol_angles)
        dopvol_precip = PrecipFilter(self.metadata, self.grid_info, self.dopvol_angles)

        #convol_precip.apply(iris_data.convol, self.convol_clutter, self.convol_angles)
        #convol_precip.copy(dopvol_precip)

        t2 = time.time()

        # Combining ClutterFilter with PrecipFilter

        convol_clutter_bool = self.convol_clutter.astype(bool)
        dopvol_clutter_bool = self.dopvol_clutter.astype(bool)

        convol_joint = np.logical_or(convol_clutter_bool, convol_precip.filter_3d)
        dopvol_joint = np.logical_or(dopvol_clutter_bool, dopvol_precip.filter_3d)

        t3 = time.time()

        iris_data.dbz_unfiltered = iris_data.merge_dbz()

        t4 = time.time()

        # modify the files based on filters
        self.impose_filter(iris_data, convol_joint, dopvol_joint)

        nc_filename = self.output_filename(iris_data.datetime)

        iris_data.dbz_filtered = iris_data.merge_dbz()
        self.set_joint_product(iris_data)

        iris_output = bugtracker.io.models.IrisOutput(self.metadata, self.grid_info)
        iris_output.populate(iris_data)
        iris_output.validate()
        iris_output.write(nc_filename)

        t5 = time.time()

        joint_precip_bool = self.combine_precip(convol_precip.filter_3d, dopvol_precip.filter_3d, iris_data)
        joint_clutter_bool = self.combine_clutter(convol_clutter_bool, dopvol_clutter_bool, iris_data)

        target_id = bugtracker.core.target_id.TargetId(iris_data.dbz_filtered, joint_clutter_bool, joint_precip_bool)
        id_matrix = target_id.export_matrix()

        iris_output.append_target_id(nc_filename, id_matrix)

        t6 = time.time()

        plot_queue = bugtracker.plots.parallel.ParallelPlotter(self.lats, self.lons, self.metadata, self.grid_info, iris_data, id_matrix)

        t7 = time.time()

        print(f"Fill grids, construct data: {(t1-t0):.3f} s")
        print(f"Precip filter: {(t2-t1):.3f} s")
        print(f"Combining filters: {(t3-t2):.3f} s")
        print(f"Vertical merge: {(t4-t3):.3f} s")
        print(f"Output product NETCDF4 {(t5-t4):.3f} s")
        print(f"Target ID setup and export {(t6-t5):.3f} s")
        print(f"Plotting radial graphs {(t7-t6):.3f} s")


    def process_sets(self, iris_sets):

        if len(iris_sets) == 0:
            raise ValueError("There are 0 IrisSet entries - cannot process.")

        for iris_set in iris_sets:
            self.process_set(iris_set)


class NexradProcessor(Processor):
    """
    Processor for US Weather Service NEXRAD file format
    """

    def __init__(self, manager):

        super().__init__(manager.metadata, manager.grid_info)
        self.manager = manager
        self.load_specific_calib()
        self.verify_specific_calib()


    def load_specific_calib(self):
        """
        Load the calibration file variables specific to
        NEXRAD files.
        """

        calib_file = self.calib_file
        dset = nc.Dataset(calib_file, mode='r')

        self.angles = dset.variables['angles'][:]
        self.clutter = dset.variables['clutter'][:,:,:]

        dset.close()


    def verify_specific_calib(self):
        
        num_angles = len(self.angles)

        if num_angles <= 1:
            raise ValueError("Not enough angles in calib")

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        calib_dim = (num_angles, azims, gates)

        if self.clutter.shape != calib_dim:
            raise ValueError(f"Invalid calib dimensions: {self.clutter.shape}")


    def filter_precip(self, precip_filter):
        print("Filtering precip")


    def impose_filter(self, nexrad_data, filter_joint):
        """
        Applying joint filter for nexrad data. Here 'raw' simply
        indicates before any processing has occured.
        """

        raw_dbz_shape = nexrad_data.dbz_unfiltered.shape
        raw_dbz_mask = np.ma.getmask(nexrad_data.dbz_unfiltered)
        filter_mask = np.ma.mask_or(filter_joint, raw_dbz_mask)

        nexrad_data.dbz_filtered = np.ma.array(nexrad_data.dbz_unfiltered, mask=filter_mask)

        dbz_filtered_shape = nexrad_data.dbz_filtered.shape

        if raw_dbz_shape != dbz_filtered_shape:
            raise ValueError("Error in dbz array size")


    def set_joint_product(self, nexrad_data):
        """
        Collapsing 3D dbz product into a 2D flat grid.
        """

        # Let's mask out anything over 30, first
        bug_threshold = self.config['processing']['joint_cutoff']
        final_dbz = np.ma.masked_where(nexrad_data.dbz_filtered >= bug_threshold, nexrad_data.dbz_filtered)

        nexrad_data.joint_product = np.amax(final_dbz, axis=0)
        print(type(nexrad_data.joint_product))
        print("joint shape:", nexrad_data.joint_product.shape)


    def process_file(self, nexrad_file):

        print("Processing file:", nexrad_file)

        t0 = time.time()

        nexrad_data = self.manager.extract_data(nexrad_file)

        t1 = time.time()

        # construct the PrecipFilter from iris_set
        precip = bugtracker.core.precip.NexradPrecipFilter(self.metadata, self.grid_info, nexrad_data.dbz_elevs)
        precip.apply(nexrad_data)

        t2 = time.time()

        # Combining ClutterFilter with PrecipFilter

        clutter_bool = self.clutter.astype(bool)
        filter_joint = np.logical_or(clutter_bool, precip.filter_3d)

        t3 = time.time()

        # modify the files based on filters
        self.impose_filter(nexrad_data, filter_joint)

        nexrad_datetime = self.manager.datetime_from_file(nexrad_file)
        nc_filename = self.output_filename(nexrad_datetime)

        self.set_joint_product(nexrad_data)

        nexrad_output = bugtracker.io.models.NexradOutput(self.metadata, self.grid_info)
        nexrad_output.populate(nexrad_data)
        nexrad_output.validate()
        nexrad_output.write(nc_filename)

        t4 = time.time()

        precip_bool = precip.filter_3d.astype(bool)

        target_id = bugtracker.core.target_id.TargetId(nexrad_data.dbz_unfiltered, clutter_bool, precip_bool)
        id_matrix = target_id.export_matrix()

        # Taking only desired levels
        max_scans = self.config['nexrad_settings']['vertical_scans']
        reduced_id_matrix = id_matrix[0:max_scans,:,:]

        nexrad_output.append_target_id(nc_filename, reduced_id_matrix)

        t5 = time.time()

        plot_queue = bugtracker.plots.parallel.ParallelPlotter(self.lats, self.lons, self.metadata, self.grid_info, nexrad_data, id_matrix)

        t6 = time.time()

        print(f"Fill grids, construct data: {(t1-t0):.3f} s")
        print(f"Precip filter: {(t2-t1):.3f} s")
        print(f"Combining filters: {(t3-t2):.3f} s")
        print(f"Output product NETCDF4 {(t4-t3):.3f} s")
        print(f"Target ID setup and export {(t5-t4):.3f} s")
        print(f"Plotting radial graphs {(t6-t5):.3f} s")


    def process_files(self, nexrad_files):

        for nexrad_file in nexrad_files:
            self.process_file(nexrad_file)


class OdimProcessor(Processor):
    """
    Processor for Odim H5 files (new Environment Canada format)
    """

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info)
        raise NotImplementedError("OdimProcessor")


    def load_specific_calib(self):
        pass


    def verify_specific_calib(self):
        pass


    def impose_filter(self):
        pass


    def set_joint_product(self):
        pass