import os
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 40).__str__()

import cv2
import gdal
import numpy as np
import pandas as pd
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

from .dialog.error import warning_msg
from .op_segment_data_produce import save_train_data
from .item import PalmPositionCanvas


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


class mainGUI(QMainWindow):    
    def __init__(self):
        super(mainGUI, self).__init__()
        loadUi('GUI/mainGUI.ui', self)
        self.setWindowTitle('Palm Position Checker')
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._moveWidgetToCenter()

        self._im_shape = []
        self._im_dir = ''
        self._factor = 0
        self._palm_pos = ''

        # canvas initialization
        self.view_canvas = PalmPositionCanvas(self, (15, 47, 962, 850))
        
        # push buttons setting
        self.pb_openfile.clicked.connect(self.file_open)
        self.pb_loadcsv.clicked.connect(self.load_position)
        self.pb_save.clicked.connect(self.save_position)
        self.pb_prob.clicked.connect(self.save_prob_map)
        self.pb_dataset.clicked.connect(self.dataset_producing)

        self.le_crop_size.setPlaceholderText('Crop Size')
        self.le_overlap_ratio.setPlaceholderText('Overlap Ratio')


    def file_open(self):
        self._im_path, _ = QFileDialog.getOpenFileName(self, 'Open File')
        if not self._im_path:  # cancel button pressed
            return

        self._im_path = Path(self._im_path)
        self._im_dir = self._im_path.parent
        self._filename = self._im_dir.stem

        types = ['.png', '.jpeg', '.tif']
        if self._im_path.suffix not in types:
            warning_msg(f"The suffix {self._im_path.suffix} is not supported.")
        else:
            self.canvas_initial(Path(self._im_path))


    def canvas_initial(self, im_path):
        im_path, self._im_shape, self._factor = resize_image(im_path)

        self.view_canvas.setPhoto(im_path)
        self.view_canvas.set_factor(self._factor)
        self.view_canvas.set_add_point_mode(False)
        self.view_canvas.clean_all_pos_items()

        self.pb_dataset.setEnabled(False)
        self.pb_loadcsv.setEnabled(True)
        self.pb_save.setEnabled(False)
        self.pb_prob.setEnabled(False)
        self.le_crop_size.setEnabled(False)
        self.le_overlap_ratio.setEnabled(False)
        self.info_display.setText('Image Loaded.')


    def load_position(self):
        pos_path, _ = QFileDialog.getOpenFileName(self, 'Open File')
        
        if not pos_path:  # cancel button pressed
            return
        elif Path(pos_path).suffix != '.csv':
            warning_msg('Only supporting the csv extension.')

        self.view_canvas.initial_palm_pos(pos_path)
        self.pb_save.setEnabled(True)
        self.info_display.setText('')


    def save_position(self):
        df = pd.DataFrame(np.rint(self.view_canvas._palm_pos/self._factor).astype('int'))
        df.to_csv(os.path.join(self._im_dir, 'palm_img_pos.csv'), header=None, index=None)
        self.info_display.setText("Save Done !")
        self.pb_prob.setEnabled(True)


    def save_prob_map(self):
        output = np.zeros((self._im_shape[0], self._im_shape[1], 3), dtype='uint8')
        output_fn = self._im_dir.joinpath('pr_palm.png')
        
        for pos in self.view_canvas._palm_pos:
            x, y = np.rint(pos / self._factor).astype('int')
            cv2.circle(output, (x, y), 20, (255, 255, 255), -1, cv2.LINE_AA)

        output[output < 255] = 0 # cleaning the noise
        cv2.imwrite(str(output_fn), output)
        self.info_display.setText("Save Map Done !")
        self.le_crop_size.setEnabled(True)
        self.le_overlap_ratio.setEnabled(True)
        self.pb_dataset.setEnabled(True)


    def dataset_producing(self):
        self.info_display.setText("")
        
        try:
            crop_size = int(self.le_crop_size.text())
            overlap_ratio = float(self.le_overlap_ratio.text())
        except ValueError:
            if not self.le_crop_size.text():
                warning_msg('Crop size cell is empty.')
            elif not self.le_overlap_ratio.text():
                warning_msg('Overlap ratio cell is empty.')
            else:
                warning_msg("Crop size/Overlap ratio format invalid.")
            return

        if overlap_ratio < 0 or overlap_ratio >= 1:
            warning_msg("Overlap Ratio must in range [0,1).")
            return

        im_path = self._im_dir.joinpath(f'{self._im_dir.stem}_reso.tif')
        label_path = self._im_dir.joinpath('pr_palm.png')
        save_train_data(im_path, label_path, crop_size, overlap_ratio)
        self.info_display.setText("Dataset Completed !")

    
    def _moveWidgetToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

