import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton
from PyQt5.QtGui import QIcon  # Import QIcon for adding icons
import subprocess
from styles import stylesheet

class NewGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("SparkyBot GUI V 0.3.0")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('/pics/SparkyBotIconSmall.png'))  # Set the window icon

        layout = QGridLayout()

        # Adding buttons to the grid layout
        buttons_text = ["Hardware Test", "Remote Control", "Image Processing", "PID Tuning", "AI"]
        button_functions = [self.run_sparky_bot_hardware, self.run_wifi_control, self.run_image_processing, self.run_pid_tuning, self.run_ai]
        button_icons = ["pics/hardware_icon.png", "pics/remote_icon.png","pics/image_icon.png", "pics/pid_icon.png", "pics/ai_icon.png"]  # Icons for buttons

        for i, (text, function, icon) in enumerate(zip(buttons_text, button_functions, button_icons)):
            button = QPushButton(text)
            button.setIcon(QIcon(icon))  # Set icon for the button
            button.setIconSize(button.rect().size())  # Set icon size
            button.clicked.connect(function)
            button.setFixedSize(400, 150)  # Set fixed size for the button
            layout.addWidget(button, i // 2, i % 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def run_sparky_bot_hardware(self):
        try:
            subprocess.run(['python3', 'sparkybot_hardware.py'])
        except Exception as e:
            print("Error:", e)
            
    def run_wifi_control(self):
        try:
            subprocess.run(['python3', 'wifi_control.py'])
        except Exception as e:
            print("Error:", e)
            
    def run_image_processing(self):
        try:
            subprocess.run(['python3', 'image_processing.py'])
        except Exception as e:
            print("Error:", e)

    def run_pid_tuning(self):
        try:
            subprocess.run(['python3', 'pid_tuning.py'])
        except Exception as e:
            print("Error:", e)

    def run_ai(self):
        try:
            subprocess.run(['python3', 'ai_models.py'])
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NewGUI()
    window.show()
    sys.exit(app.exec_())
