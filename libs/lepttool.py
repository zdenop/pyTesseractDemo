#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Library with tools related to leptonica

    Function pix_to_qimage based on Tom Powers code
"""

__author__ = u'Zdenko Podobný <zdenop@gmail.com>'
__version__ = '0.2'
__date__ = '03.05.2014'


import os
import sys
import ctypes

from PyQt4.QtGui import (QImage, qRgb)


LIBPATH = "/usr/local/lib64/"
LIBPATH_W = r'win32'

(L_INSERT, L_COPY, L_CLONE, L_COPY_CLONE) = map(ctypes.c_int, xrange(4))

# B&W Color Table.
_bwCT = [qRgb(255, 255, 255), qRgb(0, 0, 0)]

#Grayscale Color Table.
_grayscaleCT = [qRgb(i, i, i) for i in range(256)]

class BOX(ctypes.Structure):
    """ Leptonica box structure
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
            return None
    return leptonica

def pix_to_qimage(leptonica, pix_image):
    """ Convert leptonica PIX to QT QImage
    """
    # TODO(zdenop): 8509_001.4B.tif crash this -> implement PIX structure
    if not leptonica:
        return None
    width = leptonica.pixGetWidth(pix_image)
    height = leptonica.pixGetHeight(pix_image)
    depth = leptonica.pixGetDepth(pix_image)

    if depth == 1:
        image_format = QImage.Format_Mono
    elif depth == 8:
        image_format = QImage.Format_Indexed8
    elif depth == 32:
        image_format = QImage.Format_RGB32
    else:
        #  Convert other depths to 32
        pix_image = leptonica.pixConvertTo32(pix_image)
        image_format = QImage.Format_RGB32

    bytes_per_line = leptonica.pixGetWpl(pix_image) * 4
    image_datas = leptonica.pixEndianByteSwapNew(pix_image)
    datas = leptonica.pixGetData(image_datas)

    result = QImage(datas, width, height, bytes_per_line, image_format)

    result.setColorTable(_grayscaleCT)  # (depth == 8)
    if depth == 1:
        result.setColorTable(_bwCT)

    if result.isNull():
        none = QImage(0, 0, QImage.Format_Invalid)
        print 'Invalid format!!!'
        return none
    return result.rgbSwapped()

def get_version():
    """ Get tesseract version
    """
    leptonica = get_leptonica()
    if leptonica:
        leptonica.getLeptonicaVersion.restype = ctypes.c_char_p
        leptonica.getLeptonicaVersion.argtypes = []
        return leptonica.getLeptonicaVersion()
    return None


def main():
    """ Make a simple test
    """
    global LIBPATH_W
    LIBPATH_W = r'..\win32'
    leptonica_version = get_version()
    print 'Found %s' % leptonica_version
    leptonica = get_leptonica()
    pix_image = leptonica.pixRead(r'..\images\eurotext.tif')
    if pix_image:
        print 'w', leptonica.pixGetWidth(pix_image)
        print 'h', leptonica.pixGetHeight(pix_image)
        print 'd', leptonica.pixGetDepth(pix_image)
    else:
        print 'Image can not be openned'
    qimage = QImage()
    qimage = pix_to_qimage(leptonica, pix_image)
    if qimage:
        qimage.save(r'..\images\test.png')
    else:
        print "PIX conversion was not successful!"


if __name__ == '__main__':
    main()
