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

import os
import datetime

import numpy as np
import matplotlib.pyplot as plt
import pyart

import bugtracker.io.iris
import bugtracker.core.grid
import bugtracker.config
import bugtracker.plots.dbz
import bugtracker.core.metadata
import bugtracker.core.exceptions


def iris_grid():

    gates = 256 * 2
    azims = 720
    gate_step = 500.0
    azim_step = 0.5

    grid_info = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step)
    return grid_info


class IrisData:

    def __init__(self, iris_set):
        """
        Extract numpy arrays for easy file manipulation
        """

        self._iris_set = iris_set

        self.metadata = bugtracker.core.metadata.from_iris_set(iris_set)
        self.datetime = iris_set.datetime
        self.config = bugtracker.config.load('./bugtracker.json')
        self.convol_scans = self.config["iris_settings"]["convol_scans"]
        self.dopvol_scans = 3 

        self.grid = iris_grid()

        # Somehow get azimuthal angle programmatically from scan info
        # Elevations go from lowest to highest, using convention (-90.0, 90.0)
        self.convol_elevs = iris_set.get_elevs("convol")
        self.dopvol_elevs = iris_set.get_elevs("dopvol")

        azims = self.grid.azims
        gates = self.grid.gates

        convol_dims = (self.convol_scans, azims, gates)
        dopvol_dims = (self.dopvol_scans, azims, gates)

        print("CONVOL_dims", convol_dims)
        print("DOPVOL_dims", dopvol_dims)

        self.convol = np.ma.zeros(convol_dims, dtype=float)
        self.dopvol = np.ma.zeros(dopvol_dims, dtype=float)

        self.total_power = np.ma.zeros(dopvol_dims, dtype=float)
        self.velocity = np.ma.zeros(dopvol_dims, dtype=float)
        self.spectrum_width = np.ma.zeros(dopvol_dims, dtype=float)


    def fill_convol(self):
        """
        Filling convol levels
        """

        convol_raw = bugtracker.io.iris.extract_dbz(self._iris_set.convol)

        convol_levels = []
        # TODO: Get from file
        convol_azims = 360

        for x in range(0, self.convol_scans):
            start = (24 - 1 - x) * convol_azims
            end = (24 - x) * convol_azims
            convol_array = convol_raw[start:end,:]
            convol_levels.append(convol_array)

        if len(convol_levels) != self.convol_scans:
            raise ValueError("Convol scans:", len(convol_scans))

        for z in range(0, self.convol_scans):
            for x in range(0, self.grid.azims):
                azim_idx = int(x) // 2
                for y in range(0, self.grid.gates):
                    gate_idx = int(y) // 2
                    self.convol[z, x, y] = convol_levels[z][azim_idx, gate_idx]


    def fill_dopvol_short(self, scan, np_array, field_key, idx):

        dopvol_short_azims = 720
        dopvol_short_range = 225

        short_field = scan.fields[field_key]['data']
        short_field_shape = short_field.shape

        if (short_field_shape[0] != dopvol_short_azims
            or short_field_shape[1] != dopvol_short_range):
            raise ValueError("Shape error", short_field_shape)

        np_array[idx,0:dopvol_short_azims,0:dopvol_short_range] = short_field[:,:]
        np_array.mask[idx,:,dopvol_short_range:] = True


    def fill_dopvol_long(self, scan, np_array, field_key, idx):

        long_field = scan.fields[field_key]['data']
        long_field_shape = long_field.shape

        dopvol_2_gates = long_field_shape[1]
        dopvol_long_range = dopvol_2_gates * 2

        for x in range(0, self.grid.azims):
            azim_idx = int(x) // 2
            for y in range(0, dopvol_long_range):
                gate_idx = int(y) // 2
                np_array[idx, x, y] = long_field[azim_idx, gate_idx]

        np_array.mask[idx,:,dopvol_long_range:] = True


    def fill_dopvol_field(self, scan, np_array, field_key, idx, scan_type):
        
        scan_type = scan_type.strip().lower()

        if scan_type == "short":
            self.fill_dopvol_short(scan, np_array, field_key, idx)
        elif scan_type == "long":
            self.fill_dopvol_long(scan, np_array, field_key, idx)
        else:
            raise ValueError(f"Invalid scan_type: {scan_type}")


    def fill_dopvol_file(self, iris_file, idx, scan_type):
        
        scan = pyart.io.read_sigmet(iris_file)

        self.fill_dopvol_field(scan, self.dopvol, "reflectivity", idx, scan_type)
        self.fill_dopvol_field(scan, self.total_power, "total_power", idx, scan_type)
        self.fill_dopvol_field(scan, self.velocity, "velocity", idx, scan_type)
        self.fill_dopvol_field(scan, self.spectrum_width, "spectrum_width", idx, scan_type)


    def fill_grids(self):
        """
        Fill grids according to 720x512 regularization
        0.5 deg x 0.5 km bins are the standard
        """

        self.fill_convol()
        self.fill_dopvol_file(self._iris_set.dopvol_1A, 0, "short")
        self.fill_dopvol_file(self._iris_set.dopvol_1B, 1, "short")
        self.fill_dopvol_file(self._iris_set.dopvol_2, 2, "long")


    def plot_level(self, dbz_array, output_folder, label, max_range):
        # This should be decoupled and in the 'plots' module

        # Create radar
        radar_data = self.grid.create_radar(self.datetime, dbz_array, self.metadata)

        display = pyart.graph.RadarDisplay(radar_data)
        range_rings = []
        current = 25.0
        while current <= max_range:
            range_rings.append(current)
            current += 25.0

        x_limits = (-1.0 * max_range, max_range)
        y_limits = (-1.0 * max_range, max_range)
        print("limits:", x_limits, y_limits)
        print("Max range:", max_range)

        display.set_limits(xlim=x_limits, ylim=y_limits)
        display.plot_range_rings(range_rings)
        display.plot('dbz')
        plot_filename = os.path.join(output_folder, label + '.png')
        plt.savefig(plot_filename)
        plt.close()


    def plot_all_levels(self, output_folder, max_range):
        """
        Create radar objects for each
        """

        # CONVOL scans first
        for x in range(self.convol_scans):
            dbz_array = self.convol[x,:,:]
            convol_elev = self.convol_elevs[x]
            label = f"convol_{x}_elev_{convol_elev}"
            self.plot_level(dbz_array, output_folder, label, max_range)

        # DOPVOL scans
        dbz_dopvol_1A = self.dopvol[0,:,:]
        dopvol_elev_1A = self.dopvol_elevs[0]
        label_1A = f"dopvol_short_elev_{dopvol_elev_1A}"
        self.plot_level(dbz_dopvol_1A, output_folder, label_1A, max_range)

        dbz_dopvol_1B = self.dopvol[1,:,:]
        dopvol_elev_1B = self.dopvol_elevs[1]
        label_1B = f"dopvol_short_elev_{dopvol_elev_1B}"
        self.plot_level(dbz_dopvol_1B, output_folder, label_1B, max_range)

        dbz_dopvol_2 = self.dopvol[2,:,:]
        dopvol_elev_2 = self.dopvol_elevs[2]
        label_2 = f"dopvol_long_elev_{dopvol_elev_2}"
        self.plot_level(dbz_dopvol_2, output_folder, label_2, max_range)


    def check_grids(self, c_shape, d_shape):
        """
        Checking compatibility of CONVOL and DOPVOL grids
        """

        if c_shape[1] != self.grid.azims:
            raise ValueError("Inconsistent azims")

        if c_shape[2] != self.grid.gates:
            raise ValueError("Inconsistent gates")

        if len(c_shape) != 3 or len(d_shape) != 3:
            raise ValueError("Grids have incorrect dimensions.")

        if c_shape[1] != d_shape[1] or c_shape[2] != d_shape[2]:
            raise ValueError("Incompatible convol/dopvol dims.")


    def level_indices(self, unique_levels, all_elevs):

        idx_dict = dict()

        num_total_levels = len(all_elevs)

        for x in range(0, num_total_levels):
            elev = all_elevs[x]
            if elev not in idx_dict:
                idx_dict[elev] = [x]
            else:
                idx_dict[elev].append(x)

        return idx_dict


    def merge_subarray(self, all_dbz, idx_list):

        sub_array_dims = (len(idx_list), self.grid.azims, self.grid.gates)
        sub_array = np.ma.zeros(sub_array_dims, dtype=float)

        for x in range(0, len(idx_list)):
            idx = idx_list[x]
            sub_array[x,:,:] = all_dbz[idx,:,:]

        return np.average(sub_array, axis=0)


    def combine_all(self, all_dbz, level_indices, unique_levels):

        num_unique = len(unique_levels)
        dbz_dims = (num_unique, self.grid.azims, self.grid.gates)
        dbz_merged = np.ma.zeros(dbz_dims, dtype=float)

        for x in range(0, num_unique):
            unique_level = unique_levels[x]
            level_idx_list = level_indices[unique_level]
            if len(level_idx_list) == 0:
                raise ValueError("Empty index")
            elif len(level_idx_list) == 1:
                current_idx = level_idx_list[0]
                dbz_merged[x,:,:] = all_dbz[current_idx,:,:]
            else:
                merged_level = self.merge_subarray(all_dbz, level_idx_list)
                dbz_merged[x,:,:] = merged_level[:,:]

        return dbz_merged


    def merge_dbz(self):
        """
        Merge dopvol and convol together
        """

        c_shape = self.convol.shape
        d_shape = self.dopvol.shape

        self.check_grids(c_shape, d_shape)

        convol_levels = c_shape[0]
        dopvol_levels = d_shape[0]
        all_levels = convol_levels + dopvol_levels
        all_elevs = self.convol_elevs + self.dopvol_elevs
        all_dims = (all_levels, self.grid.azims, self.grid.gates)

        # Combining DOPVOL and CONVOL into one big array
        all_dbz = np.ma.zeros(all_dims, dtype=float)
        all_dbz[0:convol_levels,:,:] = self.convol[:,:,:]
        all_dbz[convol_levels:,:,:] = self.dopvol[:,:,:]

        unique_levels = list(set(all_elevs))
        unique_levels.sort()

        level_indices = self.level_indices(unique_levels, all_elevs)
        
        dbz_merged = self.combine_all(all_dbz, level_indices, unique_levels)
        self.dbz_elevs = unique_levels

        return dbz_merged


    def merge_dopvol_field(self, field_type):
        """
        First, we need to get DOPVOL_1A, DOPVOL1B
        and DOPVOL_2 on the same grid.

        Second step, is to check that fixed_angle for DOPVOL_1A
        < DOPVOL_1B. If not, a basic assumption is violated and
        an exception must be raised.
        
        The following code normalizes the Iris DOPVOL grids to
        one uniform grid. I have noticed that the elevation angles
        of the various DOPVOL scans can be quite variable, depending
        on which Canadian radar is chosen. Therefore I have written
        code that handles all possible cases.

        Direct enumeration of cases:
        1. DOPVOL_2 < DOPVOL_1A
            i) Create [3,azims,gates] array
            ii) Populate [DOPVOL_2, DOPVOL_1A, DOPVOL_1B]
        2. DOPVOL_2 == DOPVOL_1A
            i) Create [2,azims,gates] array 
            ii) Merge DOPVOL_2 and DOPVOL_1A
            iii) Populate [JOINT, DOPVOL_1B]
        3. DOPVOL_1A < DOPVOL_2 < DOPVOL_1B
            i) Create [3,azims,gates] array
            ii) Populate [DOPVOL_1, DOPVOL_2, DOPVOL_1B]
        4. DOPVOL_2 == DOPVOL_1B
            raise IrisIOException
        5. DOPVOL_2 > DOPVOL_1B
            raise IrisIoException

        Case 4 and 5 are unusual, and for the moment, I will
        throw an IrisIOException
        """

        dopvol_levels = self._iris_set.get_elevs("dopvol")

        if len(dopvol_levels) != 3:
            raise ValueError("Should be exactly 3 DOPVOL levels")

        angle_1A, angle_1B, angle_2 = dopvol_levels
        dopvol_set = set(dopvol_levels)
        num_angles = len(dopvol_set)

        if angle_1B <= angle_1A:
            raise bugtracker.core.exceptions.IrisIOException("Angle 1B cannot be lower than 1A")

        azims = self.grid.azims
        gates = self.grid.gates
        dims = (num_angles, azims, gates)

        dopvol_field = np.ma.zeros(dims, dtype=float)

        field_1A = self.pyart_dopvol_1A.fields[field_type]['data']
        field_1B = self.pyart_dopvol_1B.fields[field_type]['data']
        field_2 = self.pyart_dopvol_2.fields[field_type]['data']

        if angle_1A > angle_2:
            # Case 1
            dopvol_field[0,:,:] = field_2[:,:]
            dopvol_field[1,:,:] = field_1A[:,:]
            dopvol_field[2,:,:] = field_1B[:,:]
        elif angle_1A == angle_2:
            # Case 2
            dopvol_field[0,:,:] = merge_2d(field_2, field_1A)
            dopvol_field[1,:,:] = field_1B[:,:]
        elif angle_1A < angle_2 < angle_1B:
            # Case 3
            dopvol_field[0,:,:] = field_1A[:,:]
            dopvol_field[1,:,:] = field_2[:,:]
            dopvol_field[2,:,:] = field_1B[:,:]
        else:
            raise bugtracker.core.exceptions.IrisIOException("Unexpected case in Iris scan angles.")
        
        return dopvol_field

