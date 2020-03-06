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

import os
import time
import math

import numpy as np
from scipy import stats
import pyart
import geopy.distance

import bugtracker.core.utils
from bugtracker.core.filter import Filter
import bugtracker.plots.radial


class IrisPrecipFilter(Filter):

    def __init__(self, metadata, grid_info, iris_set):
        """
        The IRIS precipitation filter will be determined using the full set
        of convol scans. A large vertical sweep is required in order for the
        gradient-based precip detection method to be effective.

        Note that the gradient is a function of dBZ/km elevation, not elevation
        angle.
        """

        super().__init__(metadata, grid_info)

        # Using one output elevation angle

        self.convol = pyart.io.read(iris_set.convol)
        self.bins = None
        # Using one horizontal angle (for now)
        angles = [0.0]

        self.setup(angles)
        self.config = bugtracker.config.load("./bugtracker.json")


    def get_convol_coords(self):


        azimuths = self.convol.azimuth['data']
        ranges = self.convol.range['data']
        elevations = self.convol.elevation['data']

        num_azims = len(azimuths)
        num_ranges = len(ranges)
        shape = (num_azims, num_ranges)
        augmented_azims = np.zeros(shape, dtype=float)
        augmented_ranges = np.zeros(shape, dtype=float)
        augmented_elevs = np.zeros(shape, dtype=float)

        for x in range(0, num_ranges):
            augmented_azims[:,x] = azimuths[:]
            augmented_elevs[:,x] = elevations[:]

        for y in range(0, num_azims):
            augmented_ranges[y,:] = ranges[:]

        # Normalizing to kilometers
        augmented_ranges = augmented_ranges / 1000.0

        x_arr, y_arr, z_arr = pyart.core.antenna_to_cartesian(augmented_ranges, augmented_azims, augmented_elevs)

        distance_arr = np.sqrt(np.square(x_arr) + np.square(y_arr))

        lon_0 = self.metadata.lon
        lat_0 = self.metadata.lat

        print("lon_0:", lon_0)
        print("lat_0:", lat_0)

        lons, lats = pyart.core.cartesian_to_geographic_aeqd(x_arr, y_arr, lon_0, lat_0)


        # Convert to polar

        convol_coords = dict()
        convol_coords['distance'] = distance_arr
        # Converting height to kilometers
        convol_coords['z_km'] = z_arr / 1000.0


        return convol_coords


    def get_key(self, bucket_azim, bucket_gate):

        return f"{bucket_azim:03}_{bucket_gate:03}"


    def get_bucket(self, distance, azimuth):

        # The following are integers
        azim_bin_size = self.config["iris_settings"]["azim_precip_region"]
        gate_bin_size = self.config["iris_settings"]["gate_precip_region"]

        azims = self.grid_info.azims
        gates = self.grid_info.gates
        azim_step = self.grid_info.azim_step
        gate_step = self.grid_info.gate_step
        azim_offset = self.grid_info.azim_offset
        gate_offset = self.grid_info.gate_offset

        adj_azim = azimuth - azim_offset
        adj_distance = distance - gate_offset

        float_azim_idx = adj_azim / azim_step
        float_gate_idx = adj_distance / gate_step

        reduced_azim_idx = float_azim_idx / azim_bin_size
        reduced_gate_idx = float_gate_idx / gate_bin_size

        bucket_azim = int(reduced_azim_idx)
        bucket_gate = int(reduced_gate_idx)

        return bucket_azim, bucket_gate


    def bin_results(self, convol_coords):
        """
        The bins will be organized according to a dictionary
        of standardized strings

        For example
        key = "032_125"
        """

        print(self.metadata)
        print(self.grid_info)

        self.bins = dict()

        # The bucket size

        azim_bin_size = self.config["iris_settings"]["azim_precip_region"]
        gate_bin_size = self.config["iris_settings"]["gate_precip_region"]

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        num_azim_bins = azims // azim_bin_size
        num_gate_bins = gates // gate_bin_size

        rem_azim = azims % azim_bin_size
        rem_gate = gates % gate_bin_size

        print("rem_azim:", rem_azim)
        print("rem_gate:", rem_gate)

        for x in range(0, num_azim_bins):
            for y in range(0, num_gate_bins):
                current_key = self.get_key(x, y)
                self.bins[current_key] = dict()
                self.bins[current_key]['elevation'] = []
                self.bins[current_key]['dbz'] = []

        # Let's populate these bins with data points
        convol_data = self.convol.fields['total_power']['data']
        convol_shape = convol_data.shape
        
        t0 = time.time()

        min_height_km = 0.1
        max_height_km = 4.0

        print("Binning")
        for x in range(0, convol_shape[0]):
            for y in range(0, convol_shape[1]):
                distance = convol_coords['distance'][x,y]
                elevation = convol_coords['z_km'][x,y]
                azimuth = self.convol.azimuth['data'][x]
                dbz = convol_data[x,y]

                # Decide whether to include:
                if not isinstance(dbz, np.ma.core.MaskedConstant) and not np.isnan(dbz):
                    if elevation < max_height_km and elevation > min_height_km:
                        bucket_azim, bucket_gate = self.get_bucket(distance, azimuth)
                        bin_key = self.get_key(bucket_azim, bucket_gate)
                        self.bins[bin_key]['elevation'].append(elevation)
                        self.bins[bin_key]['dbz'].append(dbz)

        t1 = time.time()
        elapsed = t1 - t0
        print(f"Time for binning: {elapsed}")


    def linregress(self):

        slope_shape = (self.grid_info.azims, self.grid_info.gates)
        self.slopes = np.zeros(slope_shape, dtype=float)
        azim_bin_size = self.config["iris_settings"]["azim_precip_region"]
        gate_bin_size = self.config["iris_settings"]["gate_precip_region"]
        max_slope = self.config['iris_settings']['max_dbz_per_km']

        invalid_values = 0

        for key in self.bins:
            elevation = self.bins[key]['elevation']
            dbz = self.bins[key]['dbz']

            key_pair = key.split("_")
            bucket_azim_idx = int(key_pair[0])
            bucket_gate_idx = int(key_pair[1])
    
            azim_min_idx = azim_bin_size * bucket_azim_idx
            azim_max_idx = azim_bin_size * bucket_azim_idx + azim_bin_size
            gate_min_idx = gate_bin_size * bucket_gate_idx
            gate_max_idx = gate_bin_size * bucket_gate_idx + gate_bin_size

            BUCKET_AZIMS = slice(azim_min_idx, azim_max_idx)
            BUCKET_GATES = slice(gate_min_idx, gate_max_idx)



            if len(dbz) >= 2:
                slope, intercept, r_value, p_value, std_err = stats.linregress(elevation, dbz)
                
                if np.isnan(slope):
                    self.slopes[BUCKET_AZIMS,BUCKET_GATES] = -100.0
                else:
                    self.slopes[BUCKET_AZIMS,BUCKET_GATES] = slope
                
                if slope > max_slope:
                    self.filter_3d[:,BUCKET_AZIMS,BUCKET_GATES] = True
                else:
                    self.filter_3d[:,BUCKET_AZIMS,BUCKET_GATES] = False

            else:
                invalid_values += 1
                self.filter_3d[:,BUCKET_AZIMS,BUCKET_GATES] = True
                self.slopes[BUCKET_AZIMS,BUCKET_GATES] = -100.0
        print("Invalid values:", invalid_values)


    def plot_slopes(self):

        if self.slopes is None:
            raise ValueError("Slopes cannot be None")

        grid_coords = bugtracker.core.utils.latlon(self.grid_info, self.metadata)
        lats = grid_coords['lats']
        lons = grid_coords['lons']
        output_folder = os.path.join(self.config['plot_dir'], self.metadata.radar_id)
        plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, output_folder, self.grid_info)

        bugtracker.core.utils.arr_info(lats, "lats")
        bugtracker.core.utils.arr_info(lons, "lons")
        bugtracker.core.utils.arr_info(self.slopes, "slopes")

        max_range = self.config['plot_settings']['max_range']
        plotter.set_data(self.slopes, "gradient", self.metadata.scan_dt, self.metadata, max_range)
        plotter.save_plot(min_value=-200.0, max_value=200.0)


    def projection(self):
        """
        For bug echoes, we are looking close to 0 degrees in our scan.
        Therefore, we are interested in a precipitation filter that corresponds
        to this angle, and can be assumed to be constant in the vertical direction.

        However, for elevation angles as high as 24 degrees, we cannot consider
        them in the same vertical column. Therefore we must project onto the GridInfo
        grid that is used for the processing algorithm.
        """



        convol_coords = self.get_convol_coords()

        self.bin_results(convol_coords)
        
        t0 = time.time()
        self.linregress()
        t1 = time.time()

        elapsed = t1 - t0
        print("Regression time:", elapsed)



    def determine_angles(self, iris_set):
        """
        Look at the CONVOL file, and see how many vertical
        scans there are.
        """

        fixed_angles = len(self.convol.fixed_target['data'])





class NexradPrecipFilter(Filter):

    def __init__(self, metadata, grid_info, angles):
        """
        The NEXRAD precipitation filter is based on a differential
        reflectivity and correlation method.
        """

        super().__init__(metadata, grid_info)
        self.setup(angles)
        self.config = bugtracker.config.load("./bugtracker.json")


    def verify_dims(self):
        """
        Compare nexrad_data dimensions
        """

        pass


    def plot_filter(self, nexrad_data, dr_linear):

        #RadialPlotter(self, lats, lons, output_folder, grid_info)

        max_range = self.config['plot_settings']['max_range']

        grid_coords = bugtracker.core.utils.latlon(self.grid_info, self.metadata)
        lats = grid_coords['lats']
        lons = grid_coords['lons']

        base_folder = self.config['plot_dir']
        output_folder = os.path.join(base_folder, self.metadata.radar_id)

        print("dr_linear_shape:", dr_linear.shape)
        print("diff_reflect:", nexrad_data.diff_reflectivity.shape)
        print("cross:", nexrad_data.cross_correlation_ratio.shape)

        num_elevs = len(nexrad_data.dbz_elevs)

        for x in range(0, num_elevs):
            current_elev = nexrad_data.dbz_elevs[x]
            plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, output_folder, self.grid_info)
            plotter.set_data(dr_linear[x,:,:], f"{current_elev}_dr_linear", nexrad_data.datetime, self.metadata, max_range)
            plotter.save_plot(min_value=0.0, max_value=0.22)

            plotter.set_data(nexrad_data.diff_reflectivity[x,:,:], f"{current_elev}_diff_reflect", nexrad_data.datetime, self.metadata, max_range)
            plotter.save_plot(min_value=-5.0, max_value=10.0)

            plotter.set_data(nexrad_data.cross_correlation_ratio[x,:,:], f"{current_elev}_correlation", nexrad_data.datetime, self.metadata, max_range)
            plotter.save_plot(min_value=0.2, max_value=1.0)


    def subgrid_smoothing(self, source):

        azims = self.grid_info.azims
        gates = self.grid_info.gates
        elevs = source.shape[0]

        azim_subgrids = azims // 3
        gate_subgrids = gates // 3

        new_grid = np.zeros(source.shape, dtype=float)

        for z in range(0, elevs):
            for x in range(0, azim_subgrids):
                for y in range(0, gate_subgrids):
                    azim_start = 3 * x
                    azim_end = 3 * (x + 1)
                    gate_start = 3 * y
                    gate_end = 3 * (y + 1)
                    mean_value = source[z,azim_start:azim_end,gate_start:gate_end].mean()
                    new_grid[z,azim_start:azim_end,gate_start:gate_end] = mean_value
        
        # Filling final last bit
        new_grid[:,:,gate_subgrids*3:] = 1.0

        return new_grid


    def apply(self, nexrad_data):

        z_dr_log = self.subgrid_smoothing(nexrad_data.diff_reflectivity)
        rho_hv = self.subgrid_smoothing(nexrad_data.cross_correlation_ratio)

        """
        This cutoff comes from the equation DR(db) = 10*log10(DR_lin)
        from the paper: A Simple and Effective Method for Separating 
        Meteorological from Nonmeteorological Targets Using
        Dual-Polarization Data
        """

        #precip_cutoff = 0.0630957
        precip_cutoff = 0.07

        z_dr_lin = np.power(10.0, (0.1 * z_dr_log))
        z_offset = z_dr_lin + 1.0
        z_rhs = 2.0 * np.multiply(np.sqrt(z_dr_lin), rho_hv)

        numerator = z_offset - z_rhs
        denominator = z_offset + z_rhs

        dr_linear = np.divide(numerator, denominator)

        if dr_linear.shape != self.filter_3d.shape:
            raise ValueError("Incompatible filter dimensions")

        #self.plot_filter(nexrad_data, dr_linear)
        self.filter_3d = dr_linear < precip_cutoff


class PrecipFilter(Filter):

    def __init__(self, metadata, grid_info, angles):
        super().__init__(metadata, grid_info)

        self.setup(angles)
        self.config = bugtracker.config.load("./bugtracker.json")


    def verify_dims(self):
        
        if self.dbz_3d is None:
            raise ValueError("dbz_3d not set")

        if self.filter_3d is None:
            raise ValueError("filter_3d not set")

        dbz_shape = self.dbz_3d.shape
        filter_shape = self.dbz_3d.shape

        if len(dbz_shape) != 3 or len(filter_shape) != 3:
            raise ValueError("3D array expected.")

        if dbz_shape != filter_shape:
            raise ValueError(f"Incompatible numpy arrays: {dbz_shape}, {filter_shape}")

        num_angles = dbz_shape[0]
        num_azims = dbz_shape[1]
        num_gates = dbz_shape[2]

        if num_angles != len(self.vertical_angles):
            raise ValueError()

        if num_azims != self.grid_info.azims:
            raise ValueError(f"Incompatible azims: {azims}, {self.grid_info.azims}")


    def determine_zone_slope(self, dbz_3d, clutter, angles, azim_zone, gate_zone):
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
        height_list = []

        # Above this threshold, we consider it rain.
        max_dbz_per_km = -5.0

        for x in range(0, len(angles)):
            angle = angles[x]
            zone_data = dbz_3d[x,min_azim:max_azim,min_gate:max_gate]
            # Should be more OOP
            zone_clutter = clutter[x,min_azim:max_azim,min_gate:max_gate]
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
                    if not isinstance(dbz, np.ma.core.MaskedConstant):
                        angle_list.append(angle)
                        dbz_list.append(dbz)
                        # Making trig approximation h = x*tan(theta)
                        # Note, distance must be in km, and theta must
                        # be converted to radians.
                        # TODO: Use builtin pyart methods.
                        rad_angle = math.radians(angle)
                        # Using midpoint approximation
                        midpoint = int((min_gate + max_gate) / 2.0)
                        # Convert to kilometers
                        distance = midpoint * self.grid_info.gate_step * 0.001
                        height = distance * math.tan(rad_angle)
                        height_list.append(height)

        if len(angle_list) != len(dbz_list):
            raise ValueError("Zone slope error")

        # If there is only data from one elevation angle, we cannot
        # compute the slope.

        angle_set = set(angle_list)
        if len(angle_set) < 2:
            return np.nan
        else:
            slope, intercept, r_value, p_value, std_err = stats.linregress(height_list, dbz_list)
            return slope


    def apply(self, dbz, clutter, angles):
        """
        What creates a lot of confusion is:
        The precip filter is applied on a column-wide basis.
        """

        # First, check correspondence between dimensions

        if len(angles) != self.filter_3d.shape[0]:
            raise ValueError("Invalid number of angles")

        if dbz.shape != self.filter_3d.shape:
            raise ValueError("Input precipitation array has invalid dimensions.")

        if clutter.shape != self.filter_3d.shape:
            raise ValueError("Input clutter array has invalid dimensions.")

        t0 = time.time()

        azim_region = self.config['precip']['azim_region']
        gate_region = self.config['precip']['gate_region']
        max_slope = self.config['precip']['max_dbz_per_km']

        if self.grid_info.azims % azim_region != 0:
            raise ValueError(f"Choose value of azim_region that divides {self.grid_info.azims} evenly.")

        if self.grid_info.gates % gate_region != 0:
            raise ValueError(f"Choose value of gate_region that divides {self.grid_info.gates} evenly")

        azim_zones = self.grid_info.azims // azim_region
        gate_zones = self.grid_info.gates // gate_region

        for x in range(0, azim_zones):
            for y in range(0, gate_zones):
                slope = self.determine_zone_slope(dbz, clutter, angles, x, y)
                if not np.isnan(slope) and slope > max_slope:
                    min_azim = x * azim_region
                    max_azim = (x + 1) * azim_region

                    min_gate = y * gate_region
                    max_gate = (y + 1) * gate_region

                    self.filter_3d[:,min_azim:max_azim,min_gate:max_gate] = True

        t1 = time.time()
        print("Total time for precip filter:", t1 - t0)


    def copy(self, target_filter):
        """
        Copy the results from one precip filter into another.
        This is used for copying CONVOL filter into DOPVOL filters.
        """

        filter_shape = self.filter_3d.shape
        target_shape = target_filter.filter_3d.shape

        if filter_shape[0] < 1:
            raise ValueError("Invalid source angles")

        if filter_shape[1] != target_shape[1]:
            raise ValueError("Invalid number of azims")

        if filter_shape[2] != target_shape[2]:
            raise ValueError("Invalid number of range gates")

        first_level = self.filter_3d[0,:,:]
        num_target_levels = target_shape[0]

        for x in range(0, num_target_levels):
            target_filter.filter_3d[x,:,:] = first_level[:,:]