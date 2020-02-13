import os
import glob
import datetime
import argparse

import bugtracker
import bugtracker.config


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("stop", help="Data timestamp YYYYmmddHHMM")
    parser.add_argument("station", help="Station code")

    args = parser.parse_args()

    config = bugtracker.config.load("./bugtracker.json")

    manager = bugtracker.plots.animation.AnimationManager(config, args)
    manager.animate_all()

main()