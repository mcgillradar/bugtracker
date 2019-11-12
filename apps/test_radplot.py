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