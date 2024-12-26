from sparkybotio import setServoAngle, getServoAngle
import cv2
import numpy as np

# Adjust delay_time as needed for your desired frame rate
delay_time =  10

# Initialize camera
cap = cv2.VideoCapture(0)

# Function to set pitch servo angle
def set_pitch_angle(angle):
    setServoAngle(1, int(angle))

# Function to set yaw servo angle
def set_yaw_angle(angle):
    setServoAngle(2, int(angle))

# Constants for frame dimensions and servo movement range
FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
CENTER_X = FRAME_WIDTH // 2
CENTER_Y = FRAME_HEIGHT // 2
PITCH_ANGLE_RANGE = 180  # Maximum angle for pitch servo
YAW_ANGLE_RANGE = 180    # Maximum angle for yaw servo

# Initial pitch and yaw angles
pitch_angle_now = 90
yaw_angle_now = 90

set_pitch_angle(pitch_angle_now)
set_yaw_angle(yaw_angle_now)

# Filter alpha value for smoothing
alpha = 0.05
filtered_pitch_angle = pitch_angle_now
filtered_yaw_angle = yaw_angle_now

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    
    # Define lower and upper bounds for blue color in BGR
    lower_bound = np.array([0, 0, 182])  # Lower bound in BGR
    upper_bound = np.array([255, 86, 255])  # Upper bound in BGR

    # Threshold the image to get only red colors
    mask = cv2.inRange(frame, lower_bound, upper_bound)
    
    # Get contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the contour with the largest area
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Draw rectangle around the largest red area
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Calculate center of the bounding box
        cx = x + w // 2
        cy = y + h // 2
            
        # Calculate error in x and y directions from center of the frame
        error_x = cx - CENTER_X
        error_y = cy - CENTER_Y
        
        #print(error_x, error_y)
    
        # Normalize error values based on frame dimensions
        normalized_error_x = error_x / FRAME_WIDTH/2
        normalized_error_y = error_y / FRAME_HEIGHT/2
        print(normalized_error_x, normalized_error_y)
        
        # Convert normalized error values to angles for pitch and yaw servos
        pitch_angle_now = getServoAngle(1)
        yaw_angle_now = getServoAngle(2)
        pitch_angle = pitch_angle_now + normalized_error_y * PITCH_ANGLE_RANGE/2
        yaw_angle =  yaw_angle_now + normalized_error_x * YAW_ANGLE_RANGE/2

        # Apply low-pass filter to smooth angles
        filtered_pitch_angle = alpha * pitch_angle + (1 - alpha) * filtered_pitch_angle
        filtered_yaw_angle = alpha * yaw_angle + (1 - alpha) * filtered_yaw_angle
    
        # Update servo positions
        #set_pitch_angle(filtered_pitch_angle)
        #set_yaw_angle(filtered_yaw_angle)
            
    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(frame, frame, mask=mask)
    
    # Display the resulting frame
    cv2.imshow("Result", frame)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(delay_time) & 0xFF == ord('q'):
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
