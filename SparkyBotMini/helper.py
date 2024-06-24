from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QSlider
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QRadialGradient
from PyQt5.QtCore import Qt, QPoint, QRectF, QSize, pyqtSignal
import sys
import math
from styles import stylesheet  # Assuming stylesheet is imported correctly


class SpeedGauge(QWidget):
    base_speed_changed = pyqtSignal(int)  # Signal for base speed changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)
        self.value = -67
        self.min_value = 0
        self.max_value = 100
        self.base_speed = 0

        self.base_speed_label = QLabel(self)
        self.base_speed_label.setAlignment(Qt.AlignCenter)
        self.base_speed_label.setGeometry(120, 430, 250, 50)
        self.base_speed_label.setStyleSheet("QLabel { font-size: 40px; color: black; }")

    def set_value(self, value):
        # Check if the value is outside the range [-66, -33]
        if value < -66 or value >= -33:
            self.value = value
        self.update()  

        
    def calculate_gradient(self, value):
        # For fixed colors, simply return the corresponding color based on value range
        if value <= 50:
            return QColor(0, 255, 0)  # Green
        elif value <= 75:
            return QColor(255, 255, 0)  # Yellow
        else:
            return QColor(255, 0, 0)  # Red

    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        radius = side / 2.0
        center = QPoint(int(self.width() / 2), int(self.height() / 2))
        
        # Define the angle range for the gradient (in degrees)
        start_angle = -45  # Starting angle (top of the circle)
        span_angle = 270   # Span angle (180 degrees for half-circle)
        
        # Draw outer background circle with gradient
        outer_gradient = QConicalGradient(center, -45)
        outer_gradient.setColorAt(0, QColor(255, 0, 0))    # Red
        outer_gradient.setColorAt(0.5, QColor(255, 255, 0))  # Yellow
        outer_gradient.setColorAt(1, QColor(0, 255, 0))    # Green
        outer_gradient_radius = radius
        
        painter.setBrush(outer_gradient)
        painter.setPen(Qt.NoPen)
        #painter.drawEllipse(center, outer_gradient_radius, outer_gradient_radius)
        painter.drawPie(center.x() - int(radius), center.y() - int(radius), int(radius) * 2, int(radius) * 2, start_angle * 16, span_angle * 16)

        # Draw inner background circle with radial gradient
        inner_radius = radius * 0.98  # Adjust the inner radius as needed
        inner_gradient = QRadialGradient(center, inner_radius)
        inner_gradient.setColorAt(0.85, QColor(255, 255, 255))  # White at the center
        inner_gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Fully transparent at the edge

        painter.setBrush(inner_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, inner_radius, inner_radius)

        # Draw scale
        scale_pen = QPen(Qt.gray)
        scale_pen.setWidthF(0.02 * radius)
        painter.setPen(scale_pen)
        scale_length = 0.15 * radius
        minor_tick_length = 0.05 * radius

        scale_step = (self.max_value - self.min_value) / 10.0
        for i in range(11):
            value = int(self.min_value + i * scale_step)
            angle = -135 + i * 27

            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.drawLine(0, -int(radius), 0, -int(radius - scale_length))
            painter.restore()

            if 0 < i < 11:
                for j in range(1, 5):
                    minor_angle = angle - j * 27 / 4
                    painter.save()
                    painter.translate(center)
                    painter.rotate(minor_angle)
                    painter.drawLine(0, -int(radius), 0, -int(radius - minor_tick_length))
                    painter.restore()

            painter.save()
            painter.translate(center)
            painter.rotate(angle)

            text_position = QPoint(0, -int(radius - scale_length * 1.7))
            painter.translate(text_position)
            painter.rotate(-angle)

            font = QFont('Arial', int(0.1 * radius), QFont.Bold)
            painter.setFont(font)

            text_rect = QRectF(-20, -10, 50, 30)
            painter.drawText(text_rect, Qt.AlignCenter, str(value))
            painter.restore()

        # Draw needle
        painter.setBrush(Qt.black)  # Set brush color to black
        painter.drawEllipse(center.x() - int(0.1 * radius), center.y() - int(0.1 * radius), int(0.2 * radius), int(0.2 * radius))
        painter.setPen(Qt.NoPen)  # No pen for drawing outlines
        
        needle_pen = QPen(Qt.black)
        needle_pen.setWidthF(0.05 * radius)
        painter.setPen(needle_pen)

        normalized_angle = -135 + ((self.value - self.min_value) / (self.max_value - self.min_value)) * 270.0
        needle_angle = -int(normalized_angle)

        # Calculate base speed based on needle angle
        if 313 <= needle_angle < 360:
            self.base_speed = int((needle_angle - 313) * 10 / 27)
        elif 0 <= needle_angle <= 224:
            self.base_speed = int(needle_angle * 10 / 27 + 17.2)

        self.base_speed_label.setText(f"Speed: {self.base_speed} %")
        self.base_speed_changed.emit(self.base_speed)

        painter.save()
        painter.translate(center)
        painter.rotate(needle_angle - 90)
        painter.drawLine(0, 0, 0, -int(radius - scale_length * 1.5))
        painter.restore()
        
        painter.end()
        
    def sizeHint(self):
        return QSize(200, 200)

    def mousePressEvent(self, event):
        center = QPoint(int(self.width() / 2), int(self.height() / 2))
        click_pos = event.pos() - center

        angle = math.atan2(click_pos.y(), click_pos.x()) * (180 / math.pi)
        angle = -angle

        if angle < -180:
            angle += 360
        elif angle > 180:
            angle -= 360

        range_angle = 270
        range_value = self.max_value - self.min_value
        value = int(((angle - 45) / range_angle) * range_value + self.min_value)
        self.set_value(value)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(stylesheet)  # Assuming `stylesheet` is imported correctly
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('SparkyBot Mini GUI')
        self.setFixedSize(1024, 600)

        layout = QHBoxLayout(self)
        self.speed_gauge = SpeedGauge()
        layout.addWidget(self.speed_gauge)
        layout.addSpacing(100)

        controls_layout = QVBoxLayout()

        slider_group_layout = QHBoxLayout()

        self.mode_label = QLabel("Manual Mode")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("QLabel { font-size: 40px; font-weight: bold; color: #fff; } ")
        self.mode_label.setFixedWidth(320)
        slider_group_layout.addWidget(self.mode_label)

        self.mode_slider = QSlider(Qt.Horizontal)
        self.mode_slider.setMinimum(0)
        self.mode_slider.setMaximum(1)
        self.mode_slider.setValue(0)
        self.mode_slider.setTickInterval(1)
        self.mode_slider.setTickPosition(QSlider.TicksBelow)
        self.mode_slider.sliderMoved.connect(self.on_mode_slider_moved)
        self.mode_slider.setFixedWidth(100)
        slider_group_layout.addWidget(self.mode_slider)

        controls_layout.addLayout(slider_group_layout)

        self.on_off_button = QCheckBox("Power Off")
        self.on_off_button.setChecked(False)
        self.on_off_button.stateChanged.connect(self.on_on_off_button_state_changed)
        self.on_off_button.setStyleSheet("""
            QCheckBox {
                font-size: 40px;
            }
            QCheckBox::indicator {
                width: 50px;
                height: 50px;
            }
        """)
        self.on_off_button.setMinimumHeight(100)
        self.on_off_button.setFixedWidth(320)
        controls_layout.addWidget(self.on_off_button)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

        self.speed_gauge.base_speed_changed.connect(self.on_base_speed_changed)

    def on_base_speed_changed(self, base_speed):
        print(f"Speed: {base_speed} %")

    def on_mode_slider_moved(self, position):
        if position == 1:
            self.mode_label.setText("Auto Mode")
            print("Auto Control Mode")
        else:
            self.mode_label.setText("Manual Mode")
            print("Manual Control Mode")

    def on_on_off_button_state_changed(self, state):
        if state == Qt.Checked:
            self.on_off_button.setText("Power On")
            print("Switched On")
        else:
            self.on_off_button.setText("Power Off")
            print("Switched Off")

