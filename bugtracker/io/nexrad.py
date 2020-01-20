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

import pyart

import bugtracker.core.utils


class NexradManager:
    """
    The sole responsabilities of the NexradManager class are
    to return filenames and get metadata/grid_info from files
    """


    def __init__(self, config, radar_id):

        self.config = config
        self.radar_id = radar_id.lower()
        self.nexrad_dir = self.config['input_dirs']['nexrad']

        # Initialize radar parameters to None
        self.metadata = None
        self.product_grid = None
        self.precip_grid = None


    def __str__(self):
        rep = "NexradManager\n"

        rep += f"Radar: {self.radar_id}\n"
        rep += f"NEXRAD directory: {self.nexrad_dir}"

        return rep


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
        """
        This method extracts metadata from any nexrad_file
        """

        nexrad_handle = pyart.io.read(nexrad_file)

        radar_name = nexrad_handle.metadata['instrument_name']

        # Do a lowercase comparison
        if not bugtracker.core.utils.lower_compare(radar_name, self.radar_id):
            raise ValueError(f"Radar ID does not match: {radar_name}, {self.radar_id}")

        radar_id = self.radar_id

        latitude = nexrad_handle.latitude['data'][0]
        longitude = nexrad_handle.longitude['data'][0]

        abs_lat = abs(latitude)
        abs_lon = abs(longitude)

        if abs_lat > 180.0:
            raise ValueError(f"Invalid latitude: {latitude}")

        if abs_lon > 360.0:
            raise ValueError(f"Invalid longitude: {longitude}")

        datestamp = nexrad_handle.time['units'].split(' ')[-1]
        scan_dt = datetime.datetime.strptime(datestamp, "%Y-%m-%dT%H:%M:%SZ")

        metadata = bugtracker.core.metadata.Metadata(radar_id, scan_dt, latitude, longitude, radar_name)
        return metadata


    def extract_precip_grid(self, nexrad_file):

        nexrad_handle = pyart.io.read(nexrad_file)

        gates = 1832
        azims = 720

        azim_step = 0.5
        azim_offset = 0.25

        gate_step = nexrad_handle.range['meters_to_center_of_first_gate']
        gate_offset = nexrad_handle.range['meters_between_gates']

        precip_grid = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step,
                                                    azim_offset=azim_offset, gate_offset=gate_offset)

        return precip_grid


    def extract_product_grid(self, nexrad_file):

        nexrad_handle = pyart.io.read(nexrad_file)

        gates = 1832
        azims = 720

        azim_step = 1.0
        azim_offset = 0.5

        gate_step = nexrad_handle.range['meters_to_center_of_first_gate']
        gate_offset = nexrad_handle.range['meters_between_gates']

        product_grid = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step,
                                                     azim_offset=azim_offset, gate_offset=gate_offset)

        return product_grid


    def build_template(self, template_file):
        """
        We set a template file which "fixes" the grid orientation.
        Every subsequent scan is checked for consistency with this
        original set of dimensions. This allows us to detect when the
        scan strategy has changed.
        """

        if not os.path.isfile(template_file):
            raise FileNotFoundError(template_file)

        self.metadata = self.extract_metadata(template_file)
        self.precip_grid = self.extract_precip_grid(template_file)
        self.product_grid = self.extract_product_grid(template_file)


    def extract_data(self, nexrad_file):

        nexrad_data = NexradData(nexrad_file, self.metadata, self.product_grid, self.precip_grid)
        return nexrad_data


class NexradData:

    def __init__(self, nexrad_file, metadata, product_grid, precip_grid):
        
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

        #low_res_grid (just for precip filtering) 
        #high res grid

        # NEXRAD pyart handle
        self.handle = pyart.io.read(nexrad_file)
        self.metadata = metadata
        self.product_grid = product_grid
        self.precip_grid = precip_grid

        self.check_consistency()


    def check_field_dims(self, field_name):

        if field_name not in self.handle.fields:
            raise KeyError(f"Missing field {field_name}")

        # Can't reliably check azims, because they are 
        # bundled into the vertical direction.

        field_dims = self.handle.fields[field_name]['data'].shape

        if len(field_dims) != 2:
            raise ValueError(f"Invalid field_dims: {field_dims}")

        if self.product_grid.gates != field_dims[1]:
            raise ValueError("Invalid gate number")

        if self.precip_grid.gates != field_dims[1]:
            raise ValueError("Invalid gate number")


    def check_consistency(self):
        
        template_msg = "\nYou may need to call the method 'build_template()' from the NexradManager"

        # Check that all data grids initialized

        if self.metadata is None:
            raise ValueError(f"metadata not initialized {template_msg}")

        if self.product_grid is None:
            raise ValueError(f"product_grid not initialized {template_msg}")

        if self.precip_grid is None:
            raise ValueError(f"precip_grid not initialized {template_msg}")

        # check field dimensions

        self.check_field_dims("differential_reflectivity")
        self.check_field_dims("spectrum_width")
        self.check_field_dims("differential_phase")
        self.check_field_dims("cross_correlation_ratio")
        self.check_field_dims("velocity")