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
import glob
import datetime

import cv2


class AnimationManager:

    def __init__(self, config, args):
        
        self.config = config

        self.date_fmt = "%Y%m%d%H%M"
        self.start = datetime.datetime.strptime(args.start, self.date_fmt)
        self.stop = datetime.datetime.strptime(args.stop, self.date_fmt)
        self.anim_dir = self.config['animation_dir']

        if not os.path.isdir(self.anim_dir):
            raise FileNotFoundError(self.anim_dir)

        self.plot_dir = self.get_full_plot_dir(args)

        all_plots = glob.glob(os.path.join(self.plot_dir, "*.png"))
        
        self.filtered_plots = self.filter_dates(all_plots)


    def get_full_plot_dir(self, args):

        base_plot_dir = self.config['plot_dir']

        station = args.station.lower().strip()
        plot_dir = os.path.join(base_plot_dir, station)

        if not os.path.isdir(plot_dir):
            raise FileNotFoundError(plot_dir)

        return plot_dir


    def extract_date(self, filename):

        basename = os.path.basename(filename)
        element_list = basename.split('_')
        scan_dt = datetime.datetime.strptime(element_list[0], self.date_fmt)
        return scan_dt


    def filter_dates(self, all_plots):

        filtered_dates = []
        print("Num plots:", len(all_plots))

        # inefficient but doesn't matter
        for plot in all_plots:
            plot_date = self.extract_date(plot)
            if plot_date >= self.start and plot_date <= self.stop:
                filtered_dates.append(plot)

        print("Num filtered dates:", len(filtered_dates))
        return filtered_dates


    def create_animation(self, image_list, label):

        frame = cv2.imread(image_list[0])

        video_name = os.path.join(self.anim_dir, label + ".avi")
        print("Creating video:", video_name)
        height, width, layers = frame.shape

        video = cv2.VideoWriter(video_name, 0, 1, (width, height))

        for image in image_list:
            video.write(cv2.imread(image))

        cv2.destroyAllWindows()
        video.release()


    def animate_all(self):

        self.filtered_plots.sort()
        self.plot_bucket = dict()

        for plot in self.filtered_plots:
            basename = os.path.basename(plot)
            element_list = basename.split('_')
            keyword = "_".join(element_list[1:])
            keyword = keyword[0:-4]
            if keyword in self.plot_bucket:
                self.plot_bucket[keyword].append(plot)
            else:
                self.plot_bucket[keyword] = [plot]

        for key in self.plot_bucket:
            self.create_animation(self.plot_bucket[key], key)
