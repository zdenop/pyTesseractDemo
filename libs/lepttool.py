#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Library with tools related to leptonica
"""

__author__ = u'Zdenko Podobný <zdenop@gmail.com>'
__version__ = '0.1'
__date__ = '22.04.2014'

import os
import sys
import ctypes

LIBPATH = "/usr/local/lib64/"
LIBPATH_W = r'win32'

(L_INSERT, L_COPY, L_CLONE, L_COPY_CLONE) = map(ctypes.c_int, xrange(4))

class BOX(ctypes.Structure):
    """Leptonica box structure
    """
    _fields_ = [
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
        ("w", ctypes.c_int32),
        ("h", ctypes.c_int32),
        ("refcount", ctypes.c_uint32)
    ]

BOX_PTR_T = ctypes.POINTER(BOX)

def get_leptonica():
    """ Get leptonica handle
    """
    if sys.platform == "win32":
        leptlib = os.path.join(LIBPATH_W, 'liblept170.dll')
        leptlib_alt = "liblept170.dll"
        os.environ["PATH"] += os.pathsep + LIBPATH_W
    else:
        leptlib = LIBPATH + "liblept.so.4.0.0"
        leptlib_alt = 'liblept.so'

    try:
        leptonica = ctypes.cdll.LoadLibrary(leptlib)
    except OSError:
        try:
            leptonica = ctypes.cdll.LoadLibrary(leptlib_alt)
        except WindowsError, err:
            print("Loading of '%s failed..." % leptlib)
            print("Loading of '%s failed..." % leptlib_alt)
            print(err)
            return
    return leptonica

def get_version():
    """ Get tesseract version
    """
    leptonica = get_leptonica()
    leptonica.getLeptonicaVersion.restype = ctypes.c_char_p
    leptonica.getLeptonicaVersion.argtypes = []
    return leptonica.getLeptonicaVersion()

def main():
    """Make a simple test
    """
    leptonica_version = get_version()
    print "Found %s" % leptonica_version

if __name__ == '__main__':
    main()
