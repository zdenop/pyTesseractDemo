#!/bin/sh

pyuic4 ui/MainWindow.ui > ui/ui_mainwindow.py
pyrcc4 resources.qrc -o resources_rc.py