#!/bin/sh

pyuic5 ui/MainWindow.ui > ui/ui_mainwindow.py
pyrcc5 resources.qrc -o resources_rc.py
