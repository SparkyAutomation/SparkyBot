import cv2
import numpy as np

# Initialize webcam
cap = cv2.VideoCapture(0)

while True:
    # Read frame from webcam
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Thresholding to segment black lines
    _, thresholded = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY)
    
    # Detect edges using Canny edge detection
    edges = cv2.Canny(thresholded, 70, 150)
    
    # Apply dilation to thicken the edges
    kernel = np.ones((8,8), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Find coordinates of white pixels
    white_pixels = np.argwhere(dilated_edges == 255)
    
    # Calculate centroid
    if len(white_pixels) > 0:
        centroid = np.mean(white_pixels, axis=0, dtype=int)
        centroid_x, centroid_y = centroid[1], centroid[0]  # Swap x and y due to OpenCV coordinate convention
        
        # Draw centroid on the frame
        cv2.circle(frame, (centroid_x, centroid_y), 10, (255, 0, 0), -1)
    
    
    # Concatenate color frame and binary dilated_edges side by side
    combined_image = np.hstack((frame, cv2.cvtColor(dilated_edges, cv2.COLOR_GRAY2BGR)))
    
    # Display the stacked images
    cv2.imshow('Color and Binary Images', combined_image)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
