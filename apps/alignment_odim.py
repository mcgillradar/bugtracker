import os
import datetime

import pyart
import bugtracker


def plot_alignment(radar_id, scan_dt):

    config = bugtracker.config.load("./bugtracker.json")
    output_folder = os.path.join(config['plot_dir'], "alignment")

    plotter = bugtracker.plots.alignment.AlignmentPlotter(output_folder)

    odim_manager = bugtracker.io.odim.OdimManager(config, radar_id)
    odim_manager.populate(scan_dt)
    odim_filename = odim_manager.get_closest(scan_dt)
    odim_data = odim_manager.extract_data(odim_filename)

    plotter.set_data(odim_data.handle, radar_id)

    plotter.save_plot(scan_dt)

    print("Output shape:", odim_data.dbz_unfiltered.shape)


def main():

    """
    radar_list = ["casbe", "casbv", "cascm", "caset",
                  "casfw", "casla", "casmb", "casra",
                  "casrf", "cassm", "cassr"]
    """

    radar_list = ["casbv"]

    scan_dt = datetime.datetime(2020, 2, 19, 16, 30)

    for radar_id in radar_list:
        print("Plotting:", radar_id)
        plot_alignment(radar_id, scan_dt)


main()