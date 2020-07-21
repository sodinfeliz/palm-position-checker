import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pathlib import Path
from pkgs.mainGUI import mainGUI


if __name__ == '__main__':
    data_path = Path.cwd().joinpath('data')
    app = QApplication(sys.argv)
    app.setOverrideCursor(Qt.ArrowCursor)
    widget = mainGUI(data_path)
    widget.show()
    app.exec_()
