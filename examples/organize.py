import os
import shutil
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


    def make_folder(self):

        if not os.path.isdir(self.dst_folder):
            print("Making folder:", self.dst_folder)
            os.makedirs(self.dst_folder)


    def move_file(self):

        base = os.path.basename(self.src_path)
        new_path = os.path.join(self.dst_folder, base)
        shutil.move(self.src_path, new_path)


def extract_iris(filename):

    iris_file = bugtracker.io.iris.IrisFile(filename)
    scan_dt = iris_file.datetime

    subdirs = scan_dt.strftime(key_format)
    source_dir = os.path.dirname(filename)
    dst_folder = os.path.join(source_dir, subdirs)

    return GenericFile(filename, dst_folder)


def extract_nexrad(filename, radar_site):

    split_site = radar_site.split("/")
    radar_id = split_site[6]

    scan_dt = bugtracker.io.nexrad.datetime_from_file(filename, radar_id)

    subdirs = scan_dt.strftime(key_format)
    source_dir = os.path.dirname(filename)
    dst_folder = os.path.join(source_dir, subdirs)

    return GenericFile(filename, dst_folder)


def extract_odim(filename):

    scan_dt = bugtracker.io.odim.datetime_from_file(filename)

    subdirs = scan_dt.strftime(key_format)
    source_dir = os.path.dirname(filename)
    dst_folder = os.path.join(source_dir, subdirs)

    return GenericFile(filename, dst_folder)


def extract_generic(filename, radar_type, radar_site):
    """
    Extract date from file
    """

    radar_type = radar_type.lower()

    if radar_type == "iris":
        return extract_iris(filename)
    elif radar_type == "nexrad":
        return extract_nexrad(filename, radar_site)
    elif radar_type == "odim":
        return extract_odim(filename)
    else:
        raise ValueError(f"Unsupported type: {radar_type}")



def folder_info(folder):

    print("Folder name:", folder)
    all_files = glob.glob(os.path.join(folder, "*"))
    print("Num files:", len(all_files))



def sort_site(radar_site, radar_type):

    print("Radar site:", radar_site)
    all_files = glob.glob(os.path.join(radar_site, "*"))
    all_files.sort()
    radar_files = []

    for file in all_files:
        if not os.path.isdir(file):
            generic = extract_generic(file, radar_type, radar_site)
            radar_files.append(generic)

    print("Num files:", len(radar_files))

    for generic in radar_files:
        generic.make_folder()
        generic.move_file()


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