"""
The GridCache manages the cache of lat/lon grids computed
for a particular radar.

It is responsible for generating, caching and retrieval of grids.
Note that the output latlon (azim,gates) grids are used for plotting
on high-resolution grids that are generated 'artificially'.
"""

import os
import glob
import shutil

import numpy as np
import netCDF4 as nc
import pyart

import bugtracker.config



def get_latlon_key():
    pass


def get_calib_key(metadata, grid_info):

    radar_id = metadata.radar_id
    azims = grid_info.azims
    gates = grid_info.gates
    azim_step = grid_info.azim_step
    gate_step = grid_info.gate_step

    # TODO: Rounding might be an issue here for 0.5, float values to string
    cache_basename = f"{radar_id}_{azims}_{gates}_{azim_step}_{gate_step}.nc"
    return cache_basename


def calib_filepath(metadata, grid_info):
    """
    Sort out folder structure.
    """

    config = bugtracker.config.load("./bugtracker.json")
    cache_base = config['cache_dir']
    cache_folder = os.path.join(cache_base, 'calib')
    calib_filename = get_calib_key(metadata, grid_info)

    full_path = os.path.join(cache_folder, calib_filename)
    return full_path


class CacheManager:

    def __init__(self):

        self.config = bugtracker.config.load("./bugtracker.json")


    def __safe_mkdir(self, folder):
        """
        Makes folder only if folder doesn't exist.
        """
        if not os.path.isdir(folder):
            print("Making folder:", folder)
            os.mkdir(folder)
        else:
            print("Directory already exists:", folder)


    def reset(self):
        """
        Deletes all cache elements.
        """

        cache_root = self.config["cache_dir"]
        
        if not os.path.isdir(cache_root):
            print("Cache directory does not exist. Returning.")
            return

        print("Emptying contents of directory:", cache_root)
        authorization = input("Is this ok? [y/n]")

        if authorization.lower().strip() == "y":
            shutil.rmtree(cache_root)
            os.mkdir(cache_root)

        if not os.path.isdir(cache_root):
            raise FileNotFoundError(cache_root)


    def make_folders(self):

        cache_root = self.config["cache_dir"]

        self.__safe_mkdir(cache_root)

        elev_folder = os.path.join(cache_root, "elevation")
        zipped_folder = os.path.join(elev_folder, "zipped")
        srtm3_folder = os.path.join(elev_folder, "srtm3")
        calib_folder = os.path.join(cache_root, "calib")

        self.__safe_mkdir(elev_folder)
        self.__safe_mkdir(zipped_folder)
        self.__safe_mkdir(srtm3_folder)
        self.__safe_mkdir(calib_folder)
