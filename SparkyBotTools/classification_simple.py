import cv2
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def run(model: str, max_results: int, score_threshold: float):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def save_result(result: vision.ImageClassifierResult, unused_output_image: mp.Image, timestamp_ms: int):
        if result.classifications:
            highest_prediction = max(result.classifications[0].categories, default=None, key=lambda x: x.score)
            if highest_prediction:
                score = "{:.2f}".format(highest_prediction.score)
                print(f'Prediction: {highest_prediction.category_name} ({score})')

    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ImageClassifierOptions(base_options=base_options,
                                            running_mode=vision.RunningMode.LIVE_STREAM,
                                            max_results=max_results,
                                            score_threshold=score_threshold,
                                            result_callback=save_result)
    classifier = vision.ImageClassifier.create_from_options(options)

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print('ERROR: Unable to read from webcam.')
            break

        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        classifier.classify_async(mp_image, timestamp_ms=int(time.time() * 1000))

        cv2.imshow('image_classification', image)

        if cv2.waitKey(1) == 27:
            break

    classifier.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run("support/cats_dogs_mediapipe.tflite", 1, 0.1)
