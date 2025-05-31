import sys
import math
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QGridLayout, QHBoxLayout, QComboBox, QMessageBox
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Hardware imports
try:
    import qwiic_otos
    import sparkybotio as sb
except ImportError:
    qwiic_otos = None

# Global state
x, y, heading = 0.0, 0.0, math.radians(90.0)
tracking_enabled = False
waypoints = []
current_wp_index = 0
trajectory = []
sensor = None

class PoseToPoseGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.simulation = True
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.controlLoop)
        self.timer.start(100)
        self.prev_error = 0
        self.integral = 0

    def initUI(self):
        self.setWindowTitle("Autopilot Demo")

        grid = QGridLayout()

        self.entry_x = QLineEdit()
        self.entry_y = QLineEdit()
        grid.addWidget(QLabel("Way Point X (mm):"), 0, 0)
        grid.addWidget(self.entry_x, 0, 1)
        grid.addWidget(QLabel("Way Point Y (mm):"), 1, 0)
        grid.addWidget(self.entry_y, 1, 1)

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Simulation", "Hardware"])
        self.mode_selector.currentIndexChanged.connect(self.modeChanged)
        grid.addWidget(QLabel("Mode:"), 2, 0)
        grid.addWidget(self.mode_selector, 2, 1)

        self.set_goal_btn = QPushButton("Add Way Point")
        self.set_goal_btn.clicked.connect(self.addWayPoint)
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.startTracking)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stopTracking)

        grid.addWidget(self.set_goal_btn, 3, 0, 1, 2)
        grid.addWidget(self.start_btn, 4, 0)
        grid.addWidget(self.stop_btn, 4, 1)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.trajectory_line, = self.ax.plot([], [], 'b-', label="Path")
        self.waypoints_scatter = self.ax.plot([], [], linestyle='', marker='o', color='r', label="Way Points")[0]
        self.start_point, = self.ax.plot([], [], linestyle='', marker='o', color='g', label="Start")

        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.axis("equal")
        self.ax.grid(True)
        self.ax.legend()

        # Set initial axis limits to 500x500 centered at (0,0)
        self.ax.set_xlim(-250, 250)
        self.ax.set_ylim(-250, 250)

        main_layout = QHBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addWidget(self.canvas)
        self.setLayout(main_layout)

    def modeChanged(self, index):
        global sensor
        self.simulation = (index == 0)

        if not self.simulation:
            if qwiic_otos is None:
                QMessageBox.critical(self, "Error", "Hardware libraries not available.")
                self.mode_selector.setCurrentIndex(0)
                return

            sensor = qwiic_otos.QwiicOTOS()
            if not sensor.is_connected():
                QMessageBox.critical(self, "Error", "OTOS sensor not connected.")
                self.mode_selector.setCurrentIndex(0)
                return

            sensor.begin()
            sensor.resetTracking()
            sensor.calibrateImu()
        else:
            self.stop_motors()
            sensor = None

    def addWayPoint(self):
        try:
            wx = float(self.entry_x.text())
            wy = float(self.entry_y.text())
            waypoints.append({"x": wx, "y": wy})
            self.entry_x.clear()
            self.entry_y.clear()
            self.updatePlot()
            print(f"Added waypoint: ({wx}, {wy})")  # Debug output
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numbers.")

    def startTracking(self):
        global tracking_enabled, x, y, heading, trajectory, current_wp_index

        if not waypoints:
            QMessageBox.warning(self, "No Waypoints", "Add at least one waypoint before starting.")
            return

        x, y, heading = 0.0, 0.0, math.radians(90.0)
        trajectory.clear()
        current_wp_index = 0
        tracking_enabled = True

        self.start_point.set_data([0], [0])
        self.updatePlot()

    def stopTracking(self):
        global tracking_enabled, trajectory, waypoints, current_wp_index
        tracking_enabled = False
        trajectory.clear()
        waypoints.clear()
        current_wp_index = 0

        self.trajectory_line.set_data([], [])
        self.waypoints_scatter.set_data([], [])
        self.start_point.set_data([], [])
        self.ax.set_title("")
        # Reset view to initial 500x500 window centered at 0,0 on stop
        self.ax.set_xlim(-250, 250)
        self.ax.set_ylim(-250, 250)
        self.canvas.draw()

        if not self.simulation:
            self.stop_motors()

    def motor_left(self, speed):
        sb.setMotor(2, -speed)
        sb.setMotor(4, -speed)

    def motor_right(self, speed):
        sb.setMotor(1, -speed)
        sb.setMotor(3, -speed)

    def stop_motors(self):
        for m in [1, 2, 3, 4]:
            sb.setMotor(m, 0)

    def controlLoop(self):
        global x, y, heading, tracking_enabled, current_wp_index

        if not tracking_enabled:
            return

        if current_wp_index >= len(waypoints):
            tracking_enabled = False
            if not self.simulation:
                self.stop_motors()
            print("All waypoints reached!")
            return

        dt = 0.1
        target = waypoints[current_wp_index]
        dx, dy = target["x"] - x, target["y"] - y
        distance = math.hypот(dx, dy)
        angle_to_goal = math.atan2(dy, dx)
        error = math.atan2(math.sin(angle_to_goal - heading), math.cos(angle_to_goal - heading))

        threshold = 50 if not self.simulation else 5
        if distance < threshold:
            current_wp_index += 1
            self.prev_error = 0
            self.integral = 0
            if current_wp_index >= len(waypoints):
                tracking_enabled = False
                if not self.simulation:
                    self.stop_motors()
                print("All waypoints reached!")
            return

        if self.simulation:
            Kp, Ki, Kd = 2.0, 0.0, 0.0
            self.integral += error * dt
            derivative = (error - self.prev_error) / dt
            w = Kp * error + Ki * self.integral + Kd * derivative
            self.prev_error = error

            w = max(-10.0, min(10.0, w))
            v = 80 * math.exp(-20 * error ** 2)

            heading += w * dt
            x += v * math.cos(heading) * dt
            y += v * math.sin(heading) * dt

        else:
            pos = sensor.getPosition()
            x, y = pos.x * 25.4, pos.y * 25.4
            heading = math.radians(pos.h + 90.0)

            Kp, Ki, Kd = 1.0, 0.0, 0.01
            self.integral += error * dt
            derivative = (error - self.prev_error) / dt
            w = Kp * error + Ki * self.integral + Kd * derivative
            self.prev_error = error

            base_speed = 50
            diff = w * 60
            left_speed = max(-100, min(100, base_speed - diff))
            right_speed = max(-100, min(100, base_speed + diff))

            self.motor_left(int(left_speed))
            self.motor_right(int(right_speed))

        trajectory.append((x, y))
        self.updatePlot()

    def updatePlot(self):
        # Always update waypoints display
        if waypoints:
            wxs = [wp["x"] for wp in waypoints]
            wys = [wp["y"] for wp in waypoints]
            self.waypoints_scatter.set_data(wxs, wys)
        else:
            self.waypoints_scatter.set_data([], [])

        # Update trajectory
        if trajectory:
            xs, ys = zip(*trajectory)
            self.trajectory_line.set_data(xs, ys)
        else:
            self.trajectory_line.set_data([], [])

        # Show start point if tracking has started
        if tracking_enabled or trajectory:
            self.start_point.set_data([0], [0])
        else:
            self.start_point.set_data([], [])

        # Calculate bounds for axis scaling
        all_points = []
        
        # Add origin point
        all_points.extend([(0, 0)])
        
        # Add waypoints
        if waypoints:
            all_points.extend([(wp["x"], wp["y"]) for wp in waypoints])
        
        # Add trajectory points
        if trajectory:
            all_points.extend(trajectory)

        if len(all_points) > 1:  # More than just origin
            all_x = [p[0] for p in all_points]
            all_y = [p[1] for p in all_points]

            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

            # Calculate padding (10% of range + 20 mm buffer)
            range_x = max_x - min_x
            range_y = max_y - min_y
            pad_x = max(range_x * 0.1, 20)  # At least 20mm padding
            pad_y = max(range_y * 0.1, 20)

            min_x -= pad_x
            max_x += pad_x
            min_y -= pad_y
            max_y += pad_y

            # Enforce minimum axis range of 500 x 500
            if (max_x - min_x) < 500:
                mid_x = (max_x + min_x) / 2
                min_x = mid_x - 250
                max_x = mid_x + 250

            if (max_y - min_y) < 500:
                mid_y = (max_y + min_y) / 2
                min_y = mid_y - 250
                max_y = mid_y + 250

            self.ax.set_xlim(min_x, max_x)
            self.ax.set_ylim(min_y, max_y)
        else:
            # Reset to initial 500x500 window centered at 0,0 if no waypoints
            self.ax.set_xlim(-250, 250)
            self.ax.set_ylim(-250, 250)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PoseToPoseGUI()
    gui.show()
    sys.exit(app.exec_())
