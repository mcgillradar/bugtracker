#!/bin/bash


rm -rv build/*
rm -rv dist/*

python setup.py bdist_wheel
cd ./dist
pip uninstall -y bugtracker
pip install bugtracker-*

echo "Reinstall complete"
