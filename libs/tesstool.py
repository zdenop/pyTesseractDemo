#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Library with tools related to tesseract
"""

__author__ = u'Zdenko Podobný <zdenop@gmail.com>'
__version__ = '0.1'
__date__ = '22.04.2014'

import os
import sys
import ctypes
from ctypes.util import find_library
from itertools import count

LIBPATH = '/usr/local/lib64/'
VERSION = ''

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
 PSM_SPARSE_TEXT_OSD, PSM_COUNT) = map(ctypes.c_int, range(14))

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

def get_tesseract(search_path='.'):
    """ Get tesseract handle
    """
    if sys.platform == 'win32':
        lib_name = 'libtesseract303'
        _path = os.environ['PATH']
        for _dir in ['', 'win32', '..' , '..\win32']:
            temp_path = os.path.join(search_path, _dir)
            os.environ['PATH'] = _path + os.pathsep + temp_path
            lib_path = find_library(lib_name)
            if not lib_path is None:
                lib_path = os.path.realpath(lib_path)
                print("found", lib_path)
                break
    else:
        lib_name = 'libtesseract.so.3'
        lib_path = LIBPATH + 'libtesseract.so.3.0.3'

    try:
        tesseract = ctypes.cdll.LoadLibrary(lib_name)
    except OSError:
        try:
            tesseract = ctypes.cdll.LoadLibrary(lib_path)
        except OSError as err:
            print('Loading of %s failed...' % lib_name)
            print('Loading of %s failed...' % lib_path)
            print(err)
            return

    global VERSION
    VERSION = get_version(tesseract)
    return tesseract

def get_version(tesseract=None):
    """ Get tesseract version
    """
    if not tesseract:
        tesseract = get_tesseract()
    if not tesseract:
        return

    tesseract.TessVersion.restype = ctypes.c_char_p
    tesseract.TessVersion.argtypes = []
    return tesseract.TessVersion().decode('utf-8')

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
        try:
            tesseract.TessBaseAPIInit3(api, None, None)
        except OSError as error:
            print('Can not initialize tesseract:', error)
            return None

    get_langs = tesseract.TessBaseAPIGetAvailableLanguagesAsVector
    get_langs.restype = ctypes.POINTER(ctypes.c_char_p)
    langs_p = get_langs(api)
    langs = []
    if langs_p:
        for lang in iter_ptr_list(langs_p):
            langs.append(lang.decode('utf-8'))
    return sorted(langs)


def main():
    """Run a simple test
    """
    version = get_version()
    if version:
        print('Found tesseract OCR version %s' % version)
        print('Available languages:', get_list_of_langs())
    else:
        print('Tesseract is not available')

if __name__ == '__main__':
    main()
