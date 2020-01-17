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
        """
        Get the closest radar scan to the specified date,
        and return an error if the closest is more than 30mins away
        or if no input files are found.
        """

        current_year = target_dt.strftime("%Y")
        radar_upper = self.radar_id.upper()
        glob_string = f"{radar_upper}{current_year}*_V06"
        search = os.path.join(self.nexrad_dir, self.radar_id.lower(), glob_string)
        all_files = glob.glob(search)
        all_files.sort()

        num_files = len(all_files)

        min_idx = -1
        min_diff = 999999999

        for x in range(0, num_files):
            current_file = all_files[x]
            file_dt = self.datetime_from_file(current_file)
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
        """
        Return all NEXRAD radar files within the specified
        date range.
        """

        radar_lower = self.radar_id.lower()
        radar_upper = self.radar_id.upper()
        glob_string = f"{radar_upper}*_V06"
        search = os.path.join(self.nexrad_dir, radar_lower, glob_string)
        all_files = glob.glob(search)
        all_files.sort()

        range_list = []

        for input_file in all_files:
            current_dt = self.datetime_from_file(input_file)
            if start <= current_dt and current_dt <= end:
                range_list.append(input_file)

        for file in range_list:
            if not os.path.isfile(file):
                raise FileNotFoundError(f"File does not exist: {file}")

        return range_list


    def extract_metadata(self, nexrad_file):

        metadata = bugtracker.core.metadata()
        return metadata


    def extract_precip_grid(self, nexrad_file):

        precip_grid = bugtracker.core.grid_info()

        return precip_grid


    def extract_product_grid(self, nexrad_file):

        product_grid = bugtracker.core.grid_info()

        return product_grid



class NexradData:

    def __init__(self, nexrad_file, metadata, grid_info):
        
        """
        Should be some grid verification checks
        A basic assumption is that scan strategy might change, but
        file structure should not change.

        IE its fine if we go from scanning at 0.1, 0.3 and 0.5,
        but if it somehow goes to a different number of scans altogether,
        or the grid dimensions change, this should raise an exception.
        """

        """
        Actually this assumption should be tested. How can we compare
        the scans between 1990 and 2020? When/where does it shift?
        """

        #low_res_grid = 

        #pass
        pass