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

"""
IRIS files have a weird file structure where they are
spread out over multiple DOPVOL and CONVOL files.
"""


import os
import glob
import datetime

import numpy as np
import pyart

import bugtracker.config
import bugtracker.core.utils

def get_scan_type(radar):
    scan_type = (radar.metadata['sigmet_task_name'].decode()).strip().lower()
    permitted_scans = ['convol', 'dopvol1_a', 'dopvol1_b', 'dopvol1_c', 'dopvol2']

    if scan_type not in permitted_scans:
        raise ValueError(f"Scan type invalid: {scan_type}")

    return scan_type

def get_dbz_key(radar):
    scan_type = get_scan_type(radar)

    # The CONVOL scans (for some reason) use the 'total_power' field
    # to store reflectivity.
    if scan_type == 'convol':
        dbz_key = 'total_power'
    else:
        dbz_key = 'reflectivity'

    return dbz_key


def extract_dbz(filename):

    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)

    radar = pyart.io.read_sigmet(filename)
    scan_type = get_scan_type(radar)
    print("Extracting array from scan:", scan_type)
    dbz_key = get_dbz_key(radar)

    dbz_field = radar.fields[dbz_key]['data']
    print("DBZ array shape:", dbz_field.shape)

    return dbz_field


def extract_fixed_angle(filename, single=False):

    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)

    radar = pyart.io.read_sigmet(filename)
    angles = radar.fixed_angle['data']

    if single and len(angles) != 1:
        raise ValueError("Should be exactly one angle")
        return angles[0]
    else:
        return angles


class IrisFile:

    def __init__(self, path):

        self.path = path
        basename = os.path.basename(path)
        split_base = basename.split(':')
        if len(split_base) != 2:
            raise SyntaxError(f"Invalid filename {basename}")

        self.type = split_base[0]
        pattern = "%Y%m%d%H%M%S"
        self.datetime = datetime.datetime.strptime(split_base[1], pattern)


    def __str__(self):
        return f"{self.path}\n{self.type}\n{self.datetime}\n"


class IrisSet:

    def __init__(self, convol, radar_id):

        self.config = bugtracker.config.load("./bugtracker.json")

        if convol.datetime is None:
            raise ValueError("IrisSet datetime cannot be null.")

        if radar_id is None:
            raise ValueError("3 letter radar_id code cannot be null")

        self.datetime = convol.datetime
        self.radar_id = radar_id
        self.convol = convol.path
        self.dopvol_1A = None
        self.dopvol_1B = None
        self.dopvol_1C = None
        self.dopvol_2 = None


    def display_stats(self):

        scans = [self.convol, self.dopvol_1A, self.dopvol_1B,
                 self.dopvol_1C, self.dopvol_2]
        labels = ['convol', 'dopvol1A', 'dopvol1B', 'dopvol1C', 'dopvol2']
        num_scans = len(scans)

        for x in range(0, num_scans):
            bugtracker.core.utils.iris_scan_stats(scans[x], labels[x])


    def round_angle(self, angle):
        """
        Rounds angle, and uses convention of negative angles,
        instead of wrapping around 0 to 360.
        """

        if angle >= 360.0:
            angle -= 360.0

        return round(angle,1)


    def convol_elevs(self):
        """
        Convol elevs start from the highest, but we want
        to take the N lowest.
        """

        num_convol_scans = self.config["iris_settings"]["convol_scans"]
        convol_elevs = []
        
        fixed_angles = extract_fixed_angle(self.convol)
        total_angles = len(fixed_angles)

        for x in range(0, num_convol_scans):
            idx = total_angles - (1 + x)
            raw_angle = fixed_angles[idx]
            angle = self.round_angle(raw_angle)
            convol_elevs.append(angle)

        return convol_elevs


    def dopvol_elevs(self):
        """
        Dopvol elevs are DOPVOL_1A, DOPVOL_1B, DOPVOL_2
        """

        dopvol_elevs = []

        angle_1A = extract_fixed_angle(self.dopvol_1A)
        angle_1B = extract_fixed_angle(self.dopvol_1B)
        angle_2 = extract_fixed_angle(self.dopvol_2)

        dopvol_elevs.append(angle_1A)
        dopvol_elevs.append(angle_1B)
        dopvol_elevs.append(angle_2)

        return dopvol_elevs


    def get_elevs(self, scan_type):

        # This needs to be modified so it works for
        # radars other than XAM

        scan_type = (scan_type.strip()).lower()

        if scan_type == 'convol':
            return self.convol_elevs
        elif scan_type == 'dopvol':
            return self.dopvol_elevs
        else:
            raise ValueError(scan_type)

    def is_valid(self):

        if self.convol is None:
            return False

        if self.dopvol_1A is None:
            return False

        if self.dopvol_1B is None:
            return False

        if self.dopvol_1C is None:
            return False

        if self.dopvol_2 is None:
            return False

        return True

    def __str__(self):
        return f"{self.convol}\n{self.dopvol_1A}\n{self.dopvol_1B}\n{self.dopvol_1C}\n{self.dopvol_2}\n"


class IrisCollection:

    def __init__(self, directory, radar_id):

        self.radar_id = radar_id
        self.files = []

        convol_files = glob.glob(os.path.join(directory,"CONVOL*"))
        dopvol_files = glob.glob(os.path.join(directory,"DOPVOL*"))
        file_list = convol_files + dopvol_files

        for file in file_list:
            self.files.append(IrisFile(file))

        self._sort()
        self.sets = self._create_sets()


    def _sort(self):
        """
        Sort IRIS collection by ascending datetime
        """
        self.files.sort(key = lambda x: x.datetime)

    def _create_sets(self):

        sets = []

        current_set = None

        for file in self.files:
            if file.type == 'CONVOL':
                if current_set is not None:
                    sets.append(current_set)
                current_set = IrisSet(file, self.radar_id)
            else:
                if current_set is None:
                    print(f"Skipping leading dopvol file: {file}")
                else:
                    if file.type == 'DOPVOL1_A':
                        current_set.dopvol_1A = file.path
                    elif file.type == 'DOPVOL1_B':
                        current_set.dopvol_1B = file.path
                    elif file.type == 'DOPVOL1_C':
                        current_set.dopvol_1C = file.path
                    elif file.type == 'DOPVOL2':
                        current_set.dopvol_2 = file.path
                    else:
                        raise ValueError(f"Invalid type {file.type}")

        return sets


    def closest_set(self, target_dt):

        """
        This can be rewritten as a log(N) algorithm.
        """

        num_sets = len(self.sets)

        min_idx = -1
        min_diff = 999999999

        for x in range(0, num_sets):
            diff = target_dt - self.sets[x].datetime
            total_seconds = abs(diff.total_seconds())
            if total_seconds < min_diff:
                min_diff = total_seconds
                min_idx = x

        print("Min diff in seconds:", min_diff)

        max_threshold = 60 * 30

        if min_diff > max_threshold:
            raise ValueError("Files not found within 30 min threshold")

        if min_idx == -1:
            return None
        else:
            return self.sets[min_idx]


    def check_sets(self):

        num_sets = len(self.sets)
        valid = 0

        for iris_set in self.sets:
            if iris_set.is_valid():
                valid += 1

        print(f"{valid}/{num_sets} valid sets.")


    def time_range(self, start_time, data_mins):
        """
        Extract IrisSet list within the time period
        """

        end_time = start_time + datetime.timedelta(minutes=data_mins)

        sets_in_range = []

        print(self.sets)

        for current_set in self.sets:
            current_set_dt = current_set.datetime
            print(current_set_dt)
            if current_set_dt >= start_time and current_set_dt <= end_time:
                sets_in_range.append(current_set)

        sets_in_range.sort(key = lambda x: x.datetime)
        return sets_in_range