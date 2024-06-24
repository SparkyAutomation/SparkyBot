import sys
from PyQt5.QtWidgets import QApplication
from helper import SpeedGauge, MainWindow
from time import sleep

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

    