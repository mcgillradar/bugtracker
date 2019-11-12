"""
A simple plotting interface that is to be used
for debug use only, as it does not include terrain
and borders.
"""

import os


import matplotlib
import matplotlib.pyplot as plt
import pyart

matplotlib.use('Agg')

import bugtracker.io.iris



def plot_synthetic(radar, output_folder, range):
    pass


def debug_plot(scan_dt, radar, output_folder, args):

    dbz_key = bugtracker.io.iris.get_dbz_key(radar)
    scan_type = bugtracker.io.iris.get_scan_type(radar)

    range_array = radar.range['data']
    azim_array = radar.azimuth['data']
    num_gates = len(range_array)
    num_azims = len(azim_array)
    print("************************************")
    print(f"First gate {range_array[0]}m")
    print(f"Second gate {range_array[1]}m")
    print(f"Last gate {range_array[num_gates-1]}m")
    print(f"First azim {azim_array[0]}")
    print(f"Last azim {azim_array[num_azims-1]}")

    print("Reflectivity size:", radar.fields[dbz_key]['data'].shape)

    display = pyart.graph.RadarDisplay(radar)
    range_rings = []
    current = 25.0
    while current <= args.range:
        range_rings.append(current)
        current += 25.0

    x_limits = (-1.0 * args.range, args.range)
    y_limits = (-1.0 * args.range, args.range)


    if scan_type == 'convol':
        for x in range(0,24):
            display.set_limits(xlim=x_limits, ylim=y_limits)
            display.plot_range_rings(range_rings)
            display.plot(dbz_key, x)
            plt.savefig(os.path.join(output_folder, scan_type + "_" + str(x) + "_scan.png"))
            plt.close()
    else:
        display.set_limits(xlim=x_limits, ylim=y_limits)
        display.plot_range_rings(range_rings)
        display.plot(dbz_key)
        plt.savefig(os.path.join(output_folder, scan_type + "_scan.png"))
        plt.close()



    # Output dir should not be hard-coded, should instead come
    # from config file.