#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Library with tools related to tesseract
"""

__author__ = u'Zdenko Podobný <zdenop@gmail.com>'
__version__ = '0.1'
__date__ = '22.04.2014'

import os
import sys
import ctypes

LIBPATH = '/usr/local/lib64/'
LIBPATH_W = r'..\win32'

# Define Page Iterator Levels
RIL = ['RIL_BLOCK', 'RIL_PARA', 'RIL_TEXTLINE', 'RIL_WORD', 'RIL_SYMBOL']

#Page Segmentation Modes
PSM = ['PSM_OSD_ONLY', 'PSM_AUTO_OSD', 'PSM_AUTO_ONLY', 'PSM_AUTO',
'PSM_SINGLE_COLUMN', 'PSM_SINGLE_BLOCK_VERT_TEXT', 'PSM_SINGLE_BLOCK',
'PSM_SINGLE_LINE', 'PSM_SINGLE_WORD', 'PSM_CIRCLE_WORD', 'PSM_SINGLE_CHAR',
'PSM_SPARSE_TEXT', 'PSM_SPARSE_TEXT_OSD']

(PSM_OSD_ONLY, PSM_AUTO_OSD, PSM_AUTO_ONLY, PSM_AUTO, PSM_SINGLE_COLUMN,
 PSM_SINGLE_BLOCK_VERT_TEXT, PSM_SINGLE_BLOCK, PSM_SINGLE_LINE,
 PSM_SINGLE_WORD, PSM_CIRCLE_WORD, PSM_SINGLE_CHAR, PSM_SPARSE_TEXT,
 PSM_SPARSE_TEXT_OSD, PSM_COUNT) = map(ctypes.c_int, xrange(14))

def get_tessdata_prefix():
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if not tessdata_prefix:
        tessdata_prefix = '../'
    return tessdata_prefix

def get_tesseract():
    """ Get tesseract handle
    """
    if sys.platform == 'win32':
        libname = os.path.join(LIBPATH_W, 'libtesseract303.dll')
        libname_alt = 'libtesseract303.dll'
        os.environ['PATH'] += os.pathsep + LIBPATH_W
    else:
        libname = LIBPATH + 'libtesseract.so.3.0.2'
        libname_alt = 'libtesseract.so.3'

    try:
        tesseract = ctypes.cdll.LoadLibrary(libname)
    except OSError:
        try:
            tesseract = ctypes.cdll.LoadLibrary(libname_alt)
        except WindowsError, err:
            print('Loading of %s failed...' % libname)
            print('Loading of %s failed...' % libname_alt)
            print(err)
            return
    return tesseract

def get_version():
    """ Get tesseract version
    """
    tesseract = get_tesseract()
    tesseract.TessVersion.restype = ctypes.c_char_p
    return tesseract.TessVersion()

def main():
    """Make a simple test
    """
    tesseract_version = get_version()
    print "Found tesseract OCR version %s" % tesseract_version

if __name__ == '__main__':
    main()