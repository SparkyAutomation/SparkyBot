import os
os.environ["QT_QPA_PLATFORM"] = "xcb"  # Force X11 backend to suppress Wayland Qt warnings

import time
import numpy as np
import matplotlib.pyplot as plt
from rplidar import RPLidar, RPLidarException

# Room size in mm (for location estimation)
ROOM_WIDTH = 4500
ROOM_HEIGHT = 4000
PORT_NAME = '/dev/ttyUSB0'

def polar_to_cartesian(angle_deg, distance):
    rad = np.deg2rad(angle_deg)
    x = distance * np.cos(rad)
    y = distance * np.sin(rad)
    return x, y

def estimate_heading(angles):
    # angles in degrees, list or np.array
    if len(angles) == 0:
        return None
    # Convert to radians
    radians = np.deg2rad(angles)
    # Compute mean angle using vector sum to avoid wrap-around issues
    sin_sum = np.sum(np.sin(radians))
    cos_sum = np.sum(np.cos(radians))
    mean_angle_rad = np.arctan2(sin_sum, cos_sum)
    mean_angle_deg = np.rad2deg(mean_angle_rad)
    if mean_angle_deg < 0:
        mean_angle_deg += 360
    return mean_angle_deg

def estimate_location(xs, ys):
    if len(xs) == 0 or len(ys) == 0:
        return None, None
    min_x, max_x = np.min(xs), np.max(xs)
    min_y, max_y = np.min(ys), np.max(ys)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    est_x = ROOM_WIDTH / 2 - center_x
    est_y = ROOM_HEIGHT / 2 - center_y
    return est_x, est_y

def reset_lidar(lidar):
    try:
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()
    except:
        pass
    time.sleep(2)
    new_lidar = RPLidar(PORT_NAME)
    new_lidar.start_motor()
    time.sleep(2)
    return new_lidar

def main():
    lidar = RPLidar(PORT_NAME)
    time.sleep(1)
    print(f"Initializing LIDAR...")
    try:
        lidar.connect()
        lidar.start_motor()
        time.sleep(2)
    except RPLidarException as e:
        print(f"Failed to initialize LIDAR: {e}")
        return

    plt.ion()
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location('N')   # 0° at top
    ax.set_theta_direction(-1)        # clockwise rotation
    ax.set_rlim(0, 4000)              # max distance 4000 mm
    scan_plot, = ax.plot([], [], 'ro', markersize=2)
    loc_text = ax.text(0.5, 1.05, '', transform=ax.transAxes, ha='center')
    heading_text = ax.text(0.5, 1.1, '', transform=ax.transAxes, ha='center')

    last_heading = None  # For smoothing heading jumps

    try:
        print("Starting... Ctrl+C to stop.")
        while True:
            try:
                for scan in lidar.iter_scans(max_buf_meas=500):
                    angles_deg = []
                    distances = []
                    xs = []
                    ys = []

                    for (_, angle, distance) in scan:
                        if distance == 0 or distance > 4000:
                            continue
                        angles_deg.append(angle)
                        distances.append(distance)
                        x, y = polar_to_cartesian(angle, distance)
                        xs.append(x)
                        ys.append(y)

                    if len(angles_deg) == 0:
                        continue

                    # Update polar plot
                    angles_rad = np.radians(angles_deg)
                    scan_plot.set_data(angles_rad, distances)

                    # Estimate heading, smooth sudden jumps
                    heading = estimate_heading(angles_deg)
                    if last_heading is not None:
                        diff = heading - last_heading
                        if diff > 180:
                            heading -= 360
                        elif diff < -180:
                            heading += 360
                        heading = (last_heading * 0.8) + (heading * 0.2)  # smoothing
                        heading = heading % 360  # Wrap into [0, 360)
                    last_heading = heading

                    # Estimate location (x,y)
                    est_x, est_y = estimate_location(xs, ys)

                    if est_x is not None and est_y is not None:
                        loc_text.set_text(f"Estimated Location: ({est_x:.0f}, {est_y:.0f}) mm")
                    else:
                        loc_text.set_text("Estimated Location: Unknown")

                    if heading is not None:
                        heading_text.set_text(f"Estimated Heading: {heading:.1f}°")
                    else:
                        heading_text.set_text("Estimated Heading: Unknown")

                    fig.canvas.draw()
                    fig.canvas.flush_events()

            except RPLidarException as e:
                print(f"❌ LIDAR error: {e}. Resetting LIDAR...")
                lidar = reset_lidar(lidar)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")

    finally:
        try:
            lidar.stop()
            lidar.stop_motor()
            lidar.disconnect()
        except:
            pass
        plt.ioff()
        plt.show()
        print("✅ Shutdown complete.")

if __name__ == '__main__':
    main()