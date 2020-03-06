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
Plotting a TargetID array
"""

import os
import glob
import datetime

import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors
import geopy
import geopy.distance
import netCDF4 as nc

import bugtracker.core.utils
from bugtracker.plots.radial import RadialPlotter


class TargetIdPlotter(RadialPlotter):

    def __init__(self, lats, lons, output_folder, grid_info):

        super().__init__(lats, lons, output_folder, grid_info)


    def _plot_target_id(self):

        self.data = np.ma.masked_where(self.data == 0, self.data)

        colors = ['red', 'blue', 'green']
        cmap = matplotlib.colors.ListedColormap(colors)

        plt.pcolormesh(self.lons, self.lats, self.data, vmin=1.0, vmax=3.0, cmap=cmap)
        cb = plt.colorbar()

        # This will need to be modified if more categories are added.
        cb.set_ticks([1 + 1/3, 2.0, 3 - 1/3])
        cb.set_ticklabels(['clutter','rain','bugs'])


    def save_plot(self):


        self._fill_wedge()
        self._set_range()

        aspect = self.calculate_aspect()
        self.ax = plt.axes(projection=ccrs.PlateCarree(), aspect=aspect)
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')

        self._set_grid()
        self._plot_target_id()
        self._add_features()
        self._set_cross()
        self._set_circles()

        plt.title(self._get_title(self.label, self.plot_datetime))
        self.ax.set_extent(self.range)

        plot_filename = self.plot_datetime.strftime("%Y%m%d%H%M") + "_" + self.label + ".png"
        output_file = os.path.join(self.output_folder, plot_filename)

        plt.savefig(output_file, dpi=200)
        plt.gcf().clear()