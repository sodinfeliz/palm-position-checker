from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi


class UI_segment(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('GUI/segdialogGUI.ui', self)
        self.setWindowTitle('')
        self.setFixedSize(self.width(), self.height())

        self.pb_yes.clicked.connect(self.accept)
        self.pb_no.clicked.connect(self.reject)


