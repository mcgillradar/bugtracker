#!/bin/bash

echo "Demonstrating shell wrapper:"

# Demonstration of a bash wrapper for bugtracker

cd /home/spruce/repos/spruce-budworm/apps/
~/miniconda3/envs/bugtracker/bin/python calib.py 201806121500 xam
