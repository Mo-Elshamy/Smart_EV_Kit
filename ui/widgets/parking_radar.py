from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygon, QLinearGradient
from config import DIST_CRITICAL_CM, DIST_WARNING_CM, DIST_SAFE_CM


class ParkingVisualizer(QWidget):
    """Dynamic vector-rendered Off-Road EV Buggy with 8-zone ultrasonic radar arcs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.distances = [0.0] * 8
        self.setMinimumSize(300, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_sensor_data(self, distances):
        self.distances = list(distances)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Background Radar Grid
        self.draw_grid(painter, w, h)

        # 2. Aspect Ratio & Scaling (Optimized for 7-inch displays)
        scene_w = 320
        scene_h = 520
        scale = min(w / scene_w, h / scene_h) * 0.95

        painter.translate(w / 2, h / 2)
        painter.scale(scale, scale)

        cx = 0
        cy = 0

        # 3. Buggy Geometry
        body_w = 120
        body_h = 250

        # Suspension Links
        painter.setPen(QPen(QColor(160, 160, 160), 10))
        painter.drawLine(cx - 25, cy - 70, cx - 100, cy - 95)
        painter.drawLine(cx + 25, cy - 70, cx + 100, cy - 95)
        painter.drawLine(cx - 25, cy + 70, cx - 100, cy + 90)
        painter.drawLine(cx + 25, cy + 70, cx + 100, cy + 90)

        # Tires (Detailed Tread)
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(5, 5, 5), 2))
        wheel_w = 48
        wheel_h = 85

        self.draw_tire(painter, cx - 100, cy - 95, -8, wheel_w, wheel_h)  # Front Left
        self.draw_tire(painter, cx + 100, cy - 95, 8, wheel_w, wheel_h)   # Front Right
        self.draw_tire(painter, cx - 100, cy + 80, 0, wheel_w, wheel_h)   # Rear Left
        self.draw_tire(painter, cx + 100, cy + 80, 0, wheel_w, wheel_h)   # Rear Right

        # Body Gradient
        grad = QLinearGradient(0, -body_h // 2, 0, body_h // 2)
        grad.setColorAt(0, QColor(60, 60, 60))
        grad.setColorAt(1, QColor(10, 10, 10))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(0, 0, 0), 4))

        # Tub Shape Polygon
        poly = QPolygon()
        poly.append(QPoint(cx - 40, cy - body_h // 2))
        poly.append(QPoint(cx + 40, cy - body_h // 2))
        poly.append(QPoint(cx + body_w // 2, cy - 45))
        poly.append(QPoint(cx + body_w // 2, cy + 70))
        poly.append(QPoint(cx + 40, cy + body_h // 2))
        poly.append(QPoint(cx - 40, cy + body_h // 2))
        poly.append(QPoint(cx - body_w // 2, cy + 70))
        poly.append(QPoint(cx - body_w // 2, cy - 45))
        painter.drawPolygon(poly)

        # Chrome Roll Cage
        painter.setPen(QPen(QColor(200, 200, 200), 6))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(cx - 45, cy - 55, 90, 125)
        painter.drawLine(cx - 45, cy - 55, cx + 45, cy + 70)
        painter.drawLine(cx + 45, cy - 55, cx - 45, cy + 70)

        # Spare Tire
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawEllipse(cx - 35, cy + body_h // 2 - 50, 70, 70)
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        painter.drawEllipse(cx - 12, cy + body_h // 2 - 27, 24, 24)

        # Headlights
        painter.setBrush(QBrush(QColor(240, 240, 255)))
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawEllipse(cx - 50, cy - body_h // 2 + 12, 22, 22)
        painter.drawEllipse(cx + 28, cy - body_h // 2 + 12, 22, 22)

        # 4. 8-Zone Ultrasonic Radar Arcs
        # Front Sensors (0..3)
        self.draw_radar_arc(painter, cx, cy - body_h // 2, -55, self.distances[0])
        self.draw_radar_arc(painter, cx, cy - body_h // 2, -20, self.distances[1])
        self.draw_radar_arc(painter, cx, cy - body_h // 2,  20, self.distances[2])
        self.draw_radar_arc(painter, cx, cy - body_h // 2,  55, self.distances[3])

        # Rear Sensors (4..7)
        self.draw_radar_arc(painter, cx, cy + body_h // 2, 235, self.distances[4])
        self.draw_radar_arc(painter, cx, cy + body_h // 2, 200, self.distances[5])
        self.draw_radar_arc(painter, cx, cy + body_h // 2, 160, self.distances[6])
        self.draw_radar_arc(painter, cx, cy + body_h // 2, 125, self.distances[7])

    def draw_grid(self, painter, w, h):
        pen = QPen(QColor(0, 0, 0, 25))
        pen.setWidth(1)
        painter.setPen(pen)
        step = 50
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

        painter.setPen(QPen(QColor(0, 0, 0, 18), 2))
        center = QPoint(w // 2, h // 2)
        painter.drawEllipse(center, 100, 100)
        painter.drawEllipse(center, 200, 200)
        painter.drawEllipse(center, 300, 300)

    def draw_tire(self, painter, x, y, angle, w, h):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        painter.drawRoundedRect(-w // 2, -h // 2, w, h, 8, 8)
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawLine(-w // 2 + 5, -h // 4, w // 2 - 5, -h // 4)
        painter.drawLine(-w // 2 + 5, 0, w // 2 - 5, 0)
        painter.drawLine(-w // 2 + 5, h // 4, w // 2 - 5, h // 4)
        painter.restore()

    def draw_radar_arc(self, painter, x, y, angle_deg, distance):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle_deg - 90)

        bars = 0
        color = QColor(100, 100, 100, 50)

        if distance > 0:
            if distance < DIST_CRITICAL_CM:
                bars = 3
                color = QColor(255, 50, 50)
            elif distance < DIST_WARNING_CM:
                bars = 2
                color = QColor(255, 180, 0)
            elif distance < DIST_SAFE_CM:
                bars = 1
                color = QColor(0, 200, 100)

        span = int(35 * 16)
        start = int(-17.5 * 16)

        pen = QPen(color, 6, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        d1, d2, d3 = 90, 170, 250

        # Bar 1 (outer)
        if bars >= 1:
            painter.drawArc(-d1 // 2, -d1 // 2, d1, d1, start, span)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 25), 2))
            painter.drawArc(-d1 // 2, -d1 // 2, d1, d1, start, span)

        # Bar 2 (middle)
        if bars >= 2:
            painter.setPen(pen)
            painter.drawArc(-d2 // 2, -d2 // 2, d2, d2, start, span)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 25), 2))
            painter.drawArc(-d2 // 2, -d2 // 2, d2, d2, start, span)

        # Bar 3 (closest / critical)
        if bars >= 3:
            painter.setPen(pen)
            painter.drawArc(-d3 // 2, -d3 // 2, d3, d3, start, span)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 25), 2))
            painter.drawArc(-d3 // 2, -d3 // 2, d3, d3, start, span)

        painter.restore()

