#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
   Simple python demo of tesseract-ocr
"""
# https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg20541.html
# http://pastebin.com/DhPUgrAj

__author__ = u'Zdenko Podobný <zdenop@gmail.com>'
__version__ = '0.1'
__date__ = '22.04.2014'

import os
import sys
import ctypes
import locale

from PyQt4.QtGui import (QApplication, QMainWindow, QStyleFactory, QFileDialog,
                         QPixmap, QColor, QPen, QBrush, QTextCursor, QStyle,
                         QGraphicsScene, QTransform)
from PyQt4.QtCore import (Qt, QCoreApplication, pyqtSignature, SIGNAL, QObject,
                          QVariant, QEvent)

from ui.ui_mainwindow import Ui_MainWindow

import libs.tesstool as tess
import libs.lepttool as lept
import libs.settings as sett


class MainWindow(QMainWindow, Ui_MainWindow):
    """Class For MainWindow
    """
    def __init__(self, parent=None):
        """ Constructor
        """
        super(MainWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        QApplication.setStyle(QStyleFactory.create('cleanlooks'))
        self.setupUi(self)
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        self.scene.installEventFilter(self)
        self.graphicsView.setBackgroundBrush(QBrush(Qt.gray, Qt.BDiagPattern))
        quit_icon = QApplication.style().standardIcon(
                        QStyle.SP_DialogCloseButton)
        self.pushButtonQuit.setIcon(quit_icon)
        self.setWindowTitle('Analyze & ORC image with tesseract and leptonica')
        self.actionZoomOut.triggered.connect(self.zoomOut)
        self.actionZoomIn.triggered.connect(self.zoomIn)
        self.actionZoomTo1.triggered.connect(self.zoomTo1)
        self.connect(self.actionZoomFit, SIGNAL('triggered()'), self.zoomFit)

        # Initialize variables and pointers
        self.box_data = []
        self.pix_image = False
        self.image_width = 0
        self.image_height = 0
        self.tesseract = None
        self.api = None
        self.lang = 'eng'

        lang = sett.readSetting('language')
        if lang:
            self.lang = lang

        self.initialize_tesseract()
        if self.tesseract:
            available_languages = tess.get_list_of_langs(self.tesseract,
                                                         self.api)
            for lang in available_languages:
                self.comboBoxLang.addItem(lang, lang)
            current_index = self.comboBoxLang.findData(self.lang)
            if current_index:
                self.comboBoxLang.setCurrentIndex(current_index)

        for idx, psm in enumerate(tess.PSM):
            self.comboBoxPSM.addItem(psm, idx)
        for idx, ril in enumerate(tess.RIL):
            self.comboBoxRIL.addItem(ril, idx)

        self.leptonica = lept.get_leptonica()
        if not self.leptonica:
            self.show_msg('Leptonica initialization failed...')

        # Read settings and set default values
        geometry = sett.readSetting('settings_geometry')
        if geometry is not None:
            self.restoreGeometry(QVariant(geometry).toByteArray())
        else:
            self.resize(1150, 950)
        state = sett.readSetting('state')
        if state is not None:
            self.restoreState(QVariant(state).toByteArray())
        sp_1_state = sett.readSetting('splitter_1Sizes')
        if sp_1_state is not None:
            self.splitter_1.restoreState(QVariant(sp_1_state).toByteArray())
        sp_2_state = sett.readSetting('splitter_2Sizes')
        if sp_2_state is not None:
            self.splitter_2.restoreState(QVariant(sp_2_state).toByteArray())
        psm = sett.readSetting('PSM')
        if psm:
            current_index = self.comboBoxPSM.findData(psm)
            self.comboBoxPSM.setCurrentIndex(current_index)
        ril = sett.readSetting('RIL')
        if ril:
            current_index = self.comboBoxRIL.findData(ril)
            self.comboBoxRIL.setCurrentIndex(current_index)

        image_name = sett.readSetting('images/last_filename')
        if image_name:
            self.image_name = image_name
        self.load_image(image_name)
        zoom_factor = sett.readSetting('images/zoom_factor')
        self.setZoom(zoom_factor)


    def initialize_tesseract(self):
        """Create tesseract api
        """
        self.tesseract = tess.get_tesseract(os.path.dirname(__file__))
        if not self.tesseract:
            self.show_msg('Tesseract initialization failed...')
            return
        self.api = self.tesseract.TessBaseAPICreate()
        tessdata_prefix = tess.get_tessdata_prefix()
        #current_locale = locale.getlocale()  # Save current locale
        # Switch to C locale to handle
        #  Error: Illegal min or max specification!
        #  "Fatal error encountered!" == NULL:Error:Assert failed:in file
        #   ../../tesseract-ocr/ccutil/globaloc.cpp, line 75
        locale.setlocale(locale.LC_ALL, 'C')
        retc = self.tesseract.TessBaseAPIInit3(self.api,
                                                   tessdata_prefix,
                                                   self.lang)
        # Restore saved locale
        # locale.setlocale(locale.LC_ALL, current_locale)
        if (retc):
            self.tesseract.TessBaseAPIDelete(self.api)
            self.show_msg('<span style="color:red">Could not initialize ' \
                         'tesseract.</span>')
            return
        self.show_msg('Tesseract %s initialized with language \'%s\'.' % \
                      (tess.VERSION, self.lang))


    @pyqtSignature('')
    def on_pushButtonShow_pressed(self):
        """Display rectangles
        """
        tessdata_prefix = tess.get_tessdata_prefix()
        locale.setlocale(locale.LC_ALL, 'C')
        retc = 0
        if self.lang != str(self.comboBoxLang.currentText()):
            self.lang = str(self.comboBoxLang.currentText())
            retc = self.tesseract.TessBaseAPIInit3(self.api,
                                                   tessdata_prefix,
                                                   self.lang)
            self.show_msg('Using language \'%s\'.' % self.lang)
        if (retc):
            self.tesseract.TessBaseAPIDelete(self.api)
            self.show_msg('<span style="color:red">Could not re-initialize ' \
                         'tesseract.</span>')
            return

        # Shut up tesseract - there could be a lot of unwanted messages
        #tesseract.TessBaseAPISetVariable(api, "debug_file", "/dev/null")

        self.tesseract.TessBaseAPIClear(self.api)
        # Set PIX structure to tesseract api
        self.tesseract.TessBaseAPISetImage2(self.api, self.pix_image)

        self.tesseract.TessBaseAPISetPageSegMode(self.api,
                                            self.comboBoxPSM.currentIndex())

        # Get info(BOXA structure) about lines(RIL_TEXTLINE) from image in api
        boxa = self.tesseract.TessBaseAPIGetComponentImages(self.api,
                                            self.comboBoxRIL.currentIndex(),
                                            1, None, None)
        if not boxa:
            self.show_msg('No component found. Try to change PSM or RIL.')
            return

        # Get info about number of items on image
        n_items = self.leptonica.boxaGetCount(boxa)
        psm = tess.PSM[self.comboBoxPSM.currentIndex()]
        ril = tess.RIL[self.comboBoxRIL.currentIndex()]
        self.show_msg('<span style="color:green">' \
                     'Found %d image components with %s and %s.</span>' % \
                     (n_items, psm, ril))

        ocr_psm = tess.PSM_SINGLE_BLOCK
        if ril == 'RIL_PARA':
            ocr_psm = tess.PSM_SINGLE_BLOCK
        elif ril == 'RIL_TEXTLINE':
            ocr_psm = tess.PSM_SINGLE_LINE
        elif ril == 'RIL_WORD':
            ocr_psm = tess.PSM_SINGLE_WORD
        elif ril == 'RIL_SYMBOL':
            ocr_psm = tess.PSM_SINGLE_CHAR
        self.tesseract.TessBaseAPISetPageSegMode(self.api, ocr_psm)

        # Set up result type (BOX structure) for leptonica function boxaGetBox
        self.leptonica.boxaGetBox.restype = lept.BOX_PTR_T
        self.leptonica.boxaGetBox.argtypes = []
        n_boxes = len(self.box_data)
        if n_boxes:
            for idx in xrange(n_boxes):
                self.scene.removeItem(self.box_data[idx])

        # Display items and print its info
        box_items = []
        for item in range(0, n_items):
            lept_box = self.leptonica.boxaGetBox(boxa, item, lept.L_CLONE)
            box = lept_box.contents
            self.tesseract.TessBaseAPISetRectangle(self.api,
                                              box.x, box.y, box.w, box.h)
            ocr_result = self.tesseract.TessBaseAPIGetUTF8Text(self.api)
            result_text = ctypes.string_at(ocr_result).decode('utf-8').strip()
            conf = self.tesseract.TessBaseAPIMeanTextConf(self.api)
            self.show_msg('Box[%d]: x=%d, y=%d, w=%d, h=%d, ' \
                          'confidence: %d, ' \
                          'text: <span style="color:blue">%s</span>' % \
                          (item, box.x, box.y, box.w, box.h,
                           conf, result_text
                          ))
            box_items.append(self.scene.addRect(box.x, box.y, box.w, box.h,
                               QPen(QColor(255, 0, 0, 255)),
                               QBrush(QColor(255, 0, 0, 100))))
            box_items[item].setAcceptHoverEvents(True)
            box_items[item].setToolTip("Box[%d]: confidence:%s, text:%s" % \
                                      (item, conf, result_text))
        QCoreApplication.processEvents()
        self.box_data = box_items

    @pyqtSignature('')
    def on_pushButtonLoad_pressed(self):
        """Load Image
        """
        image = QFileDialog.getOpenFileName(self,
                    'Open Image file',
                    './',
                    'Images (*.jpg *.jpeg *.bmp *.png *.tiff *.tif *.gif);;' \
                    'All files (*.*)')

        if not image:
            self.show_msg(u"File was not selected…")
            return
        self.load_image(image)

    @pyqtSignature('')
    def on_pushButtonRestart_pressed(self):
        """Restart program
        """
        python = sys.executable
        os.execl(python, python, * sys.argv)

    def load_image(self, filename):
        """Load image to scene and create PIX
        """
        self.scene.clear()
        self.zoomTo1()
        self.image_name = str(filename)  # filename must be c-string
        self.scene.addPixmap(QPixmap(filename))

        self.setWindowTitle('Analyze & ORC image with tesseract and ' \
                            'leptonica :: %s' % os.path.basename(self.image_name))
        # Read image with leptonica => create PIX structure and report image
        # size info
        self.pix_image = self.leptonica.pixRead(self.image_name)
        self.image_width = self.leptonica.pixGetWidth(self.pix_image)
        self.image_height = self.leptonica.pixGetHeight(self.pix_image)
        self.show_msg("image size: %dx%d, resolution %dx%d" % \
                     (self.image_width,
                      self.image_height,
                      self.leptonica.pixGetXRes(self.pix_image),
                      self.leptonica.pixGetYRes(self.pix_image)
                     ))
        self.box_data = []

    def show_msg(self, message):
        """Show message in textBrowser
        """
        self.textEdit.append(message)
        # Scroll to end of the last message
        cursor = QTextCursor(self.textEdit.textCursor())
        cursor.movePosition(QTextCursor.End)
        self.textEdit.setTextCursor(cursor)
        QApplication.processEvents()

    def closeEvent(self, event):
        """Store setting on exit
        """
        sett.storeSetting('geometry', self.saveGeometry())
        sett.storeSetting('state', self.saveState())
        sett.storeSetting("splitter_1Sizes", self.splitter_1.saveState());
        sett.storeSetting("splitter_1Geo", self.splitter_1.saveGeometry());
        sett.storeSetting("splitter_2Sizes", self.splitter_2.saveState());
        sett.storeSetting('images/last_filename', self.image_name)
        sett.storeSetting('images/zoom_factor', self.getZoomFactor())
        row_l = self.comboBoxLang.currentIndex()
        lang = self.comboBoxLang.itemData(row_l).toString()
        if lang:
            sett.storeSetting('language', lang)
        row_p = self.comboBoxPSM.currentIndex()
        sett.storeSetting('PSM',
                          self.comboBoxPSM.itemData(row_p).toString())
        row_r = self.comboBoxRIL.currentIndex()
        sett.storeSetting('RIL',
                          self.comboBoxRIL.itemData(row_r).toString())
        QMainWindow.closeEvent(self, event)

    def setZoom(self, scale):
        """Scale to selected factor
        """
        transform = QTransform()
        transform.scale(scale, scale)
        self.graphicsView.setTransform(transform)

    def zoomFit(self):
        """Zoom image to fit in graphicsView window
        """
        # TODO: put border to preferencies
        border = 0.95
        if (not self.image_height) or (not self.image_width):
            return
        viewWidth = self.graphicsView.viewport().width() * border
        viewHeight = self.graphicsView.viewport().height() * border

        ratio = float(viewWidth / viewHeight)
        aspectRatio = float(self.image_width / self.image_height)

        if ratio > aspectRatio:
            zoomFactor = float(viewHeight / self.image_height)
        else:
            zoomFactor = float(viewWidth / self.image_width)
        self.setZoom(zoomFactor)

    def zoomTo1(self):
        """Zoom to 1:1
        """
        self.setZoom(1)

    def zoomIn(self):
        """Zoom In
        """
        factor = 1.25
        self.graphicsView.scale(factor, factor)

    def zoomOut(self):
        """Zoom Out
        """
        factor = .8
        self.graphicsView.scale(factor, factor)
        self.getZoomFactor()

    def getZoomFactor(self):
        """Get current zoom factor
        """
        return self.graphicsView.transform().m11()

    def eventFilter(self, obj, event):
        """Zoom In/Out with CTRL + mouse wheel
        """
        if event.type() == QEvent.GraphicsSceneWheel:
            assert isinstance(obj, QGraphicsScene)
            delta = event.delta()
            if (event.modifiers() == Qt.ControlModifier and delta > 0):
                factor = 1.41 ** (event.delta() / 240.0)
                self.graphicsView.scale(factor, factor)
                event.accept()
                return True
            elif (event.modifiers() == Qt.ControlModifier and delta < 0):
                factor = 1.41 ** (event.delta() / 240.0)
                self.graphicsView.scale(factor, factor)
                event.accept()
                return True
        return obj.eventFilter(obj, event)


def main():
    """Start GUI
    """
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
