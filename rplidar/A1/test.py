from rplidar import RPLidar

PORT_NAME = '/dev/ttyUSB0'  # Change this if your lidar uses a different port

def run():
    lidar = RPLidar(PORT_NAME)

    try:
        print("✅ RPLIDAR is running. Press Ctrl+C to stop.\n")
        for scan in lidar.iter_scans():
            for (_, angle, distance) in scan:
                print(f"Angle: {angle:.1f}°, Distance: {distance:.1f} mm")
    except KeyboardInterrupt:
        print("\n Stopped by user.")
    finally:
        lidar.stop()
        lidar.disconnect()
        print("LIDAR disconnected.")

if __name__ == '__main__':
    run()
