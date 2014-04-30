#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 10:10:00 2014

@author: zdenko.podobny
"""

from sys import platform
from os import path, environ, name
from PyQt4.QtCore import QSettings, QVariant
from PyQt4.QtGui import QDesktopServices

APPGROUP = u'tesseract'
conFile = u'pyTesseractDemo.ini'

def configFile():
    if platform.startswith("win") or name == "nt":
        try:
            import pywintypes
            try:
                from win32com.shell import shell, shellcon
                appdata = shell.SHGetSpecialFolderPath(0, \
                                                        shellcon.CSIDL_APPDATA)
            except pywintypes.com_error:
                appdata = environ['APPDATA']
        except ImportError:
            appdata = path.join(environ['APPDATA'], )
    else:
        appdata = path.expanduser(path.join("~", ".config/"))
    appdata = unicode(appdata)
    #appdata = QDesktopServices.storageLocation(QDesktopServices.DataLocation)
    #config = unicode(appdata + QDir.separator() + conFile')
    return path.join(appdata, APPGROUP, conFile)

def storeSetting(name, value):
    """Store setting to config file
    """
    settings = QSettings(configFile(), QSettings.IniFormat)
    settings.setValue(name, QVariant(value))

def readSetting(name):
    """Return stored setting value
    """
    settings = QSettings(configFile(), QSettings.IniFormat)
    # ByteArray
    if name in ('geometry', 'state', 'splitter_1Sizes', 'splitter_2Sizes'):
        return settings.value(name)
    elif name == 'images/input_dir':
        return str(settings.value(name,\
                              QDesktopServices.storageLocation(
                              QDesktopServices.DesktopLocation)).toString())
    elif name == 'images/last_filename':
        return str(settings.value(name, r'images/phototest.tif').toString())
    elif name == 'language':
        # default value 'eng'
        return str(settings.value(name, 'eng').toString())
    else:
        # Return name value as string or empty string if name does not exist
        return str(settings.value(name, "").toString())

##############################################################################
def main():
    """Test module functionality
    """
    print 'starting tests...'
    home_dir = QDesktopServices.storageLocation(QDesktopServices.HomeLocation)
    print 'Home dir is:', home_dir
    print 'configFile:', configFile()
    print 'Input durectory is: ', readSetting('images/input_dir')
    print 'Last used filename is: ', readSetting('images/last_filename')
    print 'language:', readSetting('language'), type(readSetting('language')),
    print 'tests ended...'

if __name__ == '__main__':
    main()