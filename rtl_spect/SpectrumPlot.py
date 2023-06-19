
from typing import Dict
from copy import deepcopy
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QSize, Qt
from PyQt6.QtGui import QColor, QPaintEvent, QMouseEvent, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget


class SpectrumPlot(QWidget):
    cursor_move = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._x_min = 120e6
        self._x_max = 160e6
        self._y_min = -90
        self._y_max = 0
        self._bg_color = QColor("#222")
        self._grid_color = QColor("#777")
        self._label_color = QColor("#fff")
        self._line_color = QColor("#ff0")
        self._cursor_color = QColor("#f0f")
        self._vcursor_color = QColor("#fff")
        self._x_title = "Frequency (MHz)"
        self._x_scaler = 1e6
        self._x_decimals = 1
        self._x_step = None
        self._y_title = "Relative Gain (dB)"
        self._y_scaler = 1
        self._y_decimals = 0
        self._y_step = None
        self._padding = 10
        self._client_rect = (0, 0, 0, 0)
        self._cursor_pos = None
        self._vcursor_pos = None
        self._baseline = None
        self.setMouseTracking(True)

    @pyqtSlot()
    def minimumSizeHint(self) -> QSize:
        return QSize(100, 100)

    @pyqtSlot()
    def sizeHint(self) -> QSize:
        return super().sizeHint()

    def set_x_lim(self, xmin, xmax):
        if xmin < xmax:
            self._x_min = xmin
            self._x_max = xmax
            self.update()

    def set_y_lim(self, ymin, ymax):
        if ymin < ymax:
            self._y_min = ymin
            self._y_max = ymax
            self.update()

    def add_data(self, new_data: Dict[float, float]):
        self._data |= new_data
        self.update()

    def clear_data(self):
        self._data = {}
    
    def set_vcursor(self, pos):
        self._vcursor_pos = pos
    
    def save_baseline(self):
        self._baseline = deepcopy(self._data)
        self.update()

    def reset_baseline(self):
        self._baseline = None
        self.update()

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        l, t, r, b = self._client_rect
        x = a0.pos().x()
        y = a0.pos().y()
        if x >= l and x <= r and y >= t and y <= b:
            self._cursor_pos = (x, y)
            px = (x - l) / (r - l) * (self._x_max - self._x_min) + self._x_min
            py = (y - b) / (t - b) * (self._y_max - self._y_min) + self._y_min
            self.cursor_move.emit((px, py))
        else:
            self._cursor_pos = None
        self.update()

    @staticmethod
    def _make_labels(llim, ulim, step, scal, dec):
        pos = []
        lbl = []
        x = llim
        while x < ulim:
            lbl.append(((x - llim) / (ulim - llim), f"{(x / scal):.{dec}f}"))
            x += step
        # add the upper limit point
        lbl.append((1, f"{(ulim / scal):.{dec}f}"))
        return lbl

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)

        # clear background
        painter.fillRect(self.rect(), self._bg_color)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._x_step is None:
            x_step = (self._x_max - self._x_min) / 10
        else:
            x_step = self._x_step

        if self._y_step is None:
            y_step = (self._y_max - self._y_min) / 10
        else:
            y_step = self._y_step

        x_labels = self._make_labels(
            self._x_min, self._x_max, x_step, self._x_scaler, self._x_decimals
        )
        y_labels = self._make_labels(
            self._y_min, self._y_max, y_step, self._y_scaler, self._y_decimals
        )
        x_label_width = max(
            self.fontMetrics().horizontalAdvance(l) for _, l in x_labels
        )
        x_label_height = self.fontMetrics().height()
        y_label_width = max(
            self.fontMetrics().horizontalAdvance(l) for _, l in y_labels
        )
        y_label_height = self.fontMetrics().height()

        x_title_width = self.fontMetrics().horizontalAdvance(self._x_title)
        x_title_height = self.fontMetrics().height()
        y_title_width = self.fontMetrics().horizontalAdvance(self._y_title)
        y_title_height = self.fontMetrics().height()

        # calculate drawing area
        left = 2 * self._padding + x_label_width + y_title_height
        top = 2 * self._padding
        right = self.width() - 2 * self._padding
        bottom = self.height() - 2 * self._padding - y_label_height - x_title_height
        self._client_rect = (left, top, right, bottom)

        # draw axis titles
        painter.setPen(self._label_color)
        painter.drawText(
            int((right - left) / 2 + left - x_title_width / 2),
            int(bottom + x_label_height + self._padding),
            x_title_width,
            x_title_height,
            Qt.AlignmentFlag.AlignCenter,
            self._x_title,
        )

        painter.save()
        painter.rotate(-90)
        painter.drawText(
            -int((bottom - top) / 2 + y_title_width / 2 + top),
            int(self._padding),
            y_title_width,
            y_title_height,
            Qt.AlignmentFlag.AlignCenter,
            self._y_title,
        )
        painter.restore()

        # draw grid and labels
        for pos, lbl in x_labels:
            painter.setPen(self._label_color)
            painter.drawText(
                int(left + pos * (right - left) - x_label_width / 2),
                int(bottom + self._padding),
                x_label_width,
                x_label_height,
                Qt.AlignmentFlag.AlignCenter,
                lbl,
            )
            painter.setPen(self._grid_color)
            painter.drawLine(
                int(left + pos * (right - left)),
                int(bottom),
                int(left + pos * (right - left)),
                int(top),
            )

        for pos, lbl in y_labels:
            painter.setPen(self._label_color)
            painter.drawText(
                int(left - y_label_width - self._padding),
                int(top + (1 - pos) * (bottom - top) - y_label_height / 2),
                y_label_width,
                y_label_height,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                lbl,
            )
            painter.setPen(self._grid_color)
            painter.drawLine(
                int(left),
                int(top + (1 - pos) * (bottom - top)),
                int(right),
                int(top + (1 - pos) * (bottom - top)),
            )

        # draw data
        if self._data:
            pts = sorted(self._data.items())
            path = QPainterPath()
            x, y = pts[0]
            if self._baseline and x in self._baseline:
                y -= self._baseline[x]
            path.moveTo(
                (x - self._x_min) / (self._x_max - self._x_min) * (right - left) + left,
                (y - self._y_min) / (self._y_max - self._y_min) * (top - bottom)
                + bottom,
            )
            for x, y in pts[1:]:
                if self._baseline and x in self._baseline:
                    y -= self._baseline[x]
                path.lineTo(
                    (x - self._x_min) / (self._x_max - self._x_min) * (right - left)
                    + left,
                    (y - self._y_min) / (self._y_max - self._y_min) * (top - bottom)
                    + bottom,
                )
            painter.setPen(self._line_color)
            painter.drawPath(path)

        if self._vcursor_pos is not None:
            painter.setPen(self._vcursor_color)
            px = (self._vcursor_pos - self._x_min) / (self._x_max - self._x_min) * (right - left) + left
            painter.drawLine(int(px), top, int(px), bottom)

        if self._cursor_pos is not None:
            painter.setPen(self._cursor_color)
            painter.drawLine(self._cursor_pos[0], top, self._cursor_pos[0], bottom)
            painter.drawLine(left, self._cursor_pos[1], right, self._cursor_pos[1])

        painter.end()
