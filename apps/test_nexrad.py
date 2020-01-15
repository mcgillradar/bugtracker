

import os
import datetime

import numpy as np

import bugtracker


def main():


    radar_id = "kcbw"
    config = bugtracker.config.load("./bugtracker.json")

    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)

    date_of_interest = datetime.datetime(2019,7,22,12)

    closest = manager.get_closest(date_of_interest)
    print("Closest:", closest)

    num_hours = 36

    start = date_of_interest
    end = date_of_interest + datetime.timedelta(hours=num_hours)

    file_range = manager.get_range(start, end)
    print("Num elements:", len(file_range))
    print(file_range)


main()