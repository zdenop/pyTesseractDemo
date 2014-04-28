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
from PyQt4.QtCore import (Qt, QCoreApplication, pyqtSignature, QVariant)

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
        quit_icon = QApplication.style().standardIcon(
                        QStyle.SP_DialogCloseButton)
        self.pushButtonQuit.setIcon(quit_icon)
        self.setWindowTitle('Analyze & ORC image with tesseract and leptonica')

        # Initialize variables and pointers
        self.box_data = []
        self.pix_image = False
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
        self.image_name = filename
        self.scene.addPixmap(QPixmap(filename))
        self.setWindowTitle('Analyze & ORC image with tesseract and ' \
                            'leptonica :: %s' % filename)

        # Read image with leptonica => create PIX structure and report image
        # size info
        # filename must be c-string
        self.pix_image = self.leptonica.pixRead(str(filename))
        self.show_msg("image size: %dx%d, resolution %dx%d" % \
                     (self.leptonica.pixGetWidth(self.pix_image),
                      self.leptonica.pixGetHeight(self.pix_image),
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
        sett.storeSetting('state', self.saveGeometry())
        sett.storeSetting('images/last_filename', self.image_name)
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


def main():
    """Start GUI
    """
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
