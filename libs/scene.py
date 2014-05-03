#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

class CustomGraphicsScene(QtGui.QGraphicsScene):
    def __init__(self, parent = None):
        QtGui.QGraphicsScene.__init__(self, parent)

    def dragMoveEvent(self, event):
        """ Drag Move event must be implemented othewise dropEvent will not be
            called
        """
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        print("Drop fired!")
        urls = event.mimeData().urls()
        print "urls", urls
        if urls.count:
            fname = urls[0].toLocalFile();
            print "fname", fname
            self.emit(QtCore.SIGNAL("dropped_to_scene(QString)"), fname)
#            self.parent.emit(QtCore.SIGNAL("commitItemInserted(QString*, QString*)"),
#                        fname, self.parent)
#                  QString(event.mimeData().text())
#            self._parent.emit(SIGNAL("commitItemInserted(QString*, QString*)"),
#                  QString(event.mimeData().text()), self._parent.branch)

