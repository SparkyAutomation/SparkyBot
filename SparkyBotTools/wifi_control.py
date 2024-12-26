import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
from flask import Flask, render_template, redirect, url_for, Response
from time import sleep, time
import socket
import subprocess
from styles import stylesheet
import sparkybotio
import cv2

delay_time = 0.1

class FlaskThread(QThread):
    message_received = pyqtSignal(str)  # Define a signal to pass messages

    def run(self):
        app = Flask(__name__)

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/forward-left')
        def forward_left():
            move_forward_left()
            return redirect(url_for('index'))
        
        @app.route('/forward')
        def forward():
            move_forward()
            return redirect(url_for('index'))

        @app.route('/forward-right')
        def forward_right():
            move_forward_right()
            return redirect(url_for('index'))
 
        @app.route('/left')
        def left():
            move_left()
            return redirect(url_for('index'))
        
        @app.route('/stop')
        def stop():
            stop_all()
            return redirect(url_for('index'))
        
        @app.route('/right')
        def right():
            move_right()
            return redirect(url_for('index'))

        @app.route('/backward-left')
        def backward_left():
            move_backward_left()
            return redirect(url_for('index'))
        
        @app.route('/backward')
        def backward():
            move_backward()
            return redirect(url_for('index'))

        @app.route('/backward-right')
        def backward_right():
            move_backward_right()
            return redirect(url_for('index'))

        @app.route('/ccw')
        def rotate_ccw():
            turn_ccw()
            return redirect(url_for('index'))
        
        @app.route('/cw')
        def rotate_cw():
            turn_cw()
            return redirect(url_for('index'))
        
        def get_camera_stream():
            camera = cv2.VideoCapture(0)  # Change the parameter if your camera is not the default camera
            while True:
                start_time = time()  # Record the start time
                success, frame = camera.read()
                if not success:
                    break
                ret, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                
               # Introduce a delay to control the streaming frequency
                time_elapsed = time() - start_time
                time_to_sleep = max(0, 0.2 - time_elapsed)  # Adjust the delay as needed
                sleep(time_to_sleep)  # Sleep to control the frequency
        
        @app.route('/video_feed')
        def video_feed():
            return Response(get_camera_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)

# Modify this section
def move_forward():
    sleep(delay_time)
    sparkybotio.setMotor(1, -50)
    sleep(delay_time)
    sparkybotio.setMotor(2, -50)
    sleep(delay_time)
    sparkybotio.setMotor(3, -50)
    sleep(delay_time)
    sparkybotio.setMotor(4, -50)

def move_forward_left():
    sleep(delay_time)
    sparkybotio.setMotor(1, 0)
    sleep(delay_time)
    sparkybotio.setMotor(2, -50)
    sleep(delay_time)
    sparkybotio.setMotor(3, -50)
    sleep(delay_time)
    sparkybotio.setMotor(4, 0)

def move_forward_right():
    sleep(delay_time)
    sparkybotio.setMotor(1, -50)
    sleep(delay_time)
    sparkybotio.setMotor(2, 0)
    sleep(delay_time)
    sparkybotio.setMotor(3, 0)
    sleep(delay_time)
    sparkybotio.setMotor(4, -50)
    
def move_backward():
    sleep(delay_time)
    sparkybotio.setMotor(1, 50)
    sleep(delay_time)
    sparkybotio.setMotor(2, 50)
    sleep(delay_time)
    sparkybotio.setMotor(3, 50)
    sleep(delay_time)
    sparkybotio.setMotor(4, 50)

def move_backward_left():
    sleep(delay_time)
    sparkybotio.setMotor(1, 50)
    sleep(delay_time)
    sparkybotio.setMotor(2, 0)
    sleep(delay_time)
    sparkybotio.setMotor(3, 0)
    sleep(delay_time)
    sparkybotio.setMotor(4, 50)
    
def move_backward_right():
    sleep(delay_time)
    sparkybotio.setMotor(1, 0)
    sleep(delay_time)
    sparkybotio.setMotor(2, 50)
    sleep(delay_time)
    sparkybotio.setMotor(3, 50)
    sleep(delay_time)
    sparkybotio.setMotor(4, 0)
    
def move_left():
    sleep(delay_time)
    sparkybotio.setMotor(1, 50)
    sleep(delay_time)
    sparkybotio.setMotor(2, -50)
    sleep(delay_time)
    sparkybotio.setMotor(3, -50)
    sleep(delay_time)
    sparkybotio.setMotor(4, 50)

def move_right():
    sleep(delay_time)
    sparkybotio.setMotor(1, -50)
    sleep(delay_time)
    sparkybotio.setMotor(2, 50)
    sleep(delay_time)
    sparkybotio.setMotor(3, 50)
    sleep(delay_time)
    sparkybotio.setMotor(4, -50)

def turn_ccw():
    sleep(delay_time)
    sparkybotio.setMotor(1, -50)
    sleep(delay_time)
    sparkybotio.setMotor(2, 50)
    sleep(delay_time)
    sparkybotio.setMotor(3, -50)
    sleep(delay_time)
    sparkybotio.setMotor(4, 50)
    
def turn_cw():
    sleep(delay_time)
    sparkybotio.setMotor(1, 50)
    sleep(delay_time)
    sparkybotio.setMotor(2, -50)
    sleep(delay_time)
    sparkybotio.setMotor(3, 50)
    sleep(delay_time)
    sparkybotio.setMotor(4, -50)
    
    
def stop_all():
    sleep(delay_time)
    sparkybotio.setMotor(1, 0)
    sleep(delay_time)
    sparkybotio.setMotor(2, 0)
    sleep(delay_time)
    sparkybotio.setMotor(3, 0)
    sleep(delay_time)
    sparkybotio.setMotor(4, 0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("SparkyBot Remote Control webserver")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.start_button = QPushButton("Start webserver")
        self.start_button.clicked.connect(self.start_flask)

        self.stop_button = QPushButton("Stop webserver")
        self.stop_button.clicked.connect(self.stop_flask)
        self.stop_button.setEnabled(False)  # Initially disable stop button

        self.instructions_text = QTextEdit()
        self.instructions_text.setPlainText("1. Create a 5G hotspot on the Pi first\n"
                                            "2. Connect the Pi to this hotspot\n"
                                            "3. Connect your mobile device to the same hotspot\n"
                                            "4. Start the webserver below\n"
                                            "5. Enter the IP below in the browser on your mobile device\n")
        self.get_ip_address()
        self.instructions_text.setReadOnly(True)

        layout.addWidget(self.instructions_text)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        self.flask_thread = FlaskThread()
        self.flask_thread.message_received.connect(self.update_text)

    def scroll_to_bottom(self):
        scrollbar = self.instructions_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_flask(self):
        self.start_button.setEnabled(False)  # Disable start button
        self.stop_button.setEnabled(True)    # Enable stop button
        self.flask_thread.start()
        self.update_text("Server started √")
        self.scroll_to_bottom()  # Scroll to bottom after update

    def stop_flask(self):
        self.stop_button.setEnabled(False)   # Disable stop button
        self.start_button.setEnabled(True)   # Enable start button
        self.flask_thread.finished.emit()
        self.update_text("Server stopped x")
        self.scroll_to_bottom()  # Scroll to bottom after update

    def update_text(self, message):
        current_text = self.instructions_text.toPlainText()
        updated_text = current_text + "\n" + message
        self.instructions_text.setPlainText(updated_text)
        self.scroll_to_bottom()  # Scroll to bottom after update

    def get_ip_address(self):
        try:
            output = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
            ip_addresses = output.split()
            ip = ', '.join(ip_addresses)  # Join IP addresses with comma and space 
            self.update_text("IP(s): " + ip)
        except Exception as e:
            self.update_text("Error getting IP address: " + str(e))
            self.update_text("Not available")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
