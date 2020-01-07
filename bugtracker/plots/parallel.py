import os
import time
import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np

import bugtracker.config
from bugtracker.plots.radial import RadialPlotter
from bugtracker.plots.identify import TargetIdPlotter

"""
Multiprocessing optimization:
-----------------------------
Given that Matplotlib is single-threaded, I am making the
design choice to have each plot on a single thread, but many
plots will be created at the same time, to minimize runtime
and maximize CPU usage.
"""


def get_plotter(metadata, config, lats, lons, plot_type):
    """
    Activate the RadialPlotter. This code may need to be significantly
    modified if we need to do parallel plotting (multi-cpu to speed up
    the plotting of a large set of files).
    """

    radar_id = metadata.radar_id
    plot_dir = config['plot_dir']
    output_folder = os.path.join(plot_dir, radar_id)

    if not os.path.isdir(plot_dir):
        FileNotFoundError(f"This folder should have been created {plot_dir}")

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    if plot_type == 'target_id':
        return TargetIdPlotter(lats, lons, output_folder)
    else:
        return RadialPlotter(lats, lons, output_folder)


def plot_worker(plot_type, metadata, config, lats, lons, dbz_idx, iris_data, id_matrix):

    plot_type = plot_type.lower().strip()
    plotter = get_plotter(metadata, config, lats, lons, plot_type)


    if plot_type == 'filtered':
        plot_level(plotter, metadata, config, iris_data, dbz_idx, filtered=True)
    elif plot_type == 'unfiltered':
        print(plot_type)
    elif plot_type == 'joint':
        print(plot_type)
    elif plot_type == 'target_id':
        print(plot_type)
    else:
       raise ValueError(f"Unrecognizable plot type: {plot_type}")



def plot_level(plotter, metadata, config, iris_data, dbz_idx, filtered=True):
    """
    Plot every level of the dbz output
    """

    max_range = config["plot_settings"]["max_range"]
    num_elevs = len(iris_data.dbz_elevs)
    print("angles:", iris_data.dbz_elevs)

    prefix = None
    dbz_field = None
    if filtered:
        prefix = "filtered"
        dbz_field = iris_data.dbz_filtered
    else:
        prefix = "unfiltered"
        dbz_field = iris_data.dbz_unfiltered

    elev = iris_data.dbz_elevs[dbz_idx]
    data = dbz_field[dbz_idx,:,:]
    label = f"{prefix}_angle_{elev:.1f}"
    print(f"Plotting: {label}")

    plotter.set_data(data, label, iris_data.datetime, metadata, max_range)
    plotter.save_plot(min_value=-15.0, max_value=40.0)


class ParallelPlotter:
    """
    multiprocessing.Pool based class that allows mupliple plots to
    happen at the same time.
    """

    def __init__(self, lats, lons, metadata, iris_data, id_matrix):

        self.config = bugtracker.config.load("./bugtracker.json")
        self.lats = lats
        self.lons = lons
        self.metadata = metadata
        self.iris_data = iris_data
        self.id_matrix = id_matrix

        dbz_elevs = iris_data.dbz_elevs
        num_elevs = len(dbz_elevs)

        args = []

        for idx in range(0, num_elevs):
            plot_type = "filtered"
            arglist = (plot_type, metadata, self.config, lats, lons, idx, iris_data, id_matrix)
            args.append(arglist)


        self.pool = mp.Pool()
        self.pool.starmap(plot_worker, args)





    def plot_joint_product(self, plotter):

        max_range = self.config["plot_settings"]["max_range"]

        data = iris_data.joint_product[:,:]
        label = f"joint_product"
        print(f"Plotting: {label}")
        self.plotter.set_data(data, label, iris_data.datetime, self.metadata, max_range)
        self.plotter.save_plot(min_value=-15.0, max_value=40.0)


    def plot_target_id(self, plotter):
        """
        Creating TargetIdPlotter from RadialPlotter
        """

        lats = self.plotter.lats
        lons = self.plotter.lons
        output_folder = self.plotter.output_folder

        id_plotter = bugtracker.plots.identify.TargetIdPlotter(lats, lons, output_folder)

        max_range = self.config["plot_settings"]["max_range"]

        prefix = "target_id"
        dbz_elevs = iris_data.dbz_elevs
        num_dbz_elevs = len(dbz_elevs)

        for x in range(0, num_dbz_elevs):
            elev = dbz_elevs[x]
            data = id_matrix[x,:,:]
            label = f"{prefix}_angle_{elev:.1f}"
            print(f"Plotting: {label}")
            id_plotter.set_data(data, label, iris_data.datetime, self.metadata, max_range)
            id_plotter.save_plot()


