"""
This file is part of Bugtracker
Copyright (C) 2019  McGill Radar Group

Bugtracker is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Bugtracker is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Bugtracker.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import glob
import datetime


class NexradManager:
    """
    The sole responsabilities of the NexradManager class are
    to return filenames and get metadata/grid_info from files
    """


    def __init__(self, config, radar_id):

        self.config = config
        self.radar_id = radar_id.lower()
        self.nexrad_dir = self.config['input_dirs']['nexrad']


    def datetime_from_file(self, filepath):
        """
        Extracting the timestamp with the file (with validation)
        """

        basename = os.path.basename(filepath)
        radar_upper = self.radar_id.upper()
        date_fmt = f"{radar_upper}%Y%m%d_%H%M%S_V06"
        file_dt = datetime.datetime.strptime(basename, date_fmt)

        return file_dt


    def get_closest(self, target_dt):

        current_year = target_dt.strftime("%Y")
        radar_upper = self.radar_id.upper()
        glob_string = f"{radar_upper}{current_year}*_V06"
        search = os.path.join(self.nexrad_dir, self.radar_id.lower(), glob_string)
        all_files = glob.glob(search)
        all_files.sort()

        num_files = len(all_files)

        min_idx = -1
        min_diff = 999999999

        print("num_files:", num_files)

        for x in range(0, num_files):
            current_file = all_files[x]
            file_dt = self.datetime_from_file(current_file)
            print(f"file_dt: {file_dt}, target_dt: {target_dt}")
            diff = file_dt - target_dt
            total_seconds = abs(diff.total_seconds())
            if total_seconds < min_diff:
                min_diff = total_seconds
                min_idx = x

        max_threshold = 60 * 30

        if min_diff > max_threshold:
            print(f"Min diff: {min_diff}")
            raise ValueError("Files not found within 30 min threshold")

        print("Min idx:", min_idx)
        closest = all_files[min_idx]

        if not os.path.isfile(closest):
            raise FileNotFoundError(closest)

        return closest


    def get_range(self, start, end):

        radar_upper = self.radar_id.upper()
        glob_string = f"{radar_upper}{current_year}*_V06"
        search = os.path.join(self.nexrad_dir, glob_string)
        all_files = glob.glob(search)
        all_files.sort()

        file_list = []

        for file in file_list:
            if not os.path.isfile(file):
                raise FileNotFoundError(f"File does not exist: {file}")


    def extract_metadata(nexrad_file):

        metadata = bugtracker.core.metadata()
        return metadata


    def extract_grid_info(nexrad_file):

        grid_info = bugtracker.core.grid_info()
        return grid_info





class NexradData:

    def __init__(self, nexrad_file, metadata, grid_info):
        
        """
        Should be some grid verification checks
        """

        pass

        """
        
        """