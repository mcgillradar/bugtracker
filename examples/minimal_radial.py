"""
As of v1.5.1, I noticed a bug present on Linux, which results in the
following deprecation warning.

/home/dhogg/miniconda3/envs/bugtracker/lib/python3.7/site-packages/cartopy/mpl/geoaxes.py:782: MatplotlibDeprecationWarning: Passing the minor parameter of set_xticks() positionally is deprecated since Matplotlib 3.2; the parameter will become keyword-only two minor releases later.
  return super(GeoAxes, self).set_xticks(xticks, minor)

This script is my attempt to reproduce the bug in a self-contained
way.
"""

import os
import glob
import datetime

import numpy as np

import bugtracker


def sample_plot():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    template_date = "202002190300"
    sample_date = "202002191630"
    fmt = "%Y%m%d%H%M"

    template_dt = datetime.datetime.strptime(template_date, fmt)
    sample_dt = datetime.datetime.strptime(sample_date, fmt)

    radar_id = "casbv"
    manager = bugtracker.io.odim.OdimManager(config, radar_id)
    manager.populate(template_dt)

    odim_file = manager.get_closest(sample_dt)
    odim_data = manager.extract_data(odim_file)

    plot_dir = os.path.join(config['plot_dir'], "test")
    grid_coords = bugtracker.core.utils.latlon(manager.grid_info, manager.metadata)

    lats = grid_coords['lats']
    lons = grid_coords['lons']

    zero_data = np.zeros(lats.shape, dtype=float)

    plotter = bugtracker.plots.radial.RadialPlotter(lats, lons, plot_dir, manager.grid_info)
    plotter.set_data(zero_data, "zeros", datetime.datetime.utcnow(), manager.metadata, 150.0)
    plotter.save_plot(min_value=-5.0, max_value=40.0)


sample_plot()