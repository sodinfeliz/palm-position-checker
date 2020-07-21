from PyQt5.QtWidgets import QMessageBox


def empty_firectory_error(fn, path):
    file_empty = QMessageBox()
    file_empty.setIcon(QMessageBox.Warning)
    file_empty.setText(f'Can\'t find the directory {fn} in {path}')
    file_empty.setWindowTitle('Warning')
    file_empty.setStandardButtons(QMessageBox.Ok)
    file_empty = file_empty.exec()


def empty_filename_error():
    file_empty = QMessageBox()
    file_empty.setIcon(QMessageBox.Warning)
    file_empty.setText("Filename is empty.")
    file_empty.setWindowTitle('Warning')
    file_empty.setStandardButtons(QMessageBox.Ok)
    file_empty = file_empty.exec()


def file_does_not_exist_error():
    file_empty = QMessageBox()
    file_empty.setIcon(QMessageBox.Warning)
    file_empty.setText("File doesn\'t exist.")
    file_empty.setWindowTitle('Warning')
    file_empty.setStandardButtons(QMessageBox.Ok)
    file_empty = file_empty.exec()

