import os
import glob
import sys
import datetime

import numpy as np
import pyart

import bugtracker
from bugtracker.plots.alignment import AlignmentPlotter


def dt_from_odim(odim_filename):

    base = os.path.basename(odim_filename)
    base_list = base.split("_")
    dt = datetime.datetime.strptime(base_list[0], "%Y%m%d%H%M")
    return dt


def plot_all():

    radar_id = "cascm"
    config = bugtracker.config.load("./bugtracker.json")

    odim_dir = os.path.join(config['input_dirs']['odim'], radar_id)
    odim_files = glob.glob(os.path.join(odim_dir, "*.h5"))
    odim_files.sort()

    output_folder = "/storage/spruce/plot_output/alignment"
    plotter = AlignmentPlotter(output_folder)

    for filename in odim_files:
        print(f"Plotting {filename}")
        radar_handle = pyart.aux_io.read_odim_h5(filename)
        scan_dt = dt_from_odim(filename)
        plotter.set_data(radar_handle, radar_id)
        plotter.save_plot(scan_dt)

plot_all()