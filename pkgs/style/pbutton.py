from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def set_shadow_to_pb(pb, xOffset=0, yOffset=0, blurradius=5):
    effect = QGraphicsDropShadowEffect(pb)
    effect.setOffset(xOffset, yOffset)
    effect.setBlurRadius(blurradius)
    pb.setGraphicsEffect(effect)
