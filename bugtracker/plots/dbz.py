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
import datetime

import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pyart


matplotlib.use('Agg')

import bugtracker.core.grid

def plot_dbz(dbz_array, radar_dt, output_folder, label, max_range, metadata):
    # This should be decoupled and in the 'plots' module

    # Create radar (hardcoded)
    dbz_grid = bugtracker.core.grid.GridInfo(512, 720, 500.0, 0.5)

    radar_data = dbz_grid.create_radar(radar_dt, dbz_array, metadata)

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


def map(dbz_array, radar_dt, output_folder, label, max_range, metadata):
    # This should be decoupled and in the 'plots' module

    # Create radar (hardcoded)
    dbz_grid = bugtracker.core.grid.GridInfo(512, 720, 500.0, 0.5)

    radar_data = dbz_grid.create_radar(radar_dt, dbz_array, metadata)

    proj=ccrs.PlateCarree()

    display = pyart.graph.RadarMapDisplay(radar_data, grid_projection=proj)
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