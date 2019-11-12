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


class IrisProcessor:

    def __init__(self, iris_data, calib_data, output_folder):

        self.iris_data = iris_data
        self.output_folder = output_folder
        self.calib_data = calib_data


    def execute(self):

        maximum_vals = self.iris_data.dopvol.max(axis=0)
        print("OUTPUT SHAPE:", maximum_vals.shape)

        # Now, filter out > 30 dBZ

        filtered = np.ma.masked_where(maximum_vals > 30.0, maximum_vals)

        return filtered


    def plot(self, bug_dbz, max_range):

        label = "final_dbz"
        bugtracker.plots.dbz.plot_dbz(bug_dbz, self.iris_data.datetime,
                                      self.output_folder, label, max_range, self.iris_data.metadata)



class IrisData:

    def __init__(self, iris_set):
        """
        Extract numpy arrays for easy file manipulation
        """

        self.metadata = bugtracker.core.metadata.from_iris_set(iris_set)
        self.datetime = iris_set.datetime
        self.config = bugtracker.config.load('./bugtracker.json')
        self.convol_scans = self.config["iris_convol_scans"]
        self.dopvol_scans = 3 

        gates = 256 * 2
        azims = 720
        gate_step = 500.0
        azim_step = 0.5

        self.grid = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step)
        
        self.convol_raw = bugtracker.io.iris.extract_dbz(iris_set.convol)
        self.dopvol_1A_raw = bugtracker.io.iris.extract_dbz(iris_set.dopvol_1A)
        self.dopvol_1B_raw = bugtracker.io.iris.extract_dbz(iris_set.dopvol_1B)
        self.dopvol_2_raw = bugtracker.io.iris.extract_dbz(iris_set.dopvol_2)

        self.convol = np.ma.zeros((self.convol_scans, azims, gates), dtype=float)
        self.dopvol = np.ma.zeros((self.dopvol_scans, azims, gates), dtype=float)

        # Somehow get azimuthal angle programmatically from scan info
        # Elevations go from lowest to highest, using convention (-90.0, 90.0)
        self.convol_elevs = iris_set.get_elevs("convol")
        self.dopvol_elevs = iris_set.get_elevs("dopvol")


    def print_sizes(self):

        print("CONVOL:", self.convol_raw.shape)
        print("DOPVOL_1A:", self.dopvol_1A_raw.shape)
        print("DOPVOL_1B:", self.dopvol_1B_raw.shape)
        print("DOPVOL_2:", self.dopvol_2_raw.shape)

        print("convol 3D:", self.convol.shape)
        print("dopvol 3D:", self.dopvol.shape)


    def fill_grids(self):

        # Fill CONVOL

        convol_levels = []
        # TODO: Get from file
        convol_azims = 360

        for x in range(0, self.convol_scans):
            start = (24 - 1 - x) * convol_azims
            end = (24 - x) * convol_azims
            convol_array = self.convol_raw[start:end,:]
            convol_levels.append(convol_array)

        if len(convol_levels) != self.convol_scans:
            raise ValueError("Convol scans:", len(convol_scans))

        for z in range(0, self.convol_scans):
            for x in range(0, self.grid.azims):
                azim_idx = int(x) // 2
                for y in range(0, self.grid.gates):
                    gate_idx = int(y) // 2
                    self.convol[z, x, y] = convol_levels[z][azim_idx, gate_idx]

        print("*************************")
        print("Convol scan type:", type(self.convol))
        print("Dopvol scan type:", type(self.dopvol))

        # Filling in DOPVOL_1A and DOPVOL_1B

        # TODO: Don't hardcore these
        dopvol_short_azims = 720
        dopvol_short_range = 225

        if (self.dopvol_1A_raw.shape[0] != dopvol_short_azims
            or self.dopvol_1A_raw.shape[1] != dopvol_short_range):
            raise ValueError("Shape error", self.dopvol_1A_raw.shape)

        if (self.dopvol_1B_raw.shape[0] != dopvol_short_azims
            or self.dopvol_1B_raw.shape[1] != dopvol_short_range):
            raise ValueError("Shape error". self.dopvol_1B_raw.shape)

        self.dopvol[0,0:dopvol_short_azims,0:dopvol_short_range] = self.dopvol_1A_raw[:,:]
        self.dopvol[1,0:dopvol_short_azims,0:dopvol_short_range] = self.dopvol_1B_raw[:,:]

        self.dopvol.mask[0,:,dopvol_short_range:] = True
        self.dopvol.mask[1,:,dopvol_short_range:] = True

        # Filling in DOPVOL_2 (long range)

        dopvol_2_gates = self.dopvol_2_raw.shape[1]
        dopvol_long_range = dopvol_2_gates * 2

        for x in range(0, self.grid.azims):
            azim_idx = int(x) // 2
            for y in range(0, dopvol_long_range):
                gate_idx = int(y) // 2
                self.dopvol[2, x, y] = self.dopvol_2_raw[azim_idx, gate_idx]

        self.dopvol.mask[2,:,dopvol_long_range:] = True


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

