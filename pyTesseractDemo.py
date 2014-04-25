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
                         QGraphicsScene,
                         QPixmap, QColor, QPen, QBrush, QTextCursor, QStyle)
from PyQt4.QtCore import (Qt, QCoreApplication, pyqtSignature)

from ui.ui_mainwindow import Ui_MainWindow

import libs.tesstool as tess
import libs.lepttool as lept

# Demo variables
IMAGE_NAME =  r'images/phototest.tif'
LANG = 'eng'


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
        quit_icon = QApplication.style().standardIcon(
                        QStyle.SP_DialogCloseButton)
        self.pushButtonQuit.setIcon(quit_icon)
        self.setWindowTitle('Analyze & ORC image with tesseract and leptonica')
        self.resize(1150, 950)

        for idx, psm in enumerate(tess.PSM):
            self.comboBoxPSM.addItem(psm, idx)
        for idx, ril in enumerate(tess.RIL):
            self.comboBoxRIL.addItem(ril, idx)
        # Default values
        self.comboBoxPSM.setCurrentIndex(1)
        self.comboBoxRIL.setCurrentIndex(2)

        self.leptonica = lept.get_leptonica()
        if not self.leptonica:
            self.show_msg('Leptonica initialization failed...')

        self.box_data = []
        self.pix_image = False
        self.image_name = None
        self.lang = LANG

        # Create tesseract api
        self.tesseract = tess.get_tesseract()
        if not self.tesseract:
            self.show_msg('Tesseract initialization failed...')
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
        self.show_msg('Tesseract initialized with language \'%s\'.' % \
                      self.lang)

        # populate language selector
        available_languages = tess.get_list_of_langs(self.tesseract, self.api)
        for lang in available_languages:
            self.comboBoxLang.addItem(lang, lang)
        self.load_image(IMAGE_NAME)

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
            result_text = ctypes.string_at(ocr_result)
            conf = self.tesseract.TessBaseAPIMeanTextConf(self.api)
            self.show_msg('Box[%d]: x=%d, y=%d, w=%d, h=%d, ' \
                         'confidence: %d, ' \
                         'text: <span style="color:blue">%s</span>' % \
                         (item, box.x, box.y, box.w, box.h,
                          conf,
                          result_text.strip()))
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
        self.image_name = filename
        self.scene.addPixmap(QPixmap(filename))
        self.setWindowTitle('Analyze & ORC image with tesseract and ' \
                            'leptonica :: %s' % filename)

        # Read image with leptonica => create PIX structure and report image
        # size info
        # filename must be c-string
        self.pix_image = self.leptonica.pixRead(str(filename))
        self.show_msg("image width: %d" % \
                     self.leptonica.pixGetWidth(self.pix_image))
        self.show_msg("image height: %d" % \
                     self.leptonica.pixGetHeight(self.pix_image))
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

def main():
    """Start GUI
    """
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
