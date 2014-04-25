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
from itertools import count

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

def iter_ptr_list(plist):
    """ Iterator for pointer list - to parse C array
        Source: github.com/Yaafe/Yaafe/blob/master/src_python/yaafelib/core.py
    """
    for i in count(0):
        if not plist[i]:
            raise StopIteration
        yield plist[i]

def get_tessdata_prefix():
    """Return prefix for tessdata based on enviroment variable
    """
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
        libname = LIBPATH + 'libtesseract.so.3.0.3'
        libname_alt = 'libtesseract.so.3'

    try:
        tesseract = ctypes.cdll.LoadLibrary(libname)
    except OSError:
        try:
            tesseract = ctypes.cdll.LoadLibrary(libname_alt)
        except OSError, err:
            print('Loading of %s failed...' % libname)
            print('Loading of %s failed...' % libname_alt)
            print(err)
            return
    return tesseract

def get_version():
    """ Get tesseract version
    """
    tesseract = get_tesseract()
    if not tesseract:
        return

    tesseract.TessVersion.restype = ctypes.c_char_p
    tesseract.TessVersion.argtypes = []
    return tesseract.TessVersion()

def get_list_of_langs(tesseract=None, api = None):
    """ Get tesseract version
    """
    if not tesseract:
        tesseract = get_tesseract()
        if not tesseract:
            return
    if not api:
        api = tesseract.TessBaseAPICreate()

    # check if tesseract was inited => list of languages is availabe only after
    # tesseract init
    tesseract.TessBaseAPIGetInitLanguagesAsString.restype = ctypes.c_char_p
    init_lang = tesseract.TessBaseAPIGetInitLanguagesAsString(api)
    if not init_lang:
        tesseract.TessBaseAPIInit3(api, None, None)

    get_langs = tesseract.TessBaseAPIGetAvailableLanguagesAsVector
    get_langs.restype = ctypes.POINTER(ctypes.c_char_p)
    langs_p = get_langs(api)
    langs = []
    if langs_p:
        for lang in iter_ptr_list(langs_p):
            langs.append(lang)
    return sorted(langs)


def main():
    """Run a simple test
    """
    version = get_version()
    if version:
        print 'Found tesseract OCR version %s' % version
        print 'Available languages:', get_list_of_langs()
    else:
        print 'Tesseract is not available'

if __name__ == '__main__':
    main()
