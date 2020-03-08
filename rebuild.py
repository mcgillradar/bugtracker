"""
rm -rv build/*
rm -rv dist/*

python setup.py bdist_wheel
cd ./dist
pip uninstall -y bugtracker
pip install bugtracker-*

echo "Reinstall complete"
"""

import os
import glob
import shutil
import subprocess

def empty_folder(folder):

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_package_name():

    pkgs = glob.glob("*.whl")

    if len(pkgs) != 1:
        raise ValueError("Multiple packages in dist.")

    return pkgs[0]

def rebuild():

    empty_folder("./build")
    empty_folder("./dist")

    subprocess.call("python setup.py bdist_wheel", shell=True)
    os.chdir("./dist")

    pkg_name = get_package_name()
    print(pkg_name)
    
    subprocess.call(f"pip uninstall -y {pkg_name}", shell=True)
    subprocess.call(f"pip install {pkg_name}", shell=True)

    print("Bugtracker installation complete.")


rebuild()