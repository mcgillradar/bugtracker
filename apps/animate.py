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