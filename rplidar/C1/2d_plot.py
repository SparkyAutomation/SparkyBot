import subprocess
import re
import matplotlib.pyplot as plt
import numpy as np
import math
import time

# Path to ultra_simple binary and serial port config
ULTRA_SIMPLE_PATH = './ultra_simple'
PORT = '/dev/ttyUSB0'
BAUD = '460800'

# Regex to match lines like: "theta: 123.45 Dist: 456.78 Q: 23"
pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')

# Start ultra_simple as subprocess
proc = subprocess.Popen(
    [ULTRA_SIMPLE_PATH, '--channel', '--serial', PORT, BAUD],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Setup matplotlib polar plot
plt.ion()
fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot(111, polar=True)
scan_plot, = ax.plot([], [], 'ro', markersize=2)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_rlim(0, 6000)

angles = []
distances = []
last_update = time.time()

print("📡 Visualizing LIDAR data (polar plot). Close the plot or Ctrl+C to stop.")

try:
    for line in proc.stdout:
        match = pattern.search(line)
        if match:
            angle = float(match.group(1))
            distance = float(match.group(2))

            if 0 < distance < 6000: # in mm
                angles.append(math.radians(angle))
                distances.append(distance)

        # Update every 200 ms
        if time.time() - last_update > 0.1 and angles:
            scan_plot.set_data(angles, distances)
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            angles.clear()
            distances.clear()
            last_update = time.time()

except KeyboardInterrupt:
    print("🛑 Stopped by user.")
finally:
    proc.terminate()
    proc.wait()
    plt.ioff()
    plt.show()
    print("✅ LIDAR process terminated.")
