

import os
import datetime

import numpy as np
import pyart

import bugtracker
from bugtracker.plots.alignment import AlignmentPlotter


def find_closest_idx(angles, current_angle):

    idx = -1
    min_diff = 9999.0

    num_angles = len(angles)
    for x in range(0, num_angles):
        diff = abs(angles[x] - current_angle)
        if diff < min_diff:
            min_diff = diff
            idx = x

    return idx


def group_angles(filename):

    art = pyart.io.read(filename)
    angles = art.fixed_angle['data']
    num_angles = len(angles)

    # inefficient

    counter_dict = dict()
    for x in range(0, num_angles):
        counter_dict[x] = 0

    num_azims = len(art.azimuth['data'])

    for x in range(0, num_azims):
        if x % 360 == 0:
            print(f"{x}: {art.azimuth['data'][x]}")
        current_angle = art.elevation['data'][x]
        idx = find_closest_idx(angles, current_angle)
        counter_dict[idx] += 1

    for x in range(0, num_angles):
        print(f"{x}, {angles[x]}: {counter_dict[x]}")

    print(art.range)
    print(len(art.range['data']))


def load_one(filename):

    art = pyart.io.read(filename)

    fields = art.fields

    for key in fields:
        print(key)
        print(fields[key]['data'].shape)


    print(art.azimuth)
    print(len(art.azimuth['data']))

    for x in range(0, len(art.azimuth['data'])):
        print(f"{x}: {art.azimuth['data'][x]:.3f}, {art.elevation['data'][x]:.3f}")

    print(art.elevation)
    print(art.elevation['data'].shape)

    print(art.fixed_angle)
    print(len(art.fixed_angle['data']))

    fixed = len(art.fixed_angle['data'])

    scan_final = 360 * 4 * 3 + (fixed - 3) * 360
    print(scan_final)
    print(art.azimuth['data'])


def print_fields(radar):

    fields = radar.fields

    for field in fields:
        print(field)
        print(fields[field]['data'].shape)
        print(fields[field]['data'].dtype)

    print(radar.azimuth)
    print(len(radar.azimuth['data']))
    print(radar.elevation)
    print(len(radar.elevation['data']))



def get_closest(config, radar_id, target_dt):

    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)
    filename = manager.get_closest(target_dt)
    return filename


def plot_all():

    radar_id = "kcbw"
    config = bugtracker.config.load("./bugtracker.json")
    date_of_interest = datetime.datetime(2019,7,1,12)

    output_folder = "/storage/spruce/plot_output/alignment"
    plotter = AlignmentPlotter(output_folder)


    start = date_of_interest
    end = date_of_interest + datetime.timedelta(hours=6)
    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)
    file_list = manager.get_range(start, end)

    for filename in file_list:
        print(f"Plotting {filename}")
        radar_handle = pyart.io.read(filename)
        scan_dt = manager.datetime_from_file(filename)
        plotter.set_data(radar_handle, radar_id)
        plotter.save_plot(scan_dt)


def show_sample_fields():
    radar_id = "kcbw"
    config = bugtracker.config.load("./bugtracker.json")
    date_of_interest = datetime.datetime(2019,7,1,12)

    output_folder = "/storage/spruce/plot_output/alignment"
    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)
    radar_file = manager.get_closest(date_of_interest)
    radar = pyart.io.read(radar_file)

    print_fields(radar)



def main():

    radar_id = "kcbw"
    config = bugtracker.config.load("./bugtracker.json")

    template_date = datetime.datetime(2019,7,1,0)
    data_date = datetime.datetime(2019,7,1,12)

    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)

    template_file = manager.get_closest(template_date)
    data_file = manager.get_closest(data_date)

    manager.build_template(template_file)
    nex_data = manager.extract_data(data_file)
    print(nex_data)


main()