#!/usr/bin/python
# coding: utf-8

from distutils.core import setup
import py2exe
import sys
import constants

# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

downloader_options = {
    "py2exe": {
        "compressed": 1,
        "optimize": 2,
        "ascii": 1,
        'includes' : 'cairo, pango, pangocairo, atk, gobject, gio',
    }
}

downloader = {
    'script':'downloader.py',
    'icon_resources': [(0, 'app_icon.ico')],
}

setup(
    name = constants.__app_name__,
    description = 'A Python downloader',
    version = constants.__version__,
    options = downloader_options,
    windows = [downloader],
    data_files=['app_icon.png',],
    #zipfile = None,
)
