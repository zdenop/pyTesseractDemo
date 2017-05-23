#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Zdenko Podobný 2014-2017
# Licensed under the terms of the MIT License

""" Custom QGraphicsScene
"""

from PyQt5.QtWidgets import (QGraphicsScene)
from PyQt5.QtCore import (pyqtSignal)


class CustomGraphicsScene(QGraphicsScene):
    dropped = pyqtSignal('QString')

    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)

    def dragMoveEvent(self, event):
        """ Drag Move event must be implemented othewise dropEvent will not be
            called
        """
        event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls.count:
            fname = urls[0].toLocalFile()
            self.dropped.emit(fname)
