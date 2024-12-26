import sys
import time
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSlider, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from smbus2 import SMBus, i2c_msg

# Constants for SparkyBot
__i2c = 1
__i2c_addr = 0x10
__MOTOR_ADDR = 0x20
__motor_speed = [0, 0, 0, 0]

# Function to set motor speed
def setMotor(index, speed):
    """
    Set motor speed.
    :param index: Motor index (1 to 4).
    :param speed: Speed value (-100 to 100).
    :return: Current motor speed.
    """
    if index < 1 or index > 4:
        raise AttributeError("Invalid motor num: %d" % index)
    if index == 2 or index == 4:
        speed = speed
    else:
        speed = -speed
    index -= 1
    speed = 100 if speed > 100 else speed
    speed = -100 if speed < -100 else speed
    reg = __MOTOR_ADDR + index
    with SMBus(__i2c) as bus:
        try:
            msg = i2c_msg.write(__i2c_addr, [reg, speed.to_bytes(1, 'little', signed=True)[0]])
            bus.i2c_rdwr(msg)
            __motor_speed[index] = speed
        except:
            msg = i2c_msg.write(__i2c_addr, [reg, speed.to_bytes(1, 'little', signed=True)[0]])
            bus.i2c_rdwr(msg)
            __motor_speed[index] = speed
    return __motor_speed[index]

# SparkyBot hardware interface class
class SparkyBotHardware:
    def read_line_sensors(self):
        # Placeholder for actual sensor reading logic
        # Return mock sensor values for demonstration
        return [0, 0, 0]  # Replace with actual sensor values

    def set_motor_speeds(self, left_speed, right_speed):
        setMotor(1, int(left_speed))
        setMotor(2, int(right_speed))

    def cleanup(self):
        # Reset motors on cleanup
        setMotor(1, 0)
        setMotor(2, 0)

# Line Following Tuner Application
class LineFollowingTuner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Line Following Tuner")

        # PID Variables
        self.kp = 1.0
        self.ki = 0.0
        self.kd = 0.0

        # Error tracking for PID
        self.previous_error = 0.0
        self.integral = 0.0

        # SparkyBot hardware setup
        self.bot = SparkyBotHardware()
        self.running = True

        # Layout
        self.init_ui()

        # Start feedback loop in a separate thread
        self.thread = threading.Thread(target=self.feedback_loop)
        self.thread.start()

    def init_ui(self):
        layout = QVBoxLayout()

        # Kp Slider
        self.kp_label = QLabel(f"Kp: {self.kp}")
        layout.addWidget(self.kp_label)
        self.kp_slider = QSlider(Qt.Horizontal)
        self.kp_slider.setMinimum(0)
        self.kp_slider.setMaximum(100)
        self.kp_slider.setValue(self.kp * 10)
        self.kp_slider.valueChanged.connect(self.update_kp)
        layout.addWidget(self.kp_slider)

        # Ki Slider
        self.ki_label = QLabel(f"Ki: {self.ki}")
        layout.addWidget(self.ki_label)
        self.ki_slider = QSlider(Qt.Horizontal)
        self.ki_slider.setMinimum(0)
        self.ki_slider.setMaximum(100)
        self.ki_slider.setValue(self.ki * 10)
        self.ki_slider.valueChanged.connect(self.update_ki)
        layout.addWidget(self.ki_slider)

        # Kd Slider
        self.kd_label = QLabel(f"Kd: {self.kd}")
        layout.addWidget(self.kd_label)
        self.kd_slider = QSlider(Qt.Horizontal)
        self.kd_slider.setMinimum(0)
        self.kd_slider.setMaximum(100)
        self.kd_slider.setValue(self.kd * 10)
        self.kd_slider.valueChanged.connect(self.update_kd)
        layout.addWidget(self.kd_slider)

        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.quit)
        layout.addWidget(quit_button)

        self.setLayout(layout)

    def update_kp(self, value):
        self.kp = value / 10.0
        self.kp_label.setText(f"Kp: {self.kp}")

    def update_ki(self, value):
        self.ki = value / 10.0
        self.ki_label.setText(f"Ki: {self.ki}")

    def update_kd(self, value):
        self.kd = value / 10.0
        self.kd_label.setText(f"Kd: {self.kd}")

    def feedback_loop(self):
        while self.running:
            sensor_values = self.bot.read_line_sensors()

            # Simple error calculation (e.g., deviation from center)
            error = (sensor_values[2] - sensor_values[0])

            # PID calculations
            proportional = self.kp * error
            self.integral += error * 0.1  # Integrate over time with a small time step
            integral = self.ki * self.integral
            derivative = self.kd * (error - self.previous_error) / 0.1
            self.previous_error = error

            correction = proportional + integral + derivative

            # Adjust motor speeds
            left_speed = max(-100, min(100, 50 - correction))
            right_speed = max(-100, min(100, 50 + correction))

            self.bot.set_motor_speeds(left_speed, right_speed)

            time.sleep(0.1)

    def quit(self):
        self.running = False
        self.thread.join()

        self.bot.cleanup()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tuner = LineFollowingTuner()
    tuner.show()
    sys.exit(app.exec_())
