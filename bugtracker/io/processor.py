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
import datetime
import time

import numpy as np
import netCDF4 as nc
from scipy import stats

import bugtracker
from bugtracker.core.precip import PrecipFilter

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


    def init_plotter(self):
        """
        Activate the RadialPlotter. This code may need to be significantly
        modified if we need to do parallel plotting (multi-cpu to speed up
        the plotting of a large set of files).
        """

        radar_id = self.metadata.radar_id
        plot_dir = self.config['plot_dir']
        output_folder = os.path.join(plot_dir, radar_id)

        if not os.path.isdir(plot_dir):
            FileNotFoundError(f"This folder should have been created {plot_dir}")

        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)

        self.plotter = bugtracker.plots.radial.RadialPlotter(self.lats, self.lons, output_folder)

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


    def plot_graph(self, prefix, plot_type, angle, slice_data, plot_dt):

        label = f"{prefix}_{plot_type}_{angle}"
        max_range = 150

        self.plotter.set_data(slice_data, label, plot_dt, self.metadata, max_range)
        self.plotter.save_plot(min_value=-10, max_value=40)


    def plot_iris(self, iris_data, label_prefix):
        """
        Plots a set of iris data
        """

        if self.plotter is None:
            raise ValueError("Plotter has not been initialized!")

        print("Plotting:", label_prefix)

        print("Plotting convol")
        for x in range(0, len(self.convol_angles)):
            angle = self.convol_angles[x]
            slice_data = iris_data.convol[x,:,:]
            self.plot_graph(label_prefix, "convol", angle, slice_data, iris_data.datetime)

        print("Plotting dopvol")
        for x in range(0, len(self.dopvol_angles)):
            angle = self.dopvol_angles[x]
            slice_data = iris_data.dopvol[x,:,:]
            self.plot_graph(label_prefix, "dopvol", angle, slice_data, iris_data.datetime)



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


    def determine_zone_slope(self, iris_data, azim_zone, gate_zone):
        """
        We will only use CONVOL scans for determining slopes
        The following property can be used to exclude clutter from slope.
        self.convol_clutter
        """

        azim_region = self.config['precip']['azim_region']
        gate_region = self.config['precip']['gate_region']
        
        min_azim = azim_zone * azim_region
        max_azim = (azim_zone + 1) * azim_region

        min_gate = gate_zone * gate_region
        max_gate = (gate_zone + 1) * gate_region

        angle_list = []
        dbz_list = []

        for x in range(0, len(self.convol_angles)):
            angle = self.convol_angles[x]
            zone_data = iris_data.convol[x,min_azim:max_azim,min_gate:max_gate]
            # Should be more OOP
            zone_clutter = self.convol_clutter[x,min_azim:max_azim,min_gate:max_gate]
            zone_clutter_bool = zone_clutter.astype(bool)

            if zone_data.shape != zone_clutter.shape:
                raise ValueError("Incompatible zone shapes.")

            zone_flat = list(zone_data.flatten())
            zone_clutter_flat = list(zone_clutter_bool.flatten())

            num_cells = len(zone_flat)
            num_clutter = len(zone_clutter_flat)

            if num_cells != num_clutter:
                raise ValueError("Incompatible list lengths.")

            for y in range(0, num_cells):
                if not zone_clutter_flat[y]:
                    dbz = zone_flat[y]
                    angle_list.append(angle)
                    dbz_list.append(dbz)

        if len(angle_list) != len(dbz_list):
            raise ValueError("Zone slope error")

        # If there is only data from one elevation angle, we cannot
        # compute the slope.

        angle_set = set(angle_list)
        if len(angle_set) < 2:
            return np.nan
        else:
            slope, intercept, r_value, p_value, std_err = stats.linregress(angle_list, dbz_list)
            return slope


    def filter_precip(self, convol_precip, dopvol_precip, iris_data):

        t0 = time.time()

        self.config = bugtracker.config.load("./bugtracker.json")
        azim_region = self.config['precip']['azim_region']
        gate_region = self.config['precip']['gate_region']
        max_slope = self.config['precip']['max_dbz_per_degree']

        if self.grid_info.azims % azim_region != 0:
            raise ValueError(f"Choose value of azim_region that divides {self.grid_info.azims} evenly.")

        if self.grid_info.gates % gate_region != 0:
            raise ValueError(f"Choose value of gate_region that divides {self.grid_info.gates} evenly")

        azim_zones = self.grid_info.azims // azim_region
        gate_zones = self.grid_info.gates // gate_region

        for x in range(0, azim_zones):
            for y in range(0, gate_zones):
                slope = self.determine_zone_slope(iris_data, x, y)
                if not np.isnan(slope) and slope > max_slope:
                    min_azim = x * azim_region
                    max_azim = (x + 1) * azim_region

                    min_gate = y * gate_region
                    max_gate = (y + 1) * gate_region

                    convol_precip.filter_3d[:,min_azim:max_azim,min_gate:max_gate] = True
                    dopvol_precip.filter_3d[:,min_azim:max_azim,min_gate:max_gate] = True

        t1 = time.time()
        print("Total time for precip filter:", t1 - t0)


    def output_filename(self, scan_dt):
        
        output_folder = self.config['netcdf_dir']

        if not os.path.isdir(output_folder):
            raise FileNotFoundError(output_folder)

        pattern = "dbz_%Y%m%d%H%M.nc"
        output_filename = scan_dt.strftime(pattern)

        return os.path.join(output_folder, output_filename)


    def plot_levels(self, iris_data, filtered=True):
        """
        Plot every level of the dbz output
        """

        max_range = self.config["plot_settings"]["max_range"]
        num_elevs = len(iris_data.dbz_elevs)
        print("angles:", iris_data.dbz_elevs)

        prefix = None
        dbz_field = None
        if filtered:
            prefix = "filtered"
            dbz_field = iris_data.dbz_filtered
        else:
            prefix = "unfiltered"
            dbz_field = iris_data.dbz_unfiltered

        for x in range(0,num_elevs):
            elev = iris_data.dbz_elevs[x]
            data = dbz_field[x,:,:]
            label = f"{prefix}_angle_{elev:.1f}"
            print(f"Plotting: {label}")
            self.plotter.set_data(data, label, iris_data.datetime, self.metadata, max_range)
            self.plotter.save_plot(min_value=-15.0, max_value=40.0)


    def set_joint_product(self, iris_data):
        """
        Collapsing 3D dbz product into a 2D flat grid.
        """

        # Let's mask out anything over 30, first
        bug_threshold = 30.0
        final_dbz = np.ma.masked_where(iris_data.dbz_filtered >= bug_threshold, iris_data.dbz_filtered)

        iris_data.joint_product = np.amax(final_dbz, axis=0)
        print(type(iris_data.joint_product))
        print("joint shape:", iris_data.joint_product.shape)


    def plot_joint_product(self, iris_data):

        max_range = self.config["plot_settings"]["max_range"]

        data = iris_data.joint_product[:,:]
        label = f"joint_product"
        print(f"Plotting: {label}")
        self.plotter.set_data(data, label, iris_data.datetime, self.metadata, max_range)
        self.plotter.save_plot(min_value=-15.0, max_value=40.0)


    def plot_target_id(self, id_matrix, iris_data):
        """
        Creating TargetIdPlotter from RadialPlotter
        """
        lats = self.plotter.lats
        lons = self.plotter.lons
        output_folder = self.plotter.output_folder
        id_plotter = bugtracker.plots.identify.TargetIdPlotter(lats, lons, output_folder)

        max_range = self.config["plot_settings"]["max_range"]

        prefix = "target_id"
        dbz_elevs = iris_data.dbz_elevs
        num_dbz_elevs = len(dbz_elevs)

        for x in range(0, num_dbz_elevs):
            elev = dbz_elevs[x]
            data = id_matrix[x,:,:]
            label = f"{prefix}_angle_{elev:.1f}"
            print(f"Plotting: {label}")
            id_plotter.set_data(data, label, iris_data.datetime, self.metadata, max_range)
            id_plotter.save_plot()


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

        iris_data = bugtracker.core.iris.IrisData(iris_set)
        iris_data.fill_grids()
        # plot the unmodified files
        #self.plot_iris(iris_data, "raw")
        
        t1 = time.time()

        # construct the PrecipFilter from iris_set
        convol_precip = PrecipFilter(self.metadata, self.grid_info, self.convol_angles)
        dopvol_precip = PrecipFilter(self.metadata, self.grid_info, self.dopvol_angles)

        self.filter_precip(convol_precip, dopvol_precip, iris_data)

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

        self.plot_levels(iris_data, filtered=False)
        self.plot_levels(iris_data, filtered=True)
        self.plot_joint_product(iris_data)
        self.plot_target_id(id_matrix, iris_data)

        t7 = time.time()

        print(f"Fill grids, construct data: {(t1-t0):.3f} s")
        print(f"Precip filter: {(t2-t1):.3f} s")
        print(f"Combining filters: {(t3-t2):.3f} s")
        print(f"Vertical merge: {(t4-t3):.3f} s")
        print(f"Output product NETCDF4 {(t5-t4):.3f} s")
        print(f"Target ID setup and export {(t6-t5):.3f} s")
        print(f"Plotting radial graphs {(t7-t6):.3f} s")


    def process_sets(self, iris_sets):

        self.init_plotter()

        if len(iris_sets) == 0:
            raise ValueError("There are 0 IrisSet entries - cannot process.")

        for iris_set in iris_sets:
            self.process_set(iris_set)


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