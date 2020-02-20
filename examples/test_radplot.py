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
import pyart

import bugtracker


def main():
    
    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    data = bugtracker.core.samples.sin_dbz(grid_info)
    grid_coords = bugtracker.core.utils.latlon(grid_info, metadata)
    lats = grid_coords['lats']
    lons = grid_coords['lons']

    plot_name = "synthetic_map.png"
    plot_folder = "/storage/spruce/plot_output/tests"

    plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, plot_folder)

    dt = datetime.datetime.utcnow()

    plotter.set_data(data, 'test_stuff', dt, metadata, 150.0)
    plotter.save_plot(plot_name)


main()