import sys
import cv2
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout, QPushButton, QComboBox
import os
import traceback
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from styles import stylesheet

class ImageClassificationGUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Image Classification")
        self.classifier = None
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_camera)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setEnabled(False)

        self.model_combobox = QComboBox()
        self.populate_model_combobox()  # Populate the combobox with tflite files
        self.best_prediction_label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.model_combobox)
        layout.addWidget(self.best_prediction_label)
        self.setLayout(layout)

    def populate_model_combobox(self):
        support_folder = "support"
        tflite_files = [file for file in os.listdir(support_folder) if file.endswith(".tflite")]
        self.model_combobox.addItems(tflite_files)

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.classifier = vision.ImageClassifier.create_from_options(self.get_options())

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.classify_frame)
        self.timer.start(1)

    def stop_camera(self):
        if self.classifier:
            self.classifier.close()
        if self.cap.isOpened():
            self.cap.release()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.timer.stop()

    def get_options(self):
        selected_model = self.model_combobox.currentText()
        model = f"support/{selected_model}"
        max_results = 5
        score_threshold = 0.1

        base_options = python.BaseOptions(model_asset_path=model)
        options = vision.ImageClassifierOptions(base_options=base_options, running_mode=vision.RunningMode.LIVE_STREAM,
                                                max_results=max_results, score_threshold=score_threshold,
                                                result_callback=self.save_result)
        return options

    def save_result(self, result: vision.ImageClassifierResult, unused_output_image: mp.Image, timestamp_ms: int):
        if result.classifications:
            highest_prediction = max(result.classifications[0].categories, default=None, key=lambda x: x.score)
            if highest_prediction:
                prediction_text = f'Category: {highest_prediction.index}, {highest_prediction.category_name}, Score: {highest_prediction.score:.2f}'
                self.best_prediction_label.setText(prediction_text)


    def classify_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                # Run image classifier
                self.classifier.classify_async(mp_frame, time.time_ns() // 1_000_000)

                h, w, ch = frame.shape
                bytes_per_line = ch * w
                
                # Convert frame to QImage
                q_img = self.convert_frame_to_qimage(rgb_frame)
                self.image_label.setPixmap(QPixmap.fromImage(q_img))
                
        except RuntimeError as e:
            error_message = traceback.format_exc()
            self.best_prediction_label.setText(f"Error. Please choose a different model.")

    def convert_frame_to_qimage(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return q_img
    
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageClassificationGUI()
    window.show()
    sys.exit(app.exec_())


