#!/usr/bin/python
# coding: utf-8

import os

def get_current_dir():
    return os.path.abspath(os.path.dirname(__file__))

def get_pixmaps_dir():
    return os.path.join(get_current_dir(), 'pixmaps')

def get_default_save_dir():
    f = './'
    home_dir = os.environ.get("HOME")
    if home_dir:
        f = os.path.join(os.environ.get("HOME"), "Downloads")
        if not os.path.exists(f):
            os.mkdir(f)
    return f

def convert_status_to_stock_id(status):
    status_dict = {
        "active": "gtk-go-down",
        "waiting": "gtk-refresh",
        "paused": "gtk-media-pause",
        "error": "gtk-dialog-error",
        "complete": "gtk-apply",
        "removed": "gtk-cancel"}
    return status_dict.get(status, "gtk-dialog-warning")

def bytes_to_human(b):
    b = float(b)
    if b<1024:
        return "%.1fB" % b
    else:
        kb = b/1024.0
        if kb<1024:
            return "%.1fKB" % kb
        else:
            mb = kb/1024.0
            if mb<1024:
                return "%.1fMB" % mb
            else:
                gb = mb/1024.0
                return "%.1fGB" % gb

def is_in_list(li, value):
    for v in li:
        if value == v:
            return True
    return False

if __name__ == '__main__':
    print get_current_dir()
    print get_pixmaps_dir()
