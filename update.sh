#!/bin/bash

cd ~/repos/bugtracker
rm -rv build/*
rm -rv dist/*

python setup.py bdist_wheel
cd ~/repos/bugtracker/dist
pip uninstall -y bugtracker
pip install bugtracker-*

echo "Reinstall complete"
