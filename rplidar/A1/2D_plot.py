import matplotlib.pyplot as plt
import numpy as np
from rplidar import RPLidar

PORT_NAME = '/dev/ttyUSB0'  # Update if needed

lidar = RPLidar(PORT_NAME)

# Setup the plot
plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111, polar=True)
scan_plot, = ax.plot([], [], 'ro', markersize=2)
ax.set_theta_zero_location('N')      # 0° at top
ax.set_theta_direction(-1)           # Clockwise
ax.set_rlim(0, 4000)                 # 0 to 4 meters

def update_plot(scan):
    angles = np.radians([angle for (_, angle, _) in scan])
    distances = [dist for (_, _, dist) in scan]
    scan_plot.set_data(angles, distances)
    fig.canvas.draw()
    fig.canvas.flush_events()

try:
    print("📡 RPLIDAR is scanning... Close the window or Ctrl+C to stop.")
    for scan in lidar.iter_scans():
        update_plot(scan)
except KeyboardInterrupt:
    print("🛑 Stopped by user.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    lidar.stop()
    lidar.disconnect()
    plt.ioff()
    plt.show()
