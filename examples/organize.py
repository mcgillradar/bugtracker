import os
import glob
import datetime
import argparse

import bugtracker


"""
This is a quick script for sorting input files into
/yyyy/mm/dd
"""

config = bugtracker.config.load("../apps")
key_format = os.path.join("%Y", "%m", "%d")


class GenericFile:

    def __init__(self, src, dst):

        self.src_path = src
        self.dst_folder = dst


def extract_iris(filename):

    iris_file = bugtracker.io.iris.IrisFile(filename)
    scan_dt = iris_file.datetime
    subdirs = scan_dt.strftime(key_format)

    source_dir = os.path.dirname(filename)
    dst_folder = os.path.join(source_dir, subdirs)
    print("dst_folder", dst_folder)


def extract_nexrad(filename):

    raise NotImplementedError()


def extract_odim(filename):

    raise NotImplementedError()



def extract_generic(filename, radar_type):
    """
    Extract date from file
    """

    radar_type = radar_type.lower()

    if radar_type == "iris":
        return extract_iris(filename)
    elif radar_type == "nexrad":
        return extract_nexrad(filename)
    elif radar_type == "odim":
        return extract_odim(filename)
    else:
        raise ValueError(f"Unsupported type: {radar_type}")



def folder_info(folder):

    print("Folder name:", folder)
    all_files = glob.glob(os.path.join(folder, "*"))
    print("Num files:", len(all_files))



def make_folders():
    pass


def sort_site(radar_site, radar_type):

    print("Radar site:", radar_site)
    all_files = glob.glob(os.path.join(radar_site, "*"))
    all_files.sort()
    radar_files = []

    for file in all_files:
        if not os.path.isdir(file):
            generic = extract_generic(file, radar_type)
            radar_files.append(generic)

    print("Num files:", len(radar_files))


def sort_radar(folder, radar_type):
    print("*****************************")

    all_files = glob.glob(os.path.join(folder, "*"))

    radar_sites = []

    for file in all_files:
        if os.path.isdir(file):
            radar_sites.append(file)

    for radar_site in radar_sites:
        sort_site(radar_site, radar_type)


def sort_files():

    iris_folder = config["input_dirs"]["iris"]
    nexrad_folder = config["input_dirs"]["nexrad"]
    odim_folder = config["input_dirs"]["odim"]

    sort_radar(iris_folder, "iris")
    sort_radar(nexrad_folder, "nexrad")
    sort_radar(odim_folder, "odim")


sort_files()