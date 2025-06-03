import sys
import os
import math
import importlib
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QVBoxLayout, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Directory where the control method .py files are stored
CONTROL_METHODS_PATH = "./mobile robot control methods"
if CONTROL_METHODS_PATH not in sys.path:
    sys.path.append(CONTROL_METHODS_PATH)

try:
    import qwiic_otos
    import sparkybotio as sb
except ImportError:
    qwiic_otos = None
    sb = None

def angle_wrap(a):
    return math.atan2(math.sin(a), math.cos(a))

class RobotControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.simulation = True
        self.heading_arrow_artist = None

        # Discover all available control methods dynamically
        self.control_methods = {}
        for filename in os.listdir(CONTROL_METHODS_PATH):
            if filename.endswith(".py") and filename != "__init__.py":
                display_name = filename.replace("_", " ").replace(".py", "").title()
                module_name = filename[:-3]
                self.control_methods[display_name] = module_name

        self.current_controller = None
        self.waypoints = []
        self.current_wp_index = 0
        self.trajectory = []
        self.x = 0.0
        self.y = 0.0
        self.heading = math.radians(90.0)
        self.tracking_enabled = False

        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.controlLoop)
        self.timer.start(100)
        self.resize(1300, 800)
        self.updateController()  # Import initial controller

    def initUI(self):
        self.setWindowTitle("Differential-Drive Robot Control")
        control_layout = QVBoxLayout()

        # Mode selector
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Simulation", "Hardware"])
        self.mode_selector.currentIndexChanged.connect(self.changeMode)
        control_layout.addWidget(QLabel("Mode:"))
        control_layout.addWidget(self.mode_selector)

        # --- Control Method Dropdown ---
        self.control_selector = QComboBox()
        self.control_selector.addItems(list(self.control_methods.keys()))
        self.control_selector.currentIndexChanged.connect(self.updateController)
        control_layout.addWidget(QLabel("Control Method:"))
        control_layout.addWidget(self.control_selector)

        # --- Waypoint Entry Fields ---
        entry_row = QHBoxLayout()
        self.entry_x = QLineEdit()
        self.entry_y = QLineEdit()
        self.entry_theta = QLineEdit("90.0")
        entry_row.addWidget(QLabel("X (mm):"))
        entry_row.addWidget(self.entry_x)
        entry_row.addWidget(QLabel("Y (mm):"))
        entry_row.addWidget(self.entry_y)
        entry_row.addWidget(QLabel("θ (deg):"))
        entry_row.addWidget(self.entry_theta)
        control_layout.addLayout(entry_row)

        self.btn_add_wp = QPushButton("Add Waypoint")
        self.btn_add_wp.clicked.connect(self.addWaypoint)
        control_layout.addWidget(self.btn_add_wp)
        self.entry_x.returnPressed.connect(self.addWaypoint)
        self.entry_y.returnPressed.connect(self.addWaypoint)
        self.entry_theta.returnPressed.connect(self.addWaypoint)

        # --- Waypoint Table ---
        self.waypoint_table = QTableWidget()
        self.waypoint_table.setColumnCount(3)
        self.waypoint_table.setHorizontalHeaderLabels(["X (mm)", "Y (mm)", "Heading (deg)"])
        self.waypoint_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        control_layout.addWidget(QLabel("Waypoints:"))
        control_layout.addWidget(self.waypoint_table)

        btn_wp_layout = QHBoxLayout()
        self.btn_delete_wp = QPushButton("Delete Waypoint")
        self.btn_delete_wp.clicked.connect(self.deleteWaypoint)
        btn_wp_layout.addWidget(self.btn_delete_wp)
        self.btn_clear_wp = QPushButton("Clear Waypoints")
        self.btn_clear_wp.clicked.connect(self.clearWaypoints)
        btn_wp_layout.addWidget(self.btn_clear_wp)
        control_layout.addLayout(btn_wp_layout)

        # --- Start/Stop/Verbose ---
        btn_start_stop_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.startTracking)
        btn_start_stop_layout.addWidget(self.btn_start)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stopTracking)
        btn_start_stop_layout.addWidget(self.btn_stop)
        control_layout.addLayout(btn_start_stop_layout)

        self.verbose_checkbox = QCheckBox("Verbose")
        self.verbose_checkbox.setChecked(False)
        control_layout.addStretch()
        control_layout.addWidget(self.verbose_checkbox)

        # Plot Area
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.trajectory_line, = self.ax.plot([], [], 'b-', label="Path")
        self.waypoints_scatter, = self.ax.plot([], [], 'ro', label="Waypoints")
        self.start_point, = self.ax.plot([0], [0], 'go', label="Start")
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.axis("equal")
        self.ax.grid(True)
        self.ax.legend()

        main_layout = QHBoxLayout()
        main_layout.addLayout(control_layout, 1)
        main_layout.addWidget(self.canvas, 2)
        self.setLayout(main_layout)

    def updateController(self):
        ctrl_name = self.control_selector.currentText()
        module_name = self.control_methods[ctrl_name]
        try:
            self.current_controller = importlib.import_module(module_name)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import {module_name}: {e}")
            self.current_controller = None

    def log(self, msg):
        print(msg)

    def changeMode(self, index):
        global sensor
        self.simulation = (index == 0)
        if not self.simulation:
            if qwiic_otos is None:
                QMessageBox.critical(self, "Error", "Hardware libraries not available.")
                self.mode_selector.setCurrentIndex(0)
                self.simulation = True
                return
            sensor = qwiic_otos.QwiicOTOS()
            if not sensor.is_connected():
                QMessageBox.critical(self, "Error", "OTOS sensor not connected.")
                self.mode_selector.setCurrentIndex(0)
                self.simulation = True
                return
            sensor.begin()
            sensor.resetTracking()
            sensor.calibrateImu()
            self.log("Hardware mode initialized")
        else:
            sensor = None
            self.log("Switched to simulation mode")

    def addWaypoint(self):
        try:
            wx = float(self.entry_x.text())
            wy = float(self.entry_y.text())
            theta_text = self.entry_theta.text().strip()
            theta_deg = float(theta_text) if theta_text else 90.0
            theta_rad = math.radians(theta_deg)
            self.waypoints.append({"x": wx, "y": wy, "theta": theta_rad})
            self.updateWaypointTable()
            self.entry_x.clear()
            self.entry_y.clear()
            self.entry_theta.clear()
            self.log(f"Added waypoint: ({wx}, {wy}, {theta_deg}°)")
            self.updatePlot()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric X, Y, and θ.")

    def updateWaypointTable(self):
        self.waypoint_table.setRowCount(len(self.waypoints))
        for i, wp in enumerate(self.waypoints):
            self.waypoint_table.setItem(i, 0, QTableWidgetItem(f"{wp['x']:.2f}"))
            self.waypoint_table.setItem(i, 1, QTableWidgetItem(f"{wp['y']:.2f}"))
            theta_deg = math.degrees(wp['theta']) if wp['theta'] is not None else 90.0
            self.waypoint_table.setItem(i, 2, QTableWidgetItem(f"{theta_deg:.1f}"))

    def clearWaypoints(self):
        self.waypoints.clear()
        self.current_wp_index = 0
        self.updatePlot()
        self.updateWaypointTable()
        self.log("Cleared all waypoints.")

    def deleteWaypoint(self):
        selected_rows = self.waypoint_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Delete Waypoint", "Please select at least one waypoint row to delete.")
            return
        rows_to_delete = sorted([r.row() for r in selected_rows], reverse=True)
        for row in rows_to_delete:
            if 0 <= row < len(self.waypoints):
                del self.waypoints[row]
        self.updateWaypointTable()
        self.updatePlot()
        self.log(f"Deleted waypoints at rows: {rows_to_delete}")

    def startTracking(self):
        self.trajectory.clear()
        self.current_wp_index = 0
        self.waypoints = []
        # Reload waypoints from the table:
        for row in range(self.waypoint_table.rowCount()):
            try:
                wx = float(self.waypoint_table.item(row, 0).text())
                wy = float(self.waypoint_table.item(row, 1).text())
                theta_deg = float(self.waypoint_table.item(row, 2).text())
                theta_rad = math.radians(theta_deg)
                self.waypoints.append({"x": wx, "y": wy, "theta": theta_rad})
            except Exception:
                continue
        if not self.waypoints:
            QMessageBox.warning(self, "No Waypoints", "Add at least one waypoint before starting.")
            return
        self.x = 0.0
        self.y = 0.0
        self.heading = math.radians(90.0)
        self.tracking_enabled = True
        self.log("Started tracking")
        self.updatePlot()

        def stopTracking(self):
            self.tracking_enabled = False
            self.trajectory.clear()
            self.current_wp_index = 0
            self.x, self.y, self.heading = 0.0, 0.0, math.radians(90.0)
            self.trajectory_line.set_data([], [])
            self.ax.set_title("")
            self.updatePlot()

            if not self.simulation:
                if qwiic_otos is not None and 'sensor' in globals() and sensor is not None:
                    try:
                        sensor.resetTracking()
                        sensor.setPosition(0, 0, 0)  # Reset position to (0,0)
                        self.log("Hardware odometry reset to (0,0,90°)")
                    except Exception as e:
                        self.log(f"Failed to reset OTOS sensor: {e}")
                if hasattr(self.current_controller, 'stop_motors'):
                    self.current_controller.stop_motors()

            self.log("Stopped tracking. View reset, odometery sensor reset.")


    # --- Hardware functions ---
    def get_hw_pose(self):
        global sensor
        try:
            pos = sensor.getPosition()
            x_hw, y_hw = pos.x * 25.4, pos.y * 25.4
            heading_hw = math.radians(pos.h + 90.0)
            return x_hw, y_hw, heading_hw
        except Exception as e:
            self.log(f"Sensor error: {e}")
            return self.x, self.y, self.heading

    def controlLoop(self):
        if not self.tracking_enabled or self.current_controller is None:
            return
        if self.current_wp_index >= len(self.waypoints):
            self.tracking_enabled = False
            self.log("All waypoints reached!")
            self.updatePlot()
            return

        dt = 0.1
        target = self.waypoints[self.current_wp_index]

        # Use the selected controller's control_step:
        if hasattr(self.current_controller, "control_step"):
            if self.simulation:
                get_hw_pose = lambda: (self.x, self.y, self.heading)
            else:
                get_hw_pose = self.get_hw_pose

            x_new, y_new, heading_new, done, debug = self.current_controller.control_step(
                self.x, self.y, self.heading, target, dt, self.simulation, get_hw_pose)
            self.x, self.y, self.heading = x_new, y_new, angle_wrap(heading_new)
            if self.verbose_checkbox.isChecked():
                print(debug)
            if done:
                self.current_wp_index += 1
                self.log("Waypoint reached.")
                self.updatePlot()
                return
        self.trajectory.append((self.x, self.y))
        self.updatePlot()

    def updatePlot(self):
        if self.trajectory:
            xs, ys = zip(*self.trajectory)
            self.trajectory_line.set_data(xs, ys)
        else:
            self.trajectory_line.set_data([], [])
        if self.waypoints:
            wx = [wp["x"] for wp in self.waypoints]
            wy = [wp["y"] for wp in self.waypoints]
            self.waypoints_scatter.set_data(wx, wy)
        else:
            self.waypoints_scatter.set_data([], [])
        self.start_point.set_data([0], [0])
        if self.heading_arrow_artist:
            self.heading_arrow_artist.remove()
        self.heading_arrow_artist = self.ax.arrow(
            self.x, self.y, 50 * math.cos(self.heading), 50 * math.sin(self.heading),
            head_width=20, head_length=20, fc='g', ec='g'
        )
        # --- Waypoint index numbers ---
        if hasattr(self, "wp_labels"):
            for label in self.wp_labels:
                label.remove()
        self.wp_labels = []
        if self.waypoints:
            for idx, wp in enumerate(self.waypoints):
                txt = self.ax.text(wp["x"], wp["y"], str(idx+1), color="black", fontsize=12, fontweight="bold", ha="center", va="center")
                self.wp_labels.append(txt)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    gui = RobotControlGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
