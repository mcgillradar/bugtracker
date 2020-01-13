import os
import glob
import datetime

import bugtracker.config



def get_all_plots(config, start_date, end_date):
    
    


def main():

    config = bugtracker.config.load("./bugtracker.json")

    datestamp = "201307160400"
    station_id = "xam"
    dt_hours = 6

    start = datetime.datetime.strptime(datestamp, "%Y%m%d%H%M")
    end = start + datetime.timedelta(hours=dt_hours)





main()