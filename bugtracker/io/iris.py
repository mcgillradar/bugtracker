
"""
IRIS files have a weird file structure where they are
spread out over multiple DOPVOL and CONVOL files.
"""


import os
import glob
import datetime

import numpy as np
import pyart

import bugtracker.scan



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


    def get_elevs(self, scan_type):

        # This needs to be modified so it works for
        # radars other than XAM

        scan_type = (scan_type.strip()).lower()

        if scan_type == 'convol':
            return [-0.5, -0.3, -0.1, 0.1, 0.3]
        elif scan_type == 'dopvol':
            return [-0.5, -0.2, -0.5]
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

    def __init__(self, directory, radar_id, date_range=None):

        self.radar_id = radar_id

        self.files = []

        if date_range is not None:
            raise NotImplementedError("Haven't implemented collection from range yet")
        else:
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