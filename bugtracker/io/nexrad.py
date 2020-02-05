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
import math
import time

import numpy as np
import pyart
from scipy import interpolate

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
        print(f"Type target_dt: {type(target_dt)}")
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


    def extract_grid(self, nexrad_file):

        nexrad_handle = pyart.io.read(nexrad_file)

        gates = 1832
        azims = 720

        azim_step = 0.5
        azim_offset = 0.25

        gate_step = nexrad_handle.range['meters_between_gates']
        gate_offset = nexrad_handle.range['meters_to_center_of_first_gate']

        grid_info = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step,
                                                  azim_offset=azim_offset, gate_offset=gate_offset)

        return grid_info


    def populate(self, template_date):
        """
        We set a template file which "fixes" the grid orientation.
        Every subsequent scan is checked for consistency with this
        original set of dimensions. This allows us to detect when the
        scan strategy has changed.
        """

        template_file = self.get_closest(template_date)

        if not os.path.isfile(template_file):
            raise FileNotFoundError(template_file)

        self.metadata = self.extract_metadata(template_file)
        self.grid_info = self.extract_grid(template_file)


    def extract_data(self, nexrad_file):

        if self.metadata is None:
            raise ValueError("metadata cannot be None")

        if self.grid_info is None:
            raise ValueError("grid_info cannot be None")

        t0 = time.time()

        nexrad_data = NexradData(nexrad_file, self.metadata, self.grid_info)
        
        t1 = time.time()
        elapsed = t1 - t0
        print(f"Time for data extraction: {elapsed:.3f} s")
        return nexrad_data


class NexradData:

    def __init__(self, nexrad_file, metadata, grid_info):
        
        """
        This function takes the input file, opens it as a handle
        in pyart. Then, it takes the multiplexed 2D arrays and converts
        them to a series of 3D numpy arrays.

        One important step in this process is reverting the azimuth
        offsets that are present in the original 2D array.
        """

        self.handle = pyart.io.read(nexrad_file)
        self.scan_dt = self.get_scan_dt(nexrad_file, metadata)
        self.metadata = metadata
        self.grid_info = grid_info

        self.azims_per_lower = 720
        self.azims_per_upper = 360

        # Initializing normalized 3D fields
        self.dbz_unfiltered = self.init_field()
        self.spectrum_width = self.init_field()
        self.velocity = self.init_field()
        self.cross_correlation_ratio = self.init_field()

        self.check_consistency()

        input_dims = self.handle.fields['reflectivity']['data'].shape

        num_lower_levels = self.get_num_lower()
        num_upper_levels = self.get_num_upper()

        self.scan_angles = self.get_scan_angles(num_lower_levels, num_upper_levels)

        if len(self.scan_angles) != self.dbz_unfiltered.shape[0]:
            raise ValueError(f"Inconsistent number of scan angles: {self.scan_angles} != {self.reflectivity.shape[0]}")

        self.check_levels(num_lower_levels, num_upper_levels, input_dims)

        self.fill_lower(num_lower_levels)
        self.fill_upper(num_lower_levels, num_upper_levels)


    def __str__(self):

        rep = "NexradData:\n"

        rep += f"Dimensions: {self.reflectivity.shape}"

        return rep


    def get_scan_dt(self, nexrad_file, metadata):
        """
        Extracting the datetime of the scan from the NEXRAD filename
        """
        basename = os.path.basename(nexrad_file)

        radar_id = metadata.radar_id
        date_pattern = f"{radar_id.upper()}%Y%m%d_%H%M%S_V06"

        return datetime.datetime.strptime(basename, date_pattern)


    def init_field(self):

        """
        This fields should probably be np.ma masked arrays, to 
        be consistent with the convention chosen for IRIS data
        """

        num_lower_levels = self.get_num_lower()
        num_upper_levels = self.get_num_upper()

        num_vertical = num_lower_levels // 2 + num_lower_levels

        field_shape = (num_vertical,self.grid_info.azims, self.grid_info.gates)
        field = np.zeros(field_shape, dtype=np.float32)

        return field


    def get_scan_angles(self, num_lower_levels, num_upper_levels):

        fixed_angle = self.handle.fixed_angle['data']

        scan_angles = []

        for x in range(num_lower_levels):
            # Getting even scans
            if x % 2 == 0:
                scan_angles.append(fixed_angle[x])

        for y in range(num_upper_levels):
            idx = num_lower_levels + y
            scan_angles.append(fixed_angle[idx])

        return scan_angles


    def check_field_dims(self, field_name):

        if field_name not in self.handle.fields:
            raise KeyError(f"Missing field {field_name}")

        # Can't reliably check azims, because they are 
        # bundled into the vertical direction.

        field_dims = self.handle.fields[field_name]['data'].shape

        if len(field_dims) != 2:
            raise ValueError(f"Invalid field_dims: {field_dims}")

        if self.grid_info.gates != field_dims[1]:
            raise ValueError("Invalid gate number")


    def check_consistency(self):
        
        template_msg = "\nYou may need to call the method 'build_template()' from the NexradManager"

        # Check that all data grids initialized

        if self.metadata is None:
            raise ValueError(f"metadata not initialized {template_msg}")

        if self.grid_info is None:
            raise ValueError(f"product_grid not initialized {template_msg}")

        # check field dimensions

        self.check_field_dims("spectrum_width")
        self.check_field_dims("reflectivity")
        self.check_field_dims("cross_correlation_ratio")
        self.check_field_dims("velocity")


    def check_levels(self, num_lower, num_upper, input_shape):
        """
        A consistency check to make sure the num_lower/num_upper
        detection worked correctly.
        """

        if len(input_shape) != 2:
            raise ValueError("Error: 2-dimensional array expected.")


    def get_num_lower(self):

        return 6


    def get_num_upper(self):

        """
        By convention, we will choose the 6 first levels of the
        upper scans.
        """

        return 6


    def fill_lower_field(self, field, field_key, theta, start_idx, vertical_level):
        """
        Reshuffling twisted azimuths from NEXRAD input to a regular grid
        """

        azims = self.grid_info.azims
        gates = self.grid_info.gates
        diff = azims - theta

        dst_idx = theta
        for src_idx in range(0, diff):
            field[vertical_level,dst_idx,:] = self.handle.fields[field_key]['data'][(start_idx + src_idx),:]
            dst_idx += 1

        dst_idx = 0
        for src_idx in range(diff, azims):
            field[vertical_level,dst_idx,:] = self.handle.fields[field_key]['data'][(start_idx + src_idx),:]
            dst_idx += 1


    def fill_lower_scan(self, scan_idx, level):


        start_idx = self.azims_per_lower * scan_idx
        end_idx = self.azims_per_lower * (scan_idx + 1)

        azim_start = self.handle.azimuth['data'][start_idx]
        azim_end = self.handle.azimuth['data'][end_idx-1]

        adjusted_start = azim_start - self.grid_info.azim_offset
        float_theta = adjusted_start / self.grid_info.azim_step
        theta = int(round(float_theta))

        # Code for one field first

        self.fill_lower_field(self.dbz_unfiltered, "reflectivity", theta, start_idx, level)
        self.fill_lower_field(self.spectrum_width, "spectrum_width", theta, start_idx, level)
        self.fill_lower_field(self.cross_correlation_ratio, "cross_correlation_ratio", theta, start_idx, level)
        self.fill_lower_field(self.velocity, "velocity", theta, start_idx, level)


    def fill_lower(self, num_lower):

        """
        This can be efficiently solved by using numpy array slicing
        """

        # Option to get odd or even scans
        get_odd_scans = False

        scans = []

        for x in range(0, num_lower):
            if get_odd_scans:
                if x % 2 != 0:
                    scans.append(x)
            else:
                if x % 2 == 0:
                    scans.append(x)


        for new_idx in range(0, len(scans)):
            scan_idx = scans[new_idx]
            self.fill_lower_scan(scan_idx, new_idx)


    def fill_upper_field(self, field, field_key, theta, start_idx, vertical_level):
        
        azims = self.azims_per_upper
        gates = self.grid_info.gates
        diff = azims - theta
        azim_list = np.linspace(self.upper_azim_offset, self.upper_azim_offset + self.upper_azim_step * (azims-1), num=azims)

        range_indices = np.linspace(0, gates-1, num=gates)

        # Low resolution, temp numpy array
        low_res_field = np.zeros((azims,gates), dtype=np.float32)

        dst_idx = theta
        for src_idx in range(0, diff):
            low_res_field[dst_idx,:] = self.handle.fields[field_key]['data'][(start_idx + src_idx),:]
            dst_idx += 1

        dst_idx = 0
        for src_idx in range(diff, azims):
            low_res_field[dst_idx,:] = self.handle.fields[field_key]['data'][(start_idx + src_idx),:]
            dst_idx += 1

        for x_start in range(azims):
            # Some modular arithmatic for wraparound
            x_end = (x_start + 1) % azims
            output_start = 2 * x_start
            output_mid = output_start + 1

            # Setting start first, no data manipulation required
            field[vertical_level,output_start,:] = low_res_field[x_start,:]

            # Setting midpoint, must average two arrays
            field[vertical_level,output_mid,:] = (low_res_field[x_start,:] + low_res_field[x_end,:]) / 2.0


    def fill_upper_scan(self, upper_idx, new_idx, num_lower, num_upper):

        start_idx = self.azims_per_lower * num_lower + self.azims_per_upper * upper_idx
        end_idx = self.azims_per_lower * num_lower + self.azims_per_upper * (upper_idx+1)

        azim_start = self.handle.azimuth['data'][start_idx]
        azim_end = self.handle.azimuth['data'][end_idx-1]

        self.upper_azim_step = 1.0
        self.upper_azim_offset = 0.5

        adjusted_start = azim_start - self.upper_azim_offset
        float_theta = adjusted_start / self.upper_azim_step
        theta = int(round(float_theta))

        # Code for one field first

        self.fill_upper_field(self.dbz_unfiltered, "reflectivity", theta, start_idx, new_idx)
        self.fill_upper_field(self.spectrum_width, "spectrum_width", theta, start_idx, new_idx)
        self.fill_upper_field(self.cross_correlation_ratio, "cross_correlation_ratio", theta, start_idx, new_idx)
        self.fill_upper_field(self.velocity, "velocity", theta, start_idx, new_idx)


    def fill_upper(self, num_lower, num_upper):

        """
        For the upper scans, the source resolution is 360. In order
        to get to 720, we will perform interpolation using the np.interp()
        function.
        """

        new_idx = num_lower // 2
        for upper_idx in range(0, num_upper):
            self.fill_upper_scan(upper_idx, new_idx, num_lower, num_upper)
            new_idx += 1


