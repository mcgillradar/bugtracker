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

"""
The AlignmentPlotter takes a pyART radar object and lets
us visualize the scan strategy that is being used for the
radar in question.
"""

import os
import datetime

import numpy as np
import matplotlib.pyplot as plt
import pyart


class AlignmentPlotter():

    def __init__(self, output_folder):

        self.output_folder = output_folder
        self.radar_id = None

        if not os.path.isdir(output_folder):
            raise FileNotFoundError("Folder not found:", output_folder)


    def set_data(self, radar, radar_id):
        """
        Takes a pyart.core.radar object as input
        """

        self.azimuth = radar.azimuth['data']
        self.elevation = radar.elevation['data']

        if self.azimuth.shape != self.elevation.shape:
            raise ValueError("Incompatible dimensions")

        if len(self.azimuth.shape) != 1:
            raise ValueError("Array must be 1D")

        self.length = len(radar.azimuth['data'])
        self.idx_range = np.linspace(1, self.length, num=self.length)
        self.radar_id = radar_id


    def save_plot(self, scan_dt):

        fig, ax1 = plt.subplots()
        ax1_color = 'tab:red'
        ax2_color = 'tab:blue'

        ax1.set_xlabel("Index")
        ax1.set_ylabel("azimuth", color=ax1_color)
        ax1.plot(self.idx_range, self.azimuth, label='azimuth', color=ax1_color)

        ax2 = ax1.twinx()

        ax2.set_ylabel("elevation", color=ax2_color)
        ax2.plot(self.idx_range, self.elevation, label='elevation', color=ax2_color)


        plt.legend()
        timestamp = scan_dt.strftime("%Y%m%d_%H%M%S")
        plt.title(f"Scan Alignment: {self.radar_id.upper()}, {timestamp}")

        output_base = self.radar_id + timestamp + ".png"
        output_file = os.path.join(self.output_folder, output_base)

        plt.savefig(output_file, dpi=200)
        plt.gcf().clear()