

import os
import datetime

import numpy as np
import pyart

import bugtracker


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
        print(art.azimuth['data'][x])
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


def main():

    #radar_id = "ksfx"
    radar_id = "kcbw"
    config = bugtracker.config.load("./bugtracker.json")

    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)

    date_of_interest = datetime.datetime(2020,1,1,12)

    closest = manager.get_closest(date_of_interest)
    print("Closest:", closest)

    num_hours = 36

    start = date_of_interest
    end = date_of_interest + datetime.timedelta(hours=num_hours)

    file_range = manager.get_range(start, end)
    print("Num elements:", len(file_range))

    group_angles(closest)
    # klnx also





main()