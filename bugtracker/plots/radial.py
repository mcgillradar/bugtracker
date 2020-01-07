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
The ability to generate radial plots on a variety of radar
parameters is an important part of this library.
"""


import os
import glob
import datetime

import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopy
import geopy.distance
import netCDF4 as nc


class RadialPlotter():

    """
    This class provides considerable simplication
    """

    def __init__(self, lats, lons, output_folder):
        self.invalid = -9999.0
        self.output_folder = output_folder

        if not os.path.isdir(output_folder):
            raise FileNotFoundError("Folder not found:", output_folder)

        self.ax = None
        self.fig = None

        self.lats = lats
        self.lons = lons


    def _set_grid(self):
        """
        Private function for setting grid
        """

        #TODO: Don't hard-code these bounds
        major_ticks_lat = np.arange(35, 60, 1)
        minor_ticks_lat = np.arange(35, 60, 0.2)
        major_ticks_lon = np.arange(-140, -60, 1.0)
        minor_ticks_lon = np.arange(-140, -60, 0.2)

        self.ax.set_xticks(major_ticks_lon)
        self.ax.set_xticks(minor_ticks_lon, minor=True)
        self.ax.set_yticks(major_ticks_lat)
        self.ax.set_yticks(minor_ticks_lat, minor=True)

        self.ax.grid(which='minor', alpha=0.2)
        self.ax.grid(which='major', alpha=0.5)


    def _set_contours(self, min_value=(-10), max_value=40):

        # It is logical to take the integer floor(min) and ceil(max) values
        # of the data array, given the ranges we are dealing with. Directly taking
        # the min and max leaves very ugly ranges like (0.000000125, 0.99999321)

        # TODO: This currently throws a plotting exception if the values
        # are equal to each other and are an integer (i.e. the exceptional case that all values are zero)

        min_data = min_value
        max_data = max_value
        
        print("min_data:", min_data, "max_data:", max_data)

        # Number of distinct color levels
        gradations = 160
        gradation_step = (max_data - min_data) / float(gradations)

        CS2 = plt.contourf(self.lons, self.lats, self.data, gradations,
            transform=ccrs.PlateCarree(), cmap='jet', vmin=min_data, vmax=max_data)

        m = plt.cm.ScalarMappable(cmap=plt.cm.jet)
        m.set_array(self.data)
        m.set_clim(min_data, max_data)
        cbar = plt.colorbar(m, boundaries=np.arange(min_data, max_data, gradation_step))
        cbar.ax.set_ylabel(self.label)
        print("Type CS2:", type(CS2))
        print("Type m:", type(m))
        print("Type cbar:", type(cbar))



    def _add_features(self):
        """
        Private function for creating features
        """

        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='10m',
            facecolor='none')

        coast = cfeature.NaturalEarthFeature(category='physical', scale='10m',
            facecolor='none', name='coastline')

        self.ax.add_feature(cfeature.LAND.with_scale('10m'))
        self.ax.add_feature(states_provinces.with_scale('10m'), edgecolor='gray')
        self.ax.add_feature(cfeature.BORDERS.with_scale('10m'))
        self.ax.add_feature(coast, edgecolor='black')


    def _get_title(self, plot_type, plot_date):
        return plot_type + plot_date.strftime(" at %Y-%m-%d %H:%M UTC")


    def _fill_wedge(self):
        # Extending to fill in the wedge
        # TODO: Should get these parameters from param file
        azims = 720
        gates = 512
        new_shape = (azims + 1, gates)

        self.lats = np.ma.resize(self.lats, new_shape)
        self.lons = np.ma.resize(self.lons, new_shape)
        self.data = np.ma.resize(self.data, new_shape)

    def _set_range(self):

        lat_0 = self.metadata.lat
        lon_0 = self.metadata.lon

        origin = geopy.Point(lat_0, lon_0)

        max_dist_km = self.max_range
        dist = geopy.distance.distance(kilometers=max_dist_km)
 

        west = dist.destination(origin, 270.0)
        north = dist.destination(origin, 0.0)
        east = dist.destination(origin, 90.0)
        south = dist.destination(origin, 180.0)

        min_lat = south.latitude
        max_lat = north.latitude
        min_lon = west.longitude
        max_lon = east.longitude

        self.range = [min_lon, max_lon, min_lat, max_lat]


    def _set_cross(self):

        lat_0 = self.metadata.lat
        lon_0 = self.metadata.lon

        plt.plot(lon_0, lat_0, marker='x', color='black')



    def _set_circle(self, radius_km):

        lat_0 = self.metadata.lat
        lon_0 = self.metadata.lon

        origin = geopy.Point(lat_0, lon_0)
        dist = geopy.distance.distance(kilometers=radius_km)
 
        lats = []
        lons = []

        bearings = np.linspace(-180, 180, num=360)
        for x in range(0, 360):
            bearing = bearings[x]
            destination = dist.destination(origin, bearing)
            lats.append(destination.latitude)
            lons.append(destination.longitude)

        plt.plot(lons, lats, color='black', linewidth=0.4, alpha=0.5)


    def _set_circles(self):

        km_line = 25.0
        increment_km = 25.0

        while km_line <= self.max_range:
            self._set_circle(km_line)
            km_line += increment_km


    def calculate_aspect(self):
        """
        Need an actual procedure here.
        Will be based on lat/lon location.
        """
        return 1.4


    def save_plot(self, min_value=None, max_value=None):
        self._fill_wedge()
        self._set_range()

        aspect = self.calculate_aspect()
        self.ax = plt.axes(projection=ccrs.PlateCarree(), aspect=aspect)
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')

        print("ax type:", type(self.ax))

        self._set_grid()
        self._set_contours(min_value=min_value, max_value=max_value)
        self._add_features()
        self._set_cross()
        self._set_circles()

        plt.title(self._get_title(self.label, self.plot_datetime))
        self.ax.set_extent(self.range)

        plot_filename = self.plot_datetime.strftime("%Y%m%d%H%M") + "_" + self.label + ".png"
        output_file = os.path.join(self.output_folder, plot_filename)

        plt.savefig(output_file, dpi=200)
        plt.gcf().clear()


    def set_data(self, data, label, plot_datetime, metadata, max_range):

        # Should do some kind of check to make sure data is a
        # numpy array

        self.metadata = metadata
        self.max_range = max_range
        self.data = data
        self.label = label
        self.plot_datetime = plot_datetime
