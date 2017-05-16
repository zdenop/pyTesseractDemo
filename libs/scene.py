#!/usr/bin/python3
# -*- coding: utf-8 -*-

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
        print("Drop fired!")
        urls = event.mimeData().urls()
        print("urls", urls)
        if urls.count:
            fname = urls[0].toLocalFile()
            print("fname", fname)
            self.dropped.emit(fname)
