import os
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 40).__str__()

import cv2
import gdal
import numpy as np
import pandas as pd
import threading
from pathlib import Path
from glob import glob
from pandas import read_csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from scipy.spatial.distance import cdist

from .dialog.error import empty_firectory_error, empty_filename_error, file_does_not_exist_error
from .dialog.segdialog import UI_segment
from .style.pbutton import set_shadow_to_pb


def load_position_data(path):
    try:
        return np.array(read_csv(path))
    except:
        return np.empty([0, 2], dtype='int')


def resize_image(im_path: Path):
    pixel_size = 0.107541
    size_limitation = 20000.

    tfw = gdal.Open(str(im_path)).GetGeoTransform()
    im = cv2.imread(str(im_path))
    im_shape = np.array(im.shape[:2])

    # resize the image into resolution `pixel_size`
    im_reso_factor = tfw[1] / pixel_size if tfw[:2] != (0, 1) else 1
    im_reso_shape = (im_shape * im_reso_factor).astype('int')
    result = cv2.resize(im, (int(im_shape[1] * im_reso_factor),
                             int(im_shape[0] * im_reso_factor)))
    cv2.imwrite(str(im_path.parent.joinpath(f'{im_path.stem}_reso.tif')), result)

    im_size_factor = 1
    if any(im_reso_shape > size_limitation):
        im_size_factor = size_limitation / max(im_reso_shape)

    result = cv2.resize(im, (int(im_shape[1] * im_reso_factor * im_size_factor),
                             int(im_shape[0] * im_reso_factor * im_size_factor)))
    im_path = str(im_path.parent.joinpath(f'{im_path.stem}_resize.tif'))
    cv2.imwrite(im_path, result)

    return im_path, im_reso_shape, im_size_factor


class mainGUI(QDialog):    
    def __init__(self, data_path):
        super(mainGUI, self).__init__()
        loadUi('GUI/mainGUI.ui', self)
        self.setWindowTitle('Palm Position Checker')
        self.setFixedSize(self.width(), self.height())

        self._data_path = data_path
        self._add_point = False
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene()
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self._im_shape = []
        self._im_dir = ''
        self._factor = 0
        self._palm_pos = ''
        self._palm_pos_items = []

        self.view_canvas.setScene(self._scene)
        self.pb_filename.setEnabled(True)

        # connection between buttons and functions
        self.pb_filename.clicked.connect(self.canvas_initial)
        self.pb_zoomin.clicked.connect(self.zoom_in)
        self.pb_zoomout.clicked.connect(self.zoom_out)
        self.pb_loadcsv.clicked.connect(self.load_position)
        self.pb_save.clicked.connect(self.save_position)
        self.pb_prob.clicked.connect(self.save_prob_map)

        paleta = QPalette()
        paleta.setColor(QPalette.Base, QColor("black"))
        QToolTip.setFont(QFont('SansSerif', 10))
        QToolTip.setPalette(paleta)
        self.pb_zoomin.setToolTip('shortcut: \'s\'')
        self.pb_zoomout.setToolTip('shortcut: \'a\'')
        
        set_shadow_to_pb(self.pb_filename, 2, 2, 5)
        set_shadow_to_pb(self.pb_loadcsv, 2, 2, 5)
        set_shadow_to_pb(self.pb_save, 2, 2, 5)
        set_shadow_to_pb(self.pb_prob, 2, 2, 5)


    def canvas_initial(self):
        filename = self.lineEdit_filename.text()
        if filename:
            if filename in os.listdir(self._data_path):
                self._im_dir = self._data_path.joinpath(filename)
                im_path = self._im_dir.joinpath(f'{filename}.tif')

                if im_path.is_file():
                    im_path, self._im_shape, self._factor = resize_image(im_path)

                    self._clean_pos_items()
                    self.setPhoto(QPixmap(im_path))
                    self.pb_loadcsv.setEnabled(True)
                    self.pb_save.setEnabled(False)
                    self.pb_prob.setEnabled(False)
                    self._add_point = False
                    self.label_info.setText('Image Loaded.')

                else:
                    file_does_not_exist_error()
            else:
                empty_firectory_error(filename, self._data_path)
        else:
            empty_filename_error()


    def load_position(self):
        pos_path = self._im_dir.joinpath('palm_img_pos.csv')
        self._palm_pos = load_position_data(str(pos_path))
        self._palm_pos = np.rint(self._palm_pos*self._factor).astype(self._palm_pos.dtype)

        for x, y in self._palm_pos:
            self._palm_pos_items.append(self._add_item_to_scene(PosCircleItem(x, y, 'red')))

        self.pb_save.setEnabled(True)
        self._add_point = True
        self.label_info.setText('')


    def save_position(self):

        df = pd.DataFrame(np.rint(self._palm_pos/self._factor).astype('int'))
        df.to_csv(os.path.join(self._im_dir, 'palm_img_pos.csv'), header=None, index=None)
        self.label_info.setText("Save Done !")
        self.pb_prob.setEnabled(True)


    def save_prob_map(self):

        dialog_seg = UI_segment()
        dialog_seg.show()
        rsp = dialog_seg.exec_()  # 1: accepted, 0: rejected

        print(self._im_shape)
        output = np.zeros((self._im_shape[0], self._im_shape[1], 3), dtype='uint8')
        
        for pos in self._palm_pos:
            x, y = np.rint(pos / self._factor).astype('int')
            cv2.circle(output, (x, y), 20, (255, 255, 255), -1, cv2.LINE_AA)

        cv2.imwrite(os.path.join(self._im_dir, 'pr_palm.png'), output)
        self.label_info.setText("Save Map Done !")


    #########################################
    ###          Canvas Functions         ###
    #########################################

    def hasPhoto(self):
        return not self._empty

    
    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.view_canvas.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.view_canvas.transform().mapRect(QRectF(0, 0, 1, 1))
                self.view_canvas.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.view_canvas.viewport().rect()
                scenerect = self.view_canvas.transform().mapRect(rect)
                factor = max(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.view_canvas.scale(factor, factor)
            self._zoom = 0


    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.view_canvas.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.view_canvas.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()


    def zoom_in(self):
        if self.hasPhoto():
            factor = 1.25
            self._zoom += 1
            if self._zoom > 0:
                self.view_canvas.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0


    def zoom_out(self):
        if self.hasPhoto():
            factor = 0.8
            self._zoom -= 1
            if self._zoom > 0:
                self.view_canvas.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0    

                
    def toggleDragMode(self):
        if self.view_canvas.dragMode() == QGraphicsView.ScrollHandDrag:
            self.view_canvas.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.view_canvas.setDragMode(QGraphicsView.ScrollHandDrag)


    def keyPressEvent(self, event):
        if self._add_point:
            if event.text() == 's':
                self.zoom_in()
            elif event.text() == 'a':
                self.zoom_out()


    def mouseDoubleClickEvent(self, event):
        if self._add_point: 
            widget_x, widget_y = self.view_canvas.pos().x(), self.view_canvas.pos().y()
            pos = self.view_canvas.mapToScene(event.x() - widget_x, event.y() - widget_y)
            pos = [round(pos.x()), round(pos.y())]

            if len(self._palm_pos) == 0:
                self._palm_pos = np.vstack((self._palm_pos, pos))
                self._palm_pos_items.append(self._add_item_to_scene(PosCircleItem(pos[0], pos[1], 'red')))
            else:
                if cdist([pos], self._palm_pos).min() <= round(30*self._factor):
                    index = cdist([pos], self._palm_pos).argmin()
                    self._palm_pos = np.delete(self._palm_pos, index, axis=0)
                    self._scene.removeItem(self._palm_pos_items[index].item)
                    del self._palm_pos_items[index]
                else:
                    self._palm_pos = np.vstack((self._palm_pos, pos))
                    self._palm_pos_items.append(self._add_item_to_scene(PosCircleItem(pos[0], pos[1], 'red')))
            
            self.label_info.setText('')
            self.pb_prob.setEnabled(False)


    def _add_item_to_scene(self, it):
        self._scene.addItem(it.item)
        return it


    def _clean_pos_items(self):
        for it in self._palm_pos_items:
            self._scene.removeItem(it.item)
        self._palm_pos_items = []


class PosCircleItem():
    def __init__(self, x, y, color='red'):
        self.item = self._set_item(x, y, color)

    def _set_item(self, x, y, color):
        qt_colors = {'red': Qt.red, 'blue': Qt.blue}
        circle = QGraphicsEllipseItem(x-6, y-6, 12, 12)
        circle.setBrush(QBrush(qt_colors[color], style = Qt.SolidPattern))
        return circle


