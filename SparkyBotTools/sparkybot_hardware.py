import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSplitter, QLabel, QSlider, QMessageBox, QSpacerItem, QSizePolicy, QTableView, QHeaderView, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap, QImage, QStandardItemModel, QStandardItem  # Add QStandardItemModel and QStandardItem to imports
from PyQt5.QtCore import Qt, QTimer
import cv2
import sparkybotio
from styles import stylesheet

class MainWindow(QMainWindow):
    motor_names = ["Rear Right Motor", "Rear Left Motor", "Front Right Motor", "Front Left Motor"]  # Define motor names as a class attribute
    servo_names = ["Pitch Servo", "Yaw Servo"]  # Updated servo names

    def __init__(self):
        super().__init__()
        
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("SparkyBot Hardware Test")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('/pics/SparkyBotIconSmall.png'))  # Set the window icon

        self.splitter = QSplitter(self)
        self.setCentralWidget(self.splitter)

        self.navigation_widget = QWidget()
        self.splitter.addWidget(self.navigation_widget)
        self.navigation_widget.setFixedWidth(200)  # Set fixed width for navigation widget

        self.navigation_layout = QVBoxLayout()
        self.navigation_widget.setLayout(self.navigation_layout)

        # Buttons for navigation
        self.btn_open_dc_motors = QPushButton("Drive motors")
        self.btn_open_dc_motors.setCheckable(True)  # Set the button to be checkable
        self.btn_open_dc_motors.clicked.connect(self.open_dc_motors)
        self.navigation_layout.addWidget(self.btn_open_dc_motors)

        self.btn_sensors = QPushButton("Sensors")
        self.btn_sensors.setCheckable(True)  # Set the button to be checkable
        self.btn_sensors.clicked.connect(self.open_sensors)
        self.navigation_layout.addWidget(self.btn_sensors)

        # New buttons for additional options
        self.btn_usb_cam = QPushButton("USB Cam")
        self.btn_usb_cam.setCheckable(True)
        self.btn_usb_cam.clicked.connect(self.open_usb_cam)
        self.navigation_layout.addWidget(self.btn_usb_cam)

        self.btn_servo_motor = QPushButton("Servo Motor")
        self.btn_servo_motor.setCheckable(True)
        self.btn_servo_motor.clicked.connect(self.open_servo_motor)
        self.navigation_layout.addWidget(self.btn_servo_motor)

        # Default contents widget
        self.contents_widget = QLabel()
        self.splitter.addWidget(self.contents_widget)
        self.show_default_image()  # Show default image when window is launched

        # Stop motors button
        self.stop_motors_button = QPushButton("Stop All Motors")
        self.stop_motors_button.clicked.connect(self.stop_all_motors)

        # Motor control widgets
        self.create_motor_control_widgets()
        self.hide_motor_controls()

        # Servo control widgets
        self.create_servo_control_widgets()
        self.hide_servo_controls()

        # Sensor display widget
        self.setup_sensor_display_widget()

        # Video capture
        self.setup_video_capture_widget()

    def create_motor_control_widgets(self):
        # Create sliders for motor speed control
        self.motor_speed_sliders = []
        self.motor_speed_labels = []
        for i, motor_name in enumerate(self.motor_names):
            label = QLabel(f"{motor_name} Speed (0%)")  # Initialize with 0% speed
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.valueChanged.connect(lambda value, motor_num=i+1: self.set_motor_speed(motor_num, value))
            self.motor_speed_sliders.append(slider)
            self.motor_speed_labels.append(label)

        # Create container widget for motor controls
        self.motor_control_widget = QWidget()
        motor_control_layout = QVBoxLayout()
        self.motor_control_widget.setLayout(motor_control_layout)
        for label, slider in zip(self.motor_speed_labels, self.motor_speed_sliders):
            motor_control_layout.addWidget(label)
            motor_control_layout.addWidget(slider)
            
        # Add an empty widget with fixed height to create space between sliders and button
        spacer_widget = QWidget()
        spacer_widget.setFixedHeight(100)  # Adjust the height as needed
        spacer_widget.setStyleSheet("background-color: transparent;")  # Set background color to transparent

        # Add spacer widget to layout
        motor_control_layout.addWidget(spacer_widget)
        motor_control_layout.addWidget(self.stop_motors_button)

    def hide_motor_controls(self):
        self.motor_control_widget.hide()

    def show_motor_controls(self):
        self.motor_control_widget.show()

    def set_motor_speed(self, motor_num, speed_percent):
        motor_speed = int(speed_percent)  # Convert percentage to integer
        sparkybotio.setMotor(motor_num, motor_speed)
        self.motor_speed_labels[motor_num - 1].setText(f"{self.motor_names[motor_num - 1]} Speed ({speed_percent}%)")

    def stop_all_motors(self):
        for motor_num in range(1, 5):
            self.motor_speed_sliders[motor_num - 1].setValue(0)  # Set slider value to 0
            self.set_motor_speed(motor_num, 0)  # Stop the motor

    def create_servo_control_widgets(self):
        self.servo_angle_sliders = []
        self.servo_angle_labels = []
        for i, servo_name in enumerate(self.servo_names):  # Updated servo names loop
            label = QLabel(f"{servo_name} Angle (90°)")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(180)
            slider.setValue(90)
            #slider.setFixedWidth(700)  # Set a fixed height for the slider
            slider.valueChanged.connect(lambda value, servo_num=i+1: self.set_servo_angle(servo_num, value))
            self.servo_angle_sliders.append(slider)
            self.servo_angle_labels.append(label)

        self.servo_control_widget = QWidget()
        servo_control_layout = QVBoxLayout()
        self.servo_control_widget.setLayout(servo_control_layout)
        for label, slider in zip(self.servo_angle_labels, self.servo_angle_sliders):
            servo_control_layout.addWidget(label)
            servo_control_layout.addWidget(slider)

        # Add servo angle sliders to layout
        for label, slider in zip(self.servo_angle_labels, self.servo_angle_sliders):
            servo_control_layout.addWidget(label)
            servo_control_layout.addWidget(slider)
            
        # Add an empty widget with fixed height to create space between sliders and button
        spacer_widget = QWidget()
        spacer_widget.setFixedHeight(150)  # Adjust the height as needed
        spacer_widget.setStyleSheet("background-color: transparent;")  # Set background color to transparent

        # Add spacer widget to layout
        servo_control_layout.addWidget(spacer_widget)

        # Button to reset all servo motors
        self.reset_servo_button = QPushButton("Reset All Servo Motors")
        self.reset_servo_button.clicked.connect(self.reset_all_servo_motors)
        servo_control_layout.addWidget(self.reset_servo_button)
        
    def reset_all_servo_motors(self):
        for servo_num in range(1, len(self.servo_names) + 1):
            # Set servo angle to 90 degrees
            self.set_servo_angle(servo_num, 90)
            # Reset the corresponding slider to 90 degrees
            self.servo_angle_sliders[servo_num - 1].setValue(90)
        
    def hide_servo_controls(self):
        self.servo_control_widget.hide()

    def show_servo_controls(self):
        self.servo_control_widget.show()

    def set_servo_angle(self, servo_num, angle):
        # Calculate pulse value based on the angle (assuming a range of 0 to 180 degrees)
        pulse = int(angle / 180 * 2000) + 500  # Map angle to pulse range (500 to 2500)
        # Use default time value
        use_time = 20
        sparkybotio.setServoPulse(servo_num, pulse, use_time)
        self.servo_angle_labels[servo_num - 1].setText(f"{self.servo_names[servo_num - 1]} Angle ({angle}°)")

    def open_dc_motors(self):
        if not self.btn_open_dc_motors.isChecked():
            self.btn_open_dc_motors.setChecked(True)  # Manually set the checked state
        self.btn_sensors.setChecked(False)
        self.btn_usb_cam.setChecked(False)
        self.btn_servo_motor.setChecked(False)
        self.splitter.addWidget(self.motor_control_widget)
        self.show_motor_controls()
        self.contents_widget.hide()
        self.hide_sensor_display()
        self.hide_servo_controls()  
        self.video_label.hide() 
        if self.cap:
            self.cap.release()  
            self.timer.stop()  

    def open_sensors(self):
        if not self.btn_sensors.isChecked():
            self.btn_sensors.setChecked(True)  # Manually set the checked state
        self.btn_open_dc_motors.setChecked(False)
        self.btn_usb_cam.setChecked(False)
        self.btn_servo_motor.setChecked(False)
        self.hide_motor_controls()
        self.contents_widget.hide()
        self.show_sensor_display()
        self.hide_servo_controls()  
        self.video_label.hide()  
        if self.cap:
            self.cap.release()  
            self.timer.stop()
            
    def open_usb_cam(self):
        if not self.btn_usb_cam.isChecked():
            self.btn_usb_cam.setChecked(True)  # Manually set the checked state
        self.btn_open_dc_motors.setChecked(False)
        self.btn_sensors.setChecked(False)
        self.btn_servo_motor.setChecked(False)
        
        # Check if the camera is already opened
        if self.cap is not None and self.cap.isOpened():
            # QMessageBox.information(self, "Camera Already Opened", "The USB camera is already opened.")
            return
        
        self.video_label.show()  # Show video label
        try:
            self.start_video_capture()  # Start capturing video
        except Exception as e:
            print("Error opening USB camera:", e)
            QMessageBox.critical(self, "Error", "Failed to connect USB camera. Check connects.")
        # Hide other widgets
        self.hide_motor_controls()
        self.hide_sensor_display()
        self.hide_servo_controls()
        self.contents_widget.hide()


                    
    def open_servo_motor(self):
        if not self.btn_servo_motor.isChecked():
            self.btn_servo_motor.setChecked(True)  # Manually set the checked state
        self.btn_open_dc_motors.setChecked(False)
        self.btn_sensors.setChecked(False)
        self.btn_usb_cam.setChecked(False)
        self.splitter.addWidget(self.servo_control_widget)
        self.show_servo_controls()
        self.contents_widget.hide()
        self.hide_sensor_display()
        self.hide_motor_controls()  
        self.video_label.hide()  
        if self.cap:
            self.cap.release()  
            self.timer.stop()  


    def show_default_image(self):
        pixmap = QPixmap("pics/welcome.png")
        self.contents_widget.setPixmap(pixmap)
        
    def setup_sensor_display_widget(self):
        # Create a table view for sensor display
        self.sensor_table_view = QTableView()
        self.sensor_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Stretch columns to fill the view
        self.splitter.addWidget(self.sensor_table_view)
        self.hide_sensor_display()  # This should be called after creating the table view

        # Create a standard item model for the table view
        self.sensor_model = QStandardItemModel()
        self.sensor_table_view.setModel(self.sensor_model)

        # Set font size for the items in the table view
        font = self.sensor_table_view.font()
        font.setPointSize(20)  # Adjust the font size as needed
        self.sensor_table_view.setFont(font)

        # Set font size for the header labels
        header_font = self.sensor_table_view.horizontalHeader().font()
        header_font.setPointSize(22)  # Adjust the font size for headers as needed
        self.sensor_table_view.horizontalHeader().setFont(header_font)

        # Set the default section size (cell height)
        self.sensor_table_view.verticalHeader().setDefaultSectionSize(40)  # Adjust the cell height as needed
    
        # Timer for updating sensor display
        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self.update_sensor_display)
        self.sensor_timer.start(500)  # Update every 500 milliseconds

    def update_sensor_display(self):
        try:
            line_data = sparkybotio.readInfrared()
            distance = sparkybotio.readDistance()

            # Merge all readings from the line tracking sensor into one string
            line_sensor_readings = ' '.join([str(int(data)) for data in line_data])

            # If model has no columns, set headers
            if self.sensor_model.columnCount() == 0:
                self.sensor_model.setColumnCount(2)  # Set column count to 2
                self.sensor_model.setHorizontalHeaderLabels(["Sensor", "Readings"])

            # Populate data into the table view with two rows
            sensor_names = ["Line tracking sensor", "Ultrasonic sensor (mm)"]
            for i, name in enumerate(sensor_names):
                name_item = QStandardItem(name)
                value_item = QStandardItem(line_sensor_readings if i < 1 else str(distance))  # Use the merged readings string
                self.sensor_model.setItem(i, 0, name_item)
                self.sensor_model.setItem(i, 1, value_item)

        except OSError as e:
            print("Error reading sensor data:", e)


    def hide_sensor_display(self):
        self.sensor_table_view.hide()

    def show_sensor_display(self):
        self.sensor_table_view.show()
        
    def setup_video_capture_widget(self):
        # Video capture
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.splitter.addWidget(self.video_label)
        self.video_label.hide()  # Initially hide the video label

        self.cap = None  # Video capture object
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def start_video_capture(self):
        # Open the first camera found
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Unable to open camera.")
            return
        self.timer.start(30)  # Update video frame every 30 milliseconds

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(convertToQtFormat)
            self.video_label.setPixmap(pixmap)
            self.video_label.setAlignment(Qt.AlignCenter)
    '''
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit Confirmation', 'Quit the program?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    '''
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

