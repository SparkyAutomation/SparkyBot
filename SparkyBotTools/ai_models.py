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
from utils import visualize 

class ImageClassificationGUI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Image Classification")
        self.classifier = None
        self.detector = None
        self.detection_result_list = []
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_camera)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setEnabled(False)
        
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(["Image Classification", "Object Detection"])
        self.mode_combobox.currentIndexChanged.connect(self.switch_mode)
        self.current_mode = "Image Classification"     
        self.model_combobox = QComboBox()
        self.populate_model_combobox()  # Populate the combobox with tflite files
        self.best_prediction_label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.mode_combobox)
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
        
        if self.current_mode == "Image Classification":
            self.classifier = vision.ImageClassifier.create_from_options(self.get_options())
        else:
            self.detector = vision.ObjectDetector.create_from_options(self.get_options())

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(1)

    def stop_camera(self):
        if self.classifier:
            self.classifier.close()
        if self.cap.isOpened():
            self.cap.release()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.timer.stop()
        
    def switch_mode(self, index):
        mode = self.mode_combobox.currentText()
        self.current_mode = mode
        
    def get_options(self):
        selected_model = self.model_combobox.currentText()
        model = os.path.join("support", selected_model)  # Adjusted path to include 'support' folder
        max_results = 5
        score_threshold = 0.1

        base_options = python.BaseOptions(model_asset_path=model)
        if self.current_mode == "Image Classification":
            options = vision.ImageClassifierOptions(base_options=base_options, running_mode=vision.RunningMode.LIVE_STREAM,
                                                    max_results=max_results, score_threshold=score_threshold,
                                                    result_callback=self.save_result)
        else:
            options = vision.ObjectDetectorOptions(base_options=base_options, running_mode=vision.RunningMode.LIVE_STREAM,
                                                   max_results=max_results, score_threshold=score_threshold,
                                                   result_callback=self.save_result)
        return options



    def save_result(self, result, unused_output_image: mp.Image, timestamp_ms: int):
        if self.current_mode == "Image Classification":
            if result.classifications:
                highest_prediction = max(result.classifications[0].categories, default=None, key=lambda x: x.score)
                if highest_prediction:
                    prediction_text = f'Category: {highest_prediction.index}, {highest_prediction.category_name}, Score: {highest_prediction.score:.2f}'
                    if len(prediction_text) > 40:  # arbitrary length to determine if it needs to wrap
                        prediction_text = prediction_text[:40] + '\n' + prediction_text[40:]
                    self.best_prediction_label.setText(prediction_text)
        else:
            self.detection_result_list.append(result)  # Append the detection result to the list
            #print(self.detection_result_list)


    def process_frame(self):
        try:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                if self.current_mode == "Image Classification":
                    # Run image classifier
                    self.classifier.classify_async(mp_frame, time.time_ns() // 1_000_000)
                else:
                    # Run object detection using the model.
                    self.detector.detect_async(mp_frame, time.time_ns() // 1_000_000)

                    # Call visualize function to draw bounding boxes if detection results exist
                    if self.detection_result_list:
                        frame_with_bboxes = visualize(rgb_frame, self.detection_result_list[-1])
                        rgb_frame = frame_with_bboxes


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



