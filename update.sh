#!/bin/bash

cd ~/repos/spruce-budworm
rm -rv build/*
rm -rv dist/*

python setup.py bdist_wheel
cd ~/repos/spruce-budworm/dist
pip uninstall -y bugtracker
pip install bugtracker-*

echo "Reinstall complete"
