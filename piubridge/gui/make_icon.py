#!/usr/bin/env python3
"""
Generate icon.png - a vector-rendered tray icon for the PIU bridge.

Styled after the PIU arcade pad artwork:
 - 4 corner panels (UL/UR/DL/DR) with stacked-chevron arrows (PIU style)
 - center panel (octagonal) with footprints on a yellow glow
 - dark navy outer circle with a yellow rim

Run to regenerate icon.png:
    python3 piubridge/gui/make_icon.py
"""

import math
import os
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap,
                         QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import QApplication


def _draw_stacked_chevron(p, color, outline=QColor(240, 240, 240),
                          tip_max=42, stroke_width=9, count=3, spacing=14):
    """Draw a stack of `count` chevrons pointing in the +x direction.

    Each successive chevron is shifted back toward the origin, creating
    the layered look of the PIU pad arrow art.
    """
    for i in range(count):
        tip_x = tip_max - i * spacing
        wing = tip_x - 4        # 45-degree diagonal = wing_y matches the run
        if wing < 6:
            break
        pts = QPolygonF([
            QPointF(tip_x - wing, -wing),
            QPointF(tip_x, 0),
            QPointF(tip_x - wing, wing),
        ])

        # White outline underneath
        pen = QPen(outline, stroke_width + 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPolyline(pts)

        # Colored stroke on top
        pen2 = QPen(color, stroke_width)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen2.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen2)
        p.drawPolyline(pts)


def _draw_panel(p, cx, cy, panel_size, arrow_color, arrow_angle_deg,
                draw_arrow=True):
    """Draw one pad panel (rounded dark square with optional stacked arrow)."""
    half = panel_size / 2
    rect = QRectF(cx - half, cy - half, panel_size, panel_size)

    # Panel background: near-black with subtle gradient
    grad = QRadialGradient(cx, cy, panel_size * 0.7)
    grad.setColorAt(0.0, QColor(35, 40, 52))
    grad.setColorAt(1.0, QColor(10, 12, 20))
    p.setBrush(QBrush(grad))
    p.setPen(QPen(QColor(5, 5, 10), 2))
    p.drawRoundedRect(rect, panel_size * 0.12, panel_size * 0.12)

    if draw_arrow:
        # Scale chevron to the panel
        scale = panel_size / 140.0
        p.save()
        p.translate(cx, cy)
        p.rotate(arrow_angle_deg)
        p.scale(scale, scale)
        _draw_stacked_chevron(p, arrow_color)
        p.restore()


def _draw_center_panel(p, cx, cy, size):
    """Draw the octagonal center panel with yellow glow + footprints."""
    half = size / 2

    # Octagon points (regular 8-sided, pointy-top at 22.5° offset)
    octagon = QPolygonF()
    for i in range(8):
        angle = math.radians(22.5 + i * 45)
        x = cx + half * math.cos(angle)
        y = cy + half * math.sin(angle)
        octagon.append(QPointF(x, y))

    # Dark octagon frame
    p.setBrush(QBrush(QColor(15, 18, 25)))
    p.setPen(QPen(QColor(5, 5, 10), 2))
    p.drawPolygon(octagon)

    # Yellow glowing core inside (smaller octagon)
    core_poly = QPolygonF()
    core_half = half * 0.78
    for i in range(8):
        angle = math.radians(22.5 + i * 45)
        x = cx + core_half * math.cos(angle)
        y = cy + core_half * math.sin(angle)
        core_poly.append(QPointF(x, y))

    core_grad = QRadialGradient(cx, cy, core_half)
    core_grad.setColorAt(0.0, QColor(255, 250, 180))
    core_grad.setColorAt(0.7, QColor(250, 200, 40))
    core_grad.setColorAt(1.0, QColor(200, 130, 20))
    p.setBrush(QBrush(core_grad))
    p.setPen(QPen(QColor(140, 90, 10), 1.5))
    p.drawPolygon(core_poly)

    # Two footprints (simple toe-less ovals) in a darker amber
    foot_color = QColor(180, 110, 20)
    foot_w = size * 0.12
    foot_h = size * 0.30
    dx = size * 0.13
    dy = size * 0.05
    p.setBrush(QBrush(foot_color))
    p.setPen(QPen(QColor(110, 70, 10), 1.2))
    p.drawEllipse(QPointF(cx - dx, cy - dy), foot_w, foot_h)
    p.drawEllipse(QPointF(cx + dx, cy + dy), foot_w, foot_h)


def render_icon(output_path, size=256):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = size / 2, size / 2

    # Outer circle: dark navy with yellow rim
    bg = QRadialGradient(cx, cy, size / 2)
    bg.setColorAt(0.0, QColor(35, 45, 75))
    bg.setColorAt(1.0, QColor(8, 10, 18))
    p.setBrush(QBrush(bg))
    p.setPen(QPen(QColor(255, 200, 0), 5))
    p.drawEllipse(5, 5, size - 10, size - 10)

    # Pad layout: 4 corner panels + center
    panel_size = size * 0.27
    offset = size * 0.22

    # UL, UR, DL, DR panels - arrows point outward toward each corner
    panels = [
        (-1, -1, QColor(220, 45, 50),   225),  # UL = red (fire)
        ( 1, -1, QColor(235, 60, 60),   315),  # UR = red (fire) - PIU uses same red
        (-1,  1, QColor(55,  140, 215), 135),  # DL = blue (ice)
        ( 1,  1, QColor(55,  140, 215),  45),  # DR = blue (ice) - PIU uses same blue
    ]
    for dx, dy, color, angle in panels:
        px = cx + dx * offset
        py = cy + dy * offset
        _draw_panel(p, px, py, panel_size, color, angle)

    _draw_center_panel(p, cx, cy, panel_size * 0.95)

    p.end()
    pm.save(output_path, "PNG")
    print(f"Wrote {output_path} ({size}x{size})")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    render_icon(out)
