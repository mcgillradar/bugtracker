"""
Bugtracker - A radar utility for tracking insects
Copyright (C) 2020 Frederic Fabry, Daniel Hogg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import json


def locate_path(base_path):

    backup_path = "../apps/bugtracker.json"

    if os.path.isfile(base_path):
        return base_path
    elif os.path.isfile(backup_path):
        return backup_path
    else:
        raise FileNotFoundError(base_path)


def load(base_path):
    """
    This function provides a simple way to call load a .json
    config file.

    One weakness of this approach is that the top-level scripts
    must be run from within the /apps folder.
    """

    config_path = locate_path(base_path)

    config_file = open(config_path, mode='r')
    config_json = json.load(config_file)
    config_file.close()

    return config_json


class ConfigTemplate:

    def __init__(self):

        self.data = None


    def populate(self, root_directory):
        
        self.data = dict()

        # Create directory information
        self.data["input_dirs"] = dict()
        self.data["input_dirs"]["iris"] = os.path.join(root_directory, "iris_data")
        self.data["input_dirs"]["nexrad"] = os.path.join(root_directory, "nexrad_data")
        self.data["input_dirs"]["odim"] = os.path.join(root_directory, "odim_data")
        self.data["plot_dir"] = os.path.join(root_directory, "plot_output")
        self.data["netcdf_dir"] = os.path.join(root_directory, "netcdf_output")
        self.data["cache_dir"] = os.path.join(root_directory, "cache")
        self.data["animation_dir"] = os.path.join(root_directory, "animation")

        # Default processing settings
        self.data["iris_settings"] = dict()
        self.data["iris_settings"]["convol_scans"] = 5
        self.data["iris_settings"]["azim_precip_region"] = 4
        self.data["iris_settings"]["gate_precip_region"] = 4
        self.data["iris_settings"]["max_dbz_per_km"] = 5.0

        self.data["nexrad_settings"] = dict()
        self.data["nexrad_settings"]["vertical_scans"] = 3
        self.data["nexrad_settings"]["dbz_cutoff"] = -30.0

        self.data["odim_settings"] = dict()
        self.data["odim_settings"]["dbz_cutoff"] = -30.0

        self.data["clutter"] = dict()
        self.data["clutter"]["dbz_threshold"] = 10.0
        self.data["clutter"]["coverage_threshold"] = 0.30

        self.data["precip"] = dict()
        self.data["precip"]["azim_region"] = 4
        self.data["precip"]["gate_region"] = 4
        self.data["precip"]["max_dbz_per_km"] = 0.0

        self.data["processing"] = dict()
        self.data["processing"]["joint_cutoff"] = 30.0

        self.data["plot_settings"] = dict()
        self.data["plot_settings"]["max_range"] = 150.0


    def write(self, output_file):
        """
        Use some kind of prettyprint to get the output
        JSON file looking managable.
        """

        with open(output_file, 'w') as handle: 
            json.dump(self.data, handle, indent=4)


    def safe_mkdir(self, folder):

        if not os.path.isdir(folder):
            print("Creating directory:", folder)
            os.mkdir(folder)


    def make_folders(self):

        for key in self.data['input_dirs']:
            self.safe_mkdir(self.data['input_dirs'][key])

        self.safe_mkdir(self.data["plot_dir"])
        self.safe_mkdir(self.data["netcdf_dir"])
        self.safe_mkdir(self.data["cache_dir"])
        self.safe_mkdir(self.data["animation_dir"])
