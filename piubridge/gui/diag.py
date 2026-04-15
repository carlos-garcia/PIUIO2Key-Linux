"""
Diagnostics window: visualizes the PIU pad with live button state.

Panels light up red when pressed. The layout mirrors the arcade pad:

    UL  UR
      CTR
    DL  DR

Plus the TEST and SERVICE cabinet buttons below.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class DiagWindow(QWidget):
    """Qt widget showing the PIU pad layout with live highlighting."""

    # (bit_index, label, grid_col, grid_row) for each arrow
    PAD_BUTTONS = [
        # P1: bits 0-4
        (0, "UL", 0, 0), (1, "UR", 2, 0),
        (2, "CTR", 1, 1),
        (3, "DL", 0, 2), (4, "DR", 2, 2),
        # P2: bits 5-9
        (5, "UL", 0, 0), (6, "UR", 2, 0),
        (7, "CTR", 1, 1),
        (8, "DL", 0, 2), (9, "DR", 2, 2),
    ]
    CABINET_BUTTONS = [
        (10, "TEST"),
        (11, "SERVICE"),
    ]

    COLOR_ACTIVE = QColor(220, 30, 30)
    COLOR_INACTIVE = QColor(50, 50, 50)
    COLOR_BORDER = QColor(100, 100, 100)
    COLOR_TEXT_ACTIVE = QColor(255, 255, 255)
    COLOR_TEXT_INACTIVE = QColor(140, 140, 140)
    COLOR_BG = QColor(30, 30, 30)
    COLOR_LABEL = QColor(200, 200, 200)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIU IO Bridge - Diagnostics")
        self.setFixedSize(520, 320)
        self._state = 0

    def on_state_updated(self, state):
        """Slot - called by BridgeWorker when a button changes."""
        self._state = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), self.COLOR_BG)

        btn_w, btn_h = 60, 60
        pad_spacing = 10
        pad_w = 3 * btn_w + 2 * pad_spacing
        pad_h = 3 * btn_h + 2 * pad_spacing

        p1_x, p1_y = 30, 50
        p2_x, p2_y = 280, 50

        # Player labels
        label_font = QFont("sans-serif", 12, QFont.Weight.Bold)
        p.setFont(label_font)
        p.setPen(self.COLOR_LABEL)
        p.drawText(p1_x, 35, pad_w, 20, Qt.AlignmentFlag.AlignCenter, "Player 1")
        p.drawText(p2_x, 35, pad_w, 20, Qt.AlignmentFlag.AlignCenter, "Player 2")

        btn_font = QFont("sans-serif", 10, QFont.Weight.Bold)
        p.setFont(btn_font)

        # P1 arrows (bits 0-4)
        for bit, label, gx, gy in self.PAD_BUTTONS[:5]:
            x = p1_x + gx * (btn_w + pad_spacing)
            y = p1_y + gy * (btn_h + pad_spacing)
            active = bool(self._state & (1 << bit))
            self._draw_button(p, x, y, btn_w, btn_h, label, active)

        # P2 arrows (bits 5-9)
        for bit, label, gx, gy in self.PAD_BUTTONS[5:]:
            x = p2_x + gx * (btn_w + pad_spacing)
            y = p2_y + gy * (btn_h + pad_spacing)
            active = bool(self._state & (1 << bit))
            self._draw_button(p, x, y, btn_w, btn_h, label, active)

        # Cabinet buttons
        cab_y = p1_y + pad_h + 20
        cab_w = 90
        for i, (bit, label) in enumerate(self.CABINET_BUTTONS):
            x = 30 + i * (cab_w + 20)
            active = bool(self._state & (1 << bit))
            self._draw_button(p, x, cab_y, cab_w, 40, label, active)

        p.end()

    def _draw_button(self, p, x, y, w, h, label, active):
        color = self.COLOR_ACTIVE if active else self.COLOR_INACTIVE
        text_color = self.COLOR_TEXT_ACTIVE if active else self.COLOR_TEXT_INACTIVE
        p.setPen(QPen(self.COLOR_BORDER, 1))
        p.setBrush(QBrush(color))
        p.drawRoundedRect(x, y, w, h, 6, 6)
        p.setPen(text_color)
        p.drawText(x, y, w, h, Qt.AlignmentFlag.AlignCenter, label)
