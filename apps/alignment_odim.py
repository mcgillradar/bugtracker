import os
import datetime

import pyart
import bugtracker


def main():

    config = bugtracker.config.load("./bugtracker.json")

    radar_id = "casvb"
    output_folder = os.path.join(config['plot_dir'], "alignment")

    plotter = bugtracker.plots.alignment.AlignmentPlotter(output_folder)
    odim_data = bugtracker.core.samples.odim_sample(config)

    plotter.set_data(odim_data.handle, radar_id)

    scan_dt = datetime.datetime(2020, 2, 19, 16)
    plotter.save_plot(scan_dt)

main()