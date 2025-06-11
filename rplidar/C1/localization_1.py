import subprocess
import re
import numpy as np
from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1
import math
import time
import matplotlib.pyplot as plt
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

# ==== CONFIGURATION ====
ULTRA_SIMPLE_PATH = './ultra_simple'
PORT = '/dev/ttyUSB0'
BAUD = '460800'

SCAN_SIZE = 360  # One distance per degree
MAX_DISTANCE = 6000  # Maximum distance in mm for valid data

MAP_SIZE_PIXELS = 500
MAP_SIZE_METERS = 10

# ==== LIDAR PARSER ====
pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')

# ==== SLAM OBJECTS ====
lidar_model = RPLidarA1()
slam = RMHC_SLAM(lidar_model, MAP_SIZE_PIXELS, MAP_SIZE_METERS)
mapbytes = bytearray(MAP_SIZE_PIXELS * MAP_SIZE_PIXELS)
scan = [0] * SCAN_SIZE

# ==== MATPLOTLIB SETUP ====
plt.ion()
fig, ax = plt.subplots(figsize=(6, 6))

img = ax.imshow(np.zeros((MAP_SIZE_PIXELS, MAP_SIZE_PIXELS)), cmap='gray', origin='lower')
robot_pos, = ax.plot([], [], 'ro')  # Robot position (red dot)
ax.set_title("SLAM Map")

# ==== RUN LIDAR SUBPROCESS ====
proc = subprocess.Popen(
    [ULTRA_SIMPLE_PATH, '--channel', '--serial', PORT, BAUD],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

last_update = time.time()
pose_history = []

print("Starting Lidar... Press Ctrl+C to stop.")

try:
    for line in proc.stdout:
        match = pattern.search(line)
        if match:
            angle = int(float(match.group(1)))
            distance = int(float(match.group(2)))

            if 0 <= angle < SCAN_SIZE:
                scan[angle] = distance if 0 < distance < MAX_DISTANCE else 0

        # Feed a scan every ~0.2s
        if time.time() - last_update > 0.2:
            if any(scan):
                slam.update(scan)
                x_mm, y_mm, theta_deg = slam.getpos()
                print(f"Pose: x={x_mm/1000:.2f} m, y={y_mm/1000:.2f} m, θ={theta_deg:.1f}°")
                pose_history.append((x_mm, y_mm))

                # Get map and display
                slam.getmap(mapbytes)
                map_img = np.array(mapbytes).reshape((MAP_SIZE_PIXELS, MAP_SIZE_PIXELS))
                img.set_data(map_img)
                # Plot robot path
                path_x = [x / (MAP_SIZE_METERS * 1000 / MAP_SIZE_PIXELS) for x, y in pose_history]
                path_y = [y / (MAP_SIZE_METERS * 1000 / MAP_SIZE_PIXELS) for x, y in pose_history]
                robot_pos.set_data(path_x, path_y)
                ax.set_xlim(0, MAP_SIZE_PIXELS)
                ax.set_ylim(0, MAP_SIZE_PIXELS)
                plt.pause(0.001)

            scan = [0] * SCAN_SIZE  # Reset scan for next set
            last_update = time.time()

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    proc.terminate()
    proc.wait()
    plt.ioff()
    plt.show()
