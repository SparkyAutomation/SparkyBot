import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QSlider, QTabWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
from styles import stylesheet

class RGBThresholdGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(stylesheet)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.red_lower_label = QLabel("Red Low Limit: 0")
        self.red_upper_label = QLabel("Red High Limit: 255")
        self.green_lower_label = QLabel("Green Low Limit: 0")
        self.green_upper_label = QLabel("Green High Limit: 255")
        self.blue_lower_label = QLabel("Blue Low Limit: 0")
        self.blue_upper_label = QLabel("Blue High Limit: 255")

        # Labels for Lab color space
        self.l_lower_label = QLabel("L Low Limit: 0")
        self.l_upper_label = QLabel("L High Limit: 255")
        self.a_lower_label = QLabel("a Low Limit: 0")
        self.a_upper_label = QLabel("a High Limit: 255")
        self.b_lower_label = QLabel("b Low Limit: 0")
        self.b_upper_label = QLabel("b High Limit: 255")

        # Labels for HSV color space
        self.h_lower_label = QLabel("H Low Limit: 0")
        self.h_upper_label = QLabel("H High Limit: 179")
        self.s_lower_label = QLabel("S Low Limit: 0")
        self.s_upper_label = QLabel("S High Limit: 255")
        self.v_lower_label = QLabel("V Low Limit: 0")
        self.v_upper_label = QLabel("V High Limit: 255")

        # Create range sliders for R, G, and B channels
        self.red_lower_slider = QSlider(Qt.Horizontal)
        self.red_upper_slider = QSlider(Qt.Horizontal)
        self.green_lower_slider = QSlider(Qt.Horizontal)
        self.green_upper_slider = QSlider(Qt.Horizontal)
        self.blue_lower_slider = QSlider(Qt.Horizontal)
        self.blue_upper_slider = QSlider(Qt.Horizontal)

        # Create range sliders for L, a, and b channels (Lab color space)
        self.l_lower_slider = QSlider(Qt.Horizontal)
        self.l_upper_slider = QSlider(Qt.Horizontal)
        self.a_lower_slider = QSlider(Qt.Horizontal)
        self.a_upper_slider = QSlider(Qt.Horizontal)
        self.b_lower_slider = QSlider(Qt.Horizontal)
        self.b_upper_slider = QSlider(Qt.Horizontal)

        # Create range sliders for H, S, and V channels (HSV color space)
        self.h_lower_slider = QSlider(Qt.Horizontal)
        self.h_upper_slider = QSlider(Qt.Horizontal)
        self.s_lower_slider = QSlider(Qt.Horizontal)
        self.s_upper_slider = QSlider(Qt.Horizontal)
        self.v_lower_slider = QSlider(Qt.Horizontal)
        self.v_upper_slider = QSlider(Qt.Horizontal)

        # Connect slots to update labels when sliders are changed
        self.red_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.red_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.green_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.green_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.blue_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.blue_upper_slider.valueChanged.connect(self.update_slider_labels)

        self.l_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.l_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.a_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.a_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.b_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.b_upper_slider.valueChanged.connect(self.update_slider_labels)

        self.h_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.h_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.s_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.s_upper_slider.valueChanged.connect(self.update_slider_labels)
        self.v_lower_slider.valueChanged.connect(self.update_slider_labels)
        self.v_upper_slider.valueChanged.connect(self.update_slider_labels)
        
        # Set range and initial values for each channel
        self.red_lower_slider.setRange(0, 255)
        self.red_lower_slider.setValue(0)
        self.red_upper_slider.setRange(0, 255)
        self.red_upper_slider.setValue(255)
        self.green_lower_slider.setRange(0, 255)
        self.green_lower_slider.setValue(0)
        self.green_upper_slider.setRange(0, 255)
        self.green_upper_slider.setValue(255)
        self.blue_lower_slider.setRange(0, 255)
        self.blue_lower_slider.setValue(0)
        self.blue_upper_slider.setRange(0, 255)
        self.blue_upper_slider.setValue(255)

        # Connect slots to update image when sliders are released (for live camera)
        self.red_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.red_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.green_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.green_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.blue_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.blue_upper_slider.sliderReleased.connect(self.update_live_camera)

        # Connect slots to update image when sliders are changed (for static image)
        self.red_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.red_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.green_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.green_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.blue_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.blue_upper_slider.valueChanged.connect(self.update_static_image_threshold)

        # Set range and initial values for Lab sliders
        self.l_lower_slider.setRange(0, 255)
        self.l_lower_slider.setValue(0)
        self.l_upper_slider.setRange(0, 255)
        self.l_upper_slider.setValue(255)
        self.a_lower_slider.setRange(0, 255)
        self.a_lower_slider.setValue(0)
        self.a_upper_slider.setRange(0, 255)
        self.a_upper_slider.setValue(255)
        self.b_lower_slider.setRange(0, 255)
        self.b_lower_slider.setValue(0)
        self.b_upper_slider.setRange(0, 255)
        self.b_upper_slider.setValue(255)

        # Connect slots to update Lab image when sliders are released (for live camera)
        self.l_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.l_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.a_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.a_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.b_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.b_upper_slider.sliderReleased.connect(self.update_live_camera)

        # Connect slots to update Lab image when sliders are changed (for static image)
        self.l_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.l_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.a_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.a_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.b_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.b_upper_slider.valueChanged.connect(self.update_static_image_threshold)

        # Set range and initial values for HSV sliders
        self.h_lower_slider.setRange(0, 179)
        self.h_lower_slider.setValue(0)
        self.h_upper_slider.setRange(0, 179)
        self.h_upper_slider.setValue(179)
        self.s_lower_slider.setRange(0, 255)
        self.s_lower_slider.setValue(0)
        self.s_upper_slider.setRange(0, 255)
        self.s_upper_slider.setValue(255)
        self.v_lower_slider.setRange(0, 255)
        self.v_lower_slider.setValue(0)
        self.v_upper_slider.setRange(0, 255)
        self.v_upper_slider.setValue(255)

        # Connect slots to update HSV image when sliders are released (for live camera)
        self.h_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.h_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.s_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.s_upper_slider.sliderReleased.connect(self.update_live_camera)
        self.v_lower_slider.sliderReleased.connect(self.update_live_camera)
        self.v_upper_slider.sliderReleased.connect(self.update_live_camera)

        # Connect slots to update HSV image when sliders are changed (for static image)
        self.h_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.h_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.s_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.s_upper_slider.valueChanged.connect(self.update_static_image_threshold)
        self.v_lower_slider.valueChanged.connect(self.update_static_image_threshold)
        self.v_upper_slider.valueChanged.connect(self.update_static_image_threshold)

        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)

        # Button to start live camera feed
        self.live_button = QPushButton("Live Camera")
        self.live_button.clicked.connect(self.start_or_stop_live_camera)

        # Labels for channel limits
        self.red_lower_label = QLabel("Red Low Limit: 0")
        self.red_upper_label = QLabel("Red High Limit: 255")
        self.green_lower_label = QLabel("Green Low Limit: 0")
        self.green_upper_label = QLabel("Green High Limit: 255")
        self.blue_lower_label = QLabel("Blue Low Limit: 0")
        self.blue_upper_label = QLabel("Blue High Limit: 255")

        # Labels for Lab color space
        self.l_lower_label = QLabel("L Low Limit: 0")
        self.l_upper_label = QLabel("L High Limit: 255")
        self.a_lower_label = QLabel("a Low Limit: 0")
        self.a_upper_label = QLabel("a High Limit: 255")
        self.b_lower_label = QLabel("b Low Limit: 0")
        self.b_upper_label = QLabel("b High Limit: 255")

        # Labels for HSV color space
        self.h_lower_label = QLabel("H Low Limit: 0")
        self.h_upper_label = QLabel("H High Limit: 179")
        self.s_lower_label = QLabel("S Low Limit: 0")
        self.s_upper_label = QLabel("S High Limit: 255")
        self.v_lower_label = QLabel("V Low Limit: 0")
        self.v_upper_label = QLabel("V High Limit: 255")

        # Create tab widget for RGB, Lab, and HSV color spaces
        self.tab_widget = QTabWidget()
        self.rgb_tab = QWidget()
        self.lab_tab = QWidget()
        self.hsv_tab = QWidget()
        self.tab_widget.addTab(self.rgb_tab, "RGB")
        self.tab_widget.addTab(self.lab_tab, "Lab")
        self.tab_widget.addTab(self.hsv_tab, "HSV")

        # Layout for RGB tab
        rgb_layout = QVBoxLayout(self.rgb_tab)
        rgb_layout.addWidget(self.red_lower_label)
        rgb_layout.addWidget(self.red_lower_slider)
        rgb_layout.addWidget(self.red_upper_label)
        rgb_layout.addWidget(self.red_upper_slider)
        rgb_layout.addWidget(self.green_lower_label)
        rgb_layout.addWidget(self.green_lower_slider)
        rgb_layout.addWidget(self.green_upper_label)
        rgb_layout.addWidget(self.green_upper_slider)
        rgb_layout.addWidget(self.blue_lower_label)
        rgb_layout.addWidget(self.blue_lower_slider)
        rgb_layout.addWidget(self.blue_upper_label)
        rgb_layout.addWidget(self.blue_upper_slider)

        # Layout for Lab tab
        lab_layout = QVBoxLayout(self.lab_tab)
        lab_layout.addWidget(self.l_lower_label)
        lab_layout.addWidget(self.l_lower_slider)
        lab_layout.addWidget(self.l_upper_label)
        lab_layout.addWidget(self.l_upper_slider)
        lab_layout.addWidget(self.a_lower_label)
        lab_layout.addWidget(self.a_lower_slider)
        lab_layout.addWidget(self.a_upper_label)
        lab_layout.addWidget(self.a_upper_slider)
        lab_layout.addWidget(self.b_lower_label)
        lab_layout.addWidget(self.b_lower_slider)
        lab_layout.addWidget(self.b_upper_label)
        lab_layout.addWidget(self.b_upper_slider)

        # Layout for HSV tab
        hsv_layout = QVBoxLayout(self.hsv_tab)
        hsv_layout.addWidget(self.h_lower_label)
        hsv_layout.addWidget(self.h_lower_slider)
        hsv_layout.addWidget(self.h_upper_label)
        hsv_layout.addWidget(self.h_upper_slider)
        hsv_layout.addWidget(self.s_lower_label)
        hsv_layout.addWidget(self.s_lower_slider)
        hsv_layout.addWidget(self.s_upper_label)
        hsv_layout.addWidget(self.s_upper_slider)
        hsv_layout.addWidget(self.v_lower_label)
        hsv_layout.addWidget(self.v_lower_slider)
        hsv_layout.addWidget(self.v_upper_label)
        hsv_layout.addWidget(self.v_upper_slider)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.live_button)

        layout.addLayout(button_layout)
        layout.addWidget(self.image_label)
        layout.addWidget(self.tab_widget)  # Add tab widget

        self.image = None  # Initialize self.image
        self.camera = None  # Initialize camera object
        self.is_camera_displayed = False

        # Load the default image when GUI is opened
        self.load_default_image()
        
        # Connect signal for tab change
        self.tab_widget.currentChanged.connect(self.update_image_with_threshold)

    def load_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image files (*.jpg *.png *.bmp)")
        if filename:
            image = cv2.imread(filename, cv2.IMREAD_UNCHANGED | cv2.IMREAD_IGNORE_ORIENTATION)
            if image is not None:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                h, w, ch = image_rgb.shape
                bytes_per_line = ch * w
                q_img = QPixmap.fromImage(QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888))
                self.image_label.setPixmap(q_img.scaled(400, 400, Qt.KeepAspectRatio))
                self.image = image_rgb  # Save loaded image
                self.is_camera_displayed = False
                
    def load_default_image(self):
        default_image_path = "pics/rgb.jpg"
        default_image = cv2.imread(default_image_path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_IGNORE_ORIENTATION)
        if default_image is not None:
            # Convert BGR to RGB
            default_image_rgb = cv2.cvtColor(default_image, cv2.COLOR_BGR2RGB)
            # Convert to QPixmap
            q_img = QPixmap.fromImage(QImage(default_image_rgb.data, default_image_rgb.shape[1], default_image_rgb.shape[0],
                                             default_image_rgb.shape[1] * default_image_rgb.shape[2],
                                             QImage.Format_RGB888))
            # Display the default image
            self.image_label.setPixmap(q_img.scaled(400, 400, Qt.KeepAspectRatio))
            self.image = default_image_rgb  # Save loaded image
            self.is_camera_displayed = False
            
    def start_or_stop_live_camera(self):
        if not self.is_camera_displayed:
            self.start_live_camera()
            self.live_button.setText("Stop Live Camera")  # Change button text
        else:
            self.stop_live_camera()
            self.live_button.setText("Live Camera")  # Change button text

    def start_live_camera(self):
        if not self.is_camera_displayed:
            self.clear_image()

            self.camera = cv2.VideoCapture(0)  # Open default camera (index 0)
            if self.camera.isOpened():
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_live_camera)
                self.timer.start(30)  # Update every 30 milliseconds
                self.is_camera_displayed = True
                self.load_button.setEnabled(False)  # Disable load image button
        else:
            print("Error: Camera is already displayed.")

    def stop_live_camera(self):
        if self.is_camera_displayed:
            self.timer.stop()  # Stop the timer
            self.camera.release()  # Release the camera
            self.is_camera_displayed = False
            self.load_button.setEnabled(True)  # Re-enable load image button
        else:
            print("Error: Camera is not currently displayed.")

    def clear_image(self):
        self.image_label.clear()
        self.image = None
        
    def update_image(self, frame):
        if self.tab_widget.currentIndex() == 0:  # RGB tab
            lower_bound = np.array([self.red_lower_slider.value(),
                                    self.green_lower_slider.value(),
                                    self.blue_lower_slider.value()], dtype="uint8")
            upper_bound = np.array([self.red_upper_slider.value(),
                                    self.green_upper_slider.value(),
                                    self.blue_upper_slider.value()], dtype="uint8")
            mask = cv2.inRange(frame, lower_bound, upper_bound)
            result_frame = cv2.bitwise_and(frame, frame, mask=mask)
        elif self.tab_widget.currentIndex() == 1:  # Lab tab
            frame_lab = cv2.cvtColor(frame, cv2.COLOR_RGB2Lab)
            lower_bound = np.array([self.l_lower_slider.value(),
                                    self.a_lower_slider.value(),
                                    self.b_lower_slider.value()], dtype="uint8")
            upper_bound = np.array([self.l_upper_slider.value(),
                                    self.a_upper_slider.value(),
                                    self.b_upper_slider.value()], dtype="uint8")
            mask = cv2.inRange(frame_lab, lower_bound, upper_bound)
            result_frame = cv2.bitwise_and(frame_lab, frame_lab, mask=mask)
            result_frame = cv2.cvtColor(result_frame, cv2.COLOR_Lab2RGB)
        elif self.tab_widget.currentIndex() == 2:  # HSV tab
            frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            lower_bound = np.array([self.h_lower_slider.value(),
                                    self.s_lower_slider.value(),
                                    self.v_lower_slider.value()], dtype="uint8")
            upper_bound = np.array([self.h_upper_slider.value(),
                                    self.s_upper_slider.value(),
                                    self.v_upper_slider.value()], dtype="uint8")
            mask = cv2.inRange(frame_hsv, lower_bound, upper_bound)
            result_frame = cv2.bitwise_and(frame_hsv, frame_hsv, mask=mask)
            result_frame = cv2.cvtColor(result_frame, cv2.COLOR_HSV2RGB)

        return result_frame

    def update_live_camera(self):
        if self.camera is not None and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result_frame = self.update_image(frame_rgb)

                h, w, ch = result_frame.shape
                bytes_per_line = ch * w
                q_img = QPixmap.fromImage(QImage(result_frame.data, w, h, bytes_per_line, QImage.Format_RGB888))
                self.image_label.setPixmap(q_img.scaled(800, 400, Qt.KeepAspectRatio))
        else:
            print("Error: Unable to read frame from camera.")
            
    def update_image_with_threshold(self):
        if self.image is not None:
            # Update the image using the existing update_image method
            result_image = self.update_image(self.image)
            
            # Display the updated image
            h, w, ch = result_image.shape
            bytes_per_line = ch * w
            q_img = QPixmap.fromImage(QImage(result_image.data, w, h, bytes_per_line, QImage.Format_RGB888))
            self.image_label.setPixmap(q_img.scaled(400, 400, Qt.KeepAspectRatio))
            
        
    def update_static_image_threshold(self):
        if self.image is not None:
            result_image = self.update_image(self.image)

            h, w, ch = result_image.shape
            bytes_per_line = ch * w
            q_img = QPixmap.fromImage(QImage(result_image.data, w, h, bytes_per_line, QImage.Format_RGB888))
            self.image_label.setPixmap(q_img.scaled(400, 400, Qt.KeepAspectRatio))
   
    def update_slider_labels(self):
        # Update the labels with the current slider values
        red_lower = self.red_lower_slider.value()
        red_upper = self.red_upper_slider.value()
        if red_lower >= red_upper:
            self.red_lower_slider.setValue(red_upper - 1)
            red_lower = red_upper - 1
        self.red_lower_label.setText(f"Red Low Limit: {self.red_lower_slider.value()}")
        self.red_upper_label.setText(f"Red High Limit: {self.red_upper_slider.value()}")
        
        green_lower = self.green_lower_slider.value()
        green_upper = self.green_upper_slider.value()
        if green_lower >= green_upper:
            self.green_lower_slider.setValue(green_upper - 1)
            green_lower = green_upper - 1
        self.green_lower_label.setText(f"Green Low Limit: {self.green_lower_slider.value()}")
        self.green_upper_label.setText(f"Green High Limit: {self.green_upper_slider.value()}")
        
        blue_lower = self.blue_lower_slider.value()
        blue_upper = self.blue_upper_slider.value()
        if blue_lower >= blue_upper:
            self.blue_lower_slider.setValue(blue_upper - 1)
            blue_lower = blue_upper - 1        
        self.blue_lower_label.setText(f"Blue Low Limit: {self.blue_lower_slider.value()}")
        self.blue_upper_label.setText(f"Blue High Limit: {self.blue_upper_slider.value()}")
        

        l_lower = self.l_lower_slider.value()
        l_upper = self.l_upper_slider.value()
        if l_lower >= l_upper:
            self.l_lower_slider.setValue(l_upper - 1)
            l_lower = l_upper - 1
        self.l_lower_label.setText(f"L Low Limit: {self.l_lower_slider.value()}")
        self.l_upper_label.setText(f"L High Limit: {self.l_upper_slider.value()}")
        
        a_lower = self.a_lower_slider.value()
        a_upper = self.a_upper_slider.value()
        if a_lower >= a_upper:
            self.a_lower_slider.setValue(a_upper - 1)
            a_lower = a_upper - 1
        self.a_lower_label.setText(f"a Low Limit: {self.a_lower_slider.value()}")
        self.a_upper_label.setText(f"a High Limit: {self.a_upper_slider.value()}")
        
        b_lower = self.b_lower_slider.value()
        b_upper = self.b_upper_slider.value()
        if b_lower >= b_upper:
            self.b_lower_slider.setValue(b_upper - 1)
            b_lower = b_upper - 1
        self.b_lower_label.setText(f"b Low Limit: {self.b_lower_slider.value()}")
        self.b_upper_label.setText(f"b High Limit: {self.b_upper_slider.value()}")

        h_lower = self.h_lower_slider.value()
        h_upper = self.h_upper_slider.value()
        if h_lower >= h_upper:
            self.h_lower_slider.setValue(h_upper - 1)
            h_lower = h_upper - 1
        self.h_lower_label.setText(f"H Low Limit: {self.h_lower_slider.value()}")
        self.h_upper_label.setText(f"H High Limit: {self.h_upper_slider.value()}")
        
        s_lower = self.s_lower_slider.value()
        s_upper = self.s_upper_slider.value()
        if s_lower >= s_upper:
            self.s_lower_slider.setValue(s_upper - 1)
            s_lower = s_upper - 1     
        self.s_lower_label.setText(f"S Low Limit: {self.s_lower_slider.value()}")
        self.s_upper_label.setText(f"S High Limit: {self.s_upper_slider.value()}")
        
        v_lower = self.v_lower_slider.value()
        v_upper = self.v_upper_slider.value()
        if v_lower >= v_upper:
            self.v_lower_slider.setValue(v_upper - 1)
            v_lower = v_upper - 1
        self.v_lower_label.setText(f"V Low Limit: {self.v_lower_slider.value()}")
        self.v_upper_label.setText(f"V High Limit: {self.v_upper_slider.value()}")
        
        
    def closeEvent(self, event):
        self.stop_live_camera()  # Ensure camera is stopped when closing
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RGBThresholdGUI()
    window.setWindowTitle('RGB Color Thresholding GUI')
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())

