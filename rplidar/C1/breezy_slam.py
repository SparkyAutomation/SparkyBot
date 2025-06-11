import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import subprocess
import re
import numpy as np
from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1
import matplotlib.pyplot as plt
from collections import deque

ULTRA_SIMPLE_PATH = './ultra_simple'
PORT = '/dev/ttyUSB0'
BAUD = '460800'

SCAN_SIZE = 360
MAX_DISTANCE = 6000
MAP_SIZE_PIXELS = 500
MAP_SIZE_METERS = 6
MAX_POINTS = 5000
MIN_SCAN_VALID = 200  # Tune as needed

pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')

lidar_model = RPLidarA1()
slam = RMHC_SLAM(lidar_model, MAP_SIZE_PIXELS, MAP_SIZE_METERS)
mapbytes = bytearray(MAP_SIZE_PIXELS * MAP_SIZE_PIXELS)
scan = [0] * SCAN_SIZE

plt.ion()
fig, ax = plt.subplots(figsize=(6, 6))
img = ax.imshow(np.zeros((MAP_SIZE_PIXELS, MAP_SIZE_PIXELS)), cmap='gray', origin='lower')
robot_pos, = ax.plot([], [], 'ro')
ax.set_title("SLAM Map")
ax.set_aspect('equal')

proc = subprocess.Popen(
    [ULTRA_SIMPLE_PATH, '--channel', '--serial', PORT, BAUD],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

pose_history = deque(maxlen=MAX_POINTS)
origin = None
unique_angle_set = set()
print("Starting Lidar... Press Ctrl+C to stop.")

try:
    for line in proc.stdout:
        match = pattern.search(line)
        if match:
            try:
                angle = int(float(match.group(1)))
                distance = int(float(match.group(2)))
            except ValueError:
                continue
            if 0 <= angle < SCAN_SIZE:
                scan[angle] = distance if 0 < distance < MAX_DISTANCE else 0
                unique_angle_set.add(angle)
        # Only update after enough unique angles
        if len(unique_angle_set) >= MIN_SCAN_VALID:
            #print("Scan snippet (first 20):", scan[:20])
            slam.update(scan)
            x_mm, y_mm, theta_deg = slam.getpos()

            if origin is None:
                origin = (x_mm, y_mm, theta_deg)
                print("Origin set to: x=%.2f m, y=%.2f m, θ=%.1f°" %
                      (x_mm/1000, y_mm/1000, theta_deg))

            rel_x_mm = x_mm - origin[0]
            rel_y_mm = y_mm - origin[1]
            rel_theta_deg = (theta_deg - origin[2] + 180) % 360 - 180

            print(f"Pose: x={rel_x_mm/1000:.2f} m, y={rel_y_mm/1000:.2f} m, θ={rel_theta_deg:.1f}°")
            pose_history.append((rel_x_mm, rel_y_mm))

            slam.getmap(mapbytes)
            map_img = np.array(mapbytes).reshape((MAP_SIZE_PIXELS, MAP_SIZE_PIXELS))
            img.set_data(map_img)
            path_x = [x / (MAP_SIZE_METERS * 1000 / MAP_SIZE_PIXELS) for x, y in pose_history]
            path_y = [y / (MAP_SIZE_METERS * 1000 / MAP_SIZE_PIXELS) for x, y in pose_history]
            robot_pos.set_data(path_x, path_y)
            ax.set_xlim(0, MAP_SIZE_PIXELS)
            ax.set_ylim(0, MAP_SIZE_PIXELS)
            plt.pause(0.001)

            scan = [0] * SCAN_SIZE
            unique_angle_set = set()
except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    proc.terminate()
    proc.wait()
    plt.ioff()
    plt.show()

