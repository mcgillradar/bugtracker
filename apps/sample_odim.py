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

import pyart
import bugtracker


def plot_sample(radar_id, scan_dt):

    config = bugtracker.config.load("./bugtracker.json")
    output_folder = os.path.join(config['plot_dir'], "tests")

    odim_manager = bugtracker.io.odim.OdimManager(config, radar_id)
    odim_manager.populate(scan_dt)
    odim_filename = odim_manager.get_closest(scan_dt)
    odim_data = odim_manager.extract_data(odim_filename)

    metadata = odim_manager.metadata
    grid_info = odim_manager.grid_info

    grid_coords = bugtracker.core.utils.latlon(grid_info, metadata)
    lats = grid_coords['lats']
    lons = grid_coords['lons']

    plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, output_folder, grid_info)

    elevs = odim_data.dbz_elevs

    for x in range(0, len(elevs)):
        current_elev = elevs[x]
        plotter.set_data(odim_data.dbz_unfiltered[x,:,:], f"dbz_{current_elev:2f}", scan_dt, metadata, 200.0)
        plotter.save_plot(min_value=-30, max_value=50.0)

    print("Output shape:", odim_data.dbz_unfiltered.shape)


def main():

    """
    radar_list = ["casbe", "casbv", "cascm", "caset",
                  "casfw", "casla", "casmb", "casra",
                  "casrf", "cassm", "cassr"]
    """

    radar_id = "casbv"
    scan_dt = datetime.datetime(2020, 2, 19, 16, 30)

    plot_sample(radar_id, scan_dt)


main()