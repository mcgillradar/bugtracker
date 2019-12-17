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

import numpy as np


def get_code_dict():
    """
    We only want to define these number codes in
    one place, that way we keep consistent.
    """

    code_dict = dict()
    code_dict['none'] = 0
    code_dict['clutter'] = 1
    code_dict['rain'] = 2
    code_dict['bugs'] = 3

    return code_dict


def get_code(target_code):

    target_code = target_code.lower().strip()
    code_dict = get_code_dict()

    if target_code not in code_dict:
        raise ValueError(f"Invaid target_code {target_code}")
    else:
        return code_dict[target_code]


class TargetId():

    def __init__(self, filtered_dbz, clutter_3d, precip_3d):
        

        self.min_dbz_bugs = -10.0
        self.max_dbz_bugs = 30.0

        self.dbz = filtered_dbz
        self.clutter = clutter_3d
        self.precip = precip_3d

        self.id_matrix = None

        self.verify_inputs()

        self.dims = self.dbz.shape

        self.construct_matrix()


    def verify_inputs(self):
        """
        Make sure input dimensions correspond, that types
        are correct.
        """

        dbz_shape = self.dbz.shape
        clutter_shape = self.clutter.shape
        precip_shape = self.precip.shape

        if dbz_shape != clutter_shape:
            raise ValueError("Incompatible array dimensions - clutter filter.")

        if dbz_shape != precip_shape:
            raise ValueError("Incompatible array dimensions - precip filter.")


    def construct_matrix(self):
        """
        Priority list for classification:
        clutter > rain > bugs
        """
        
        code_dict = get_code_dict()
        all_clutter = np.full(self.dims, code_dict['clutter'], dtype=int)
        all_rain = np.full(self.dims, code_dict['rain'], dtype=int)
        all_bugs = np.full(self.dims, code_dict['bugs'], dtype=int)

        self.id_matrix = np.zeros(self.dims, dtype=int)

        bug_condition = np.logical_and(self.dbz < self.max_dbz_bugs, self.dbz > self.min_dbz_bugs)
        bug_condition = np.logical_and(bug_condition, np.logical_not(np.ma.getmask(self.dbz)))

        # Successively writing target classifications, with higher
        # priority classes overwriting previous.

        self.id_matrix = np.where(bug_condition, all_bugs, self.id_matrix)
        self.id_matrix = np.where(self.precip, all_rain, self.id_matrix)
        self.id_matrix = np.where(self.clutter, all_clutter, self.id_matrix)


    def export_matrix(self):
        """
        Returns matrix with a brief check to ensure init
        """

        if self.id_matrix is None:
            raise ValueError("Cannot export null matrix")

        return self.id_matrix
