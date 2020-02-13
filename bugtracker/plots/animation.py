"""
This module is a thin wrapper around ffmpeg
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
            keyword = element_list[1]
            if keyword in self.plot_bucket:
                self.plot_bucket[keyword].append(plot)
            else:
                self.plot_bucket[keyword] = [plot]

        for key in self.plot_bucket:
            print(key, len(self.plot_bucket[key]))

        # Starting just with joint plots
        joints = self.plot_bucket["joint"]
        joints.sort()

        self.create_animation(joints, "joint")