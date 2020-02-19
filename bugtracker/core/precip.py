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

import bugtracker.core.utils
from bugtracker.core.filter import Filter
import bugtracker.plots.radial


class IrisPrecipFilter(Filter):

    def __init__(self, metadata, grid_info, angles):

        super().__init__(metadata, grid_info)
        self.setup(angles)
        self.config = bugtracker.load("./bugtracker.json")


class NexradPrecipFilter(Filter):

    def __init__(self, metadata, grid_info, angles):

        super().__init__(metadata, grid_info)
        self.setup(angles)
        self.config = bugtracker.config.load("./bugtracker.json")


    def verify_dims(self):
        """
        Compare nexrad_data dimensions
        """

        pass


    def plot_filter(self, dr_linear, plot_datetime):

        #RadialPlotter(self, lats, lons, output_folder, grid_info)

        grid_coords = bugtracker.core.utils.latlon(self.grid_info, self.metadata)
        lats = grid_coords['lats']
        lons = grid_coords['lons']

        base_folder = self.config['plot_dir']
        output_folder = os.path.join(base_folder, self.metadata.radar_id)

        plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, output_folder, self.grid_info)
        plotter.set_data(dr_linear, "dr_linear", plot_datetime, self.metadata, 150.0)
        plotter.save_plot(min_value=-1.0, max_value=1.0)


    def apply(self, nexrad_data):

        z_dr = nexrad_data.diff_reflectivity
        rho_hv = nexrad_data.cross_correlation_ratio

        """
        This cutoff comes from the equation DR(db) = 10*log10(DR_lin)
        from the paper: A Simple and Effective Method for Separating 
        Meteorological from Nonmeteorological Targets Using
        Dual-Polarization Data
        """
        precip_cutoff = 0.0630957

        z_offset = z_dr + 1.0
        z_rhs = 2.0 * np.multiply(np.sqrt(z_dr), rho_hv)

        numerator = z_offset - z_rhs
        denominator = z_offset + z_rhs

        dr_linear = np.divide(numerator, denominator)

        if dr_linear.shape != self.filter_3d.shape:
            raise ValueError("Incompatible filter dimensions")

        self.plot_filter(dr_linear, nexrad_data.datetime)
        self.filter_3d = dr_linear < precip_cutoff

        bugtracker.core.utils.arr_info(dr_linear, "dr_linear")


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
        max_slope = self.config['precip']['max_dbz_per_degree']

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
