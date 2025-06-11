import subprocess
import re
import matplotlib.pyplot as plt
import numpy as np
import cv2
import math
import time
import logging
import os
from typing import Optional, Tuple
from sklearn.cluster import KMeans

# Configure logging for debugging and performance monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration (adjust these parameters as needed)
CONFIG = {
    'ULTRA_SIMPLE_PATH': './ultra_simple',  # Path to LIDAR executable
    'PORT': '/dev/ttyUSB0',  # Serial port for LIDAR
    'BAUD': '460800',  # Baud rate for serial communication
    'RECT_WIDTH': 3600,  # Rectangle width in mm
    'RECT_HEIGHT': 4000,  # Rectangle height in mm
    'MAX_DISTANCE': 6000,  # Max valid distance in mm
    'UPDATE_INTERVAL': 0.1,  # Seconds between plot updates
    'MIN_POINTS': 20,  # Min points for rectangle fitting
    'ANGLE_SMOOTHING_FACTOR': 0.7,  # Weight for angle smoothing (0-1, higher = smoother)
    'KMEANS_POINTS': 100,  # Max points for clustering (limits computation)
    'OUTLIER_THRESHOLD': 2.0,  # IQR multiplier for outlier removal
    'ALIGNMENT_THRESHOLD': 1500,  # Max avg distance (mm) for rectangle validation
    'MAX_POINTS': 1000,  # Max points to process per update (for efficiency)
}

def check_dependencies() -> bool:
    """Check if required Python packages are installed."""
    required = ['numpy', 'matplotlib', 'cv2', 'sklearn']
    for module in required:
        try:
            __import__(module)
        except ImportError:
            logger.error(f"Missing package: {module}. Install with 'pip install {module}'")
            return False
    return True

def validate_environment() -> bool:
    """Validate that required paths and permissions exist."""
    if not check_dependencies():
        return False
    if not os.path.exists(CONFIG['ULTRA_SIMPLE_PATH']):
        logger.error(f"LIDAR executable not found at {CONFIG['ULTRA_SIMPLE_PATH']}")
        return False
    if not os.access(CONFIG['ULTRA_SIMPLE_PATH'], os.X_OK):
        logger.error(f"LIDAR executable at {CONFIG['ULTRA_SIMPLE_PATH']} is not executable")
        return False
    if not os.path.exists(CONFIG['PORT']):
        logger.error(f"Serial port {CONFIG['PORT']} not found")
        return False
    return True

def start_lidar_process() -> Optional[subprocess.Popen]:
    """Start the LIDAR subprocess with error handling."""
    try:
        return subprocess.Popen(
            [CONFIG['ULTRA_SIMPLE_PATH'], '--channel', '--serial', CONFIG['PORT'], CONFIG['BAUD']],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to start LIDAR process: {e}")
        return None

def remove_outliers(points: np.ndarray) -> np.ndarray:
    """Remove outliers using IQR method to clean point cloud."""
    if len(points) < CONFIG['MIN_POINTS']:
        return points
    
    centroid = np.mean(points, axis=0)
    distances = np.linalg.norm(points - centroid, axis=1)
    q25, q75 = np.percentile(distances, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - CONFIG['OUTLIER_THRESHOLD'] * iqr
    upper_bound = q75 + CONFIG['OUTLIER_THRESHOLD'] * iqr
    mask = (distances >= lower_bound) & (distances <= upper_bound)
    return points[mask]

def get_extent_angle(points: np.ndarray) -> float:
    """Estimate orientation based on point cloud extent."""
    if len(points) < CONFIG['MIN_POINTS']:
        return 0.0
    x_range = np.ptp(points[:, 0])
    y_range = np.ptp(points[:, 1])
    return 0.0 if x_range > y_range else 90.0

def fit_fixed_rectangle(points: np.ndarray, 
                       prev_angle: Optional[float] = None) -> Tuple[Optional[np.ndarray], Optional[float]]:
    """Fit a fixed-size rectangle (3600mm x 4000mm) to the point cloud."""
    start_time = time.time()
    if len(points) < CONFIG['MIN_POINTS']:
        logger.debug(f"Insufficient points ({len(points)} < {CONFIG['MIN_POINTS']})")
        return None, prev_angle

    try:
        # Subsample points for efficiency
        if len(points) > CONFIG['KMEANS_POINTS']:
            indices = np.random.choice(len(points), CONFIG['KMEANS_POINTS'], replace=False)
            points = points[indices]

        # Remove outliers
        points = remove_outliers(points)
        if len(points) < CONFIG['MIN_POINTS']:
            logger.debug(f"Too few points after outlier removal ({len(points)})")
            return None, prev_angle

        # Cluster points using K-means (faster than DBSCAN)
        kmeans = KMeans(n_clusters=1, n_init=1, random_state=0).fit(points)
        cluster_points = points  # K-means returns centroid, use all points for fitting

        # Try fitting minimum area rectangle
        try:
            rect = cv2.minAreaRect(cluster_points)
            center, size, angle = rect

            # Correct orientation using point cloud extent
            extent_angle = get_extent_angle(cluster_points)
            current_width, current_height = size
            if abs(current_width - CONFIG['RECT_WIDTH']) > abs(current_height - CONFIG['RECT_WIDTH']):
                angle = angle + 90 if angle < 0 else angle - 90
                logger.debug(f"Orientation corrected: angle from {angle:.2f} to {angle+90:.2f}")

            # Smooth angle
            if prev_angle is not None:
                angle = CONFIG['ANGLE_SMOOTHING_FACTOR'] * angle + (1 - CONFIG['ANGLE_SMOOTHING_FACTOR']) * prev_angle
            else:
                prev_angle = angle

            # Create fixed-size rectangle
            fixed_rect = (center, (CONFIG['RECT_WIDTH'], CONFIG['RECT_HEIGHT']), angle)
            box = cv2.boxPoints(fixed_rect)
            box = np.append(box, [box[0]], axis=0)

            # Validate alignment
            distances = np.array([np.min(np.linalg.norm(cluster_points - p, axis=1)) for p in box[:-1]])
            mean_distance = np.mean(distances)
            if mean_distance > CONFIG['ALIGNMENT_THRESHOLD']:
                logger.debug(f"Poor alignment (avg distance: {mean_distance:.2f}mm), trying fallback")
                raise ValueError("Poor alignment")

            logger.debug(f"Rectangle fitted: center={center}, angle={angle:.2f}, avg_distance={mean_distance:.2f}mm, time={time.time()-start_time:.3f}s")
            return box, angle

        except (cv2.error, ValueError):
            # Fallback: Center rectangle at centroid with extent-based angle
            logger.debug("Falling back to centroid-based rectangle")
            center = np.mean(cluster_points, axis=0)
            angle = get_extent_angle(cluster_points) if prev_angle is None else prev_angle
            fixed_rect = (center, (CONFIG['RECT_WIDTH'], CONFIG['RECT_HEIGHT']), angle)
            box = cv2.boxPoints(fixed_rect)
            box = np.append(box, [box[0]], axis=0)
            logger.debug(f"Fallback rectangle: center={center}, angle={angle:.2f}, time={time.time()-start_time:.3f}s")
            return box, angle

    except Exception as e:
        logger.error(f"Rectangle fitting failed: {e}")
        return None, prev_angle

def main():
    """Run LIDAR visualization with real-time plotting."""
    if not validate_environment():
        return

    # Initialize plot
    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal')
    ax.set_xlim(-CONFIG['MAX_DISTANCE'], CONFIG['MAX_DISTANCE'])
    ax.set_ylim(-CONFIG['MAX_DISTANCE'], CONFIG['MAX_DISTANCE'])
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.grid(True)
    scan_plot, = ax.plot([], [], 'ro', markersize=2, label='LIDAR Points')
    rect_plot, = ax.plot([], [], 'g-', linewidth=2, label='Fitted Rectangle')
    ax.legend()

    proc = start_lidar_process()
    if not proc:
        return

    # Pre-allocate arrays for efficiency
    points = np.zeros((CONFIG['MAX_POINTS'], 2), dtype=np.float32)
    point_count = 0
    last_update = time.time()
    prev_angle: Optional[float] = None

    logger.info("Starting LIDAR visualization. Press Ctrl+C to stop.")
    pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')

    try:
        while True:
            try:
                line = proc.stdout.readline().strip()
                if not line and proc.poll() is not None:
                    logger.error("LIDAR process terminated unexpectedly")
                    break

                match = pattern.search(line)
                if match:
                    try:
                        angle = float(match.group(1))
                        distance = float(match.group(2))
                        if 0 < distance < CONFIG['MAX_DISTANCE'] and point_count < CONFIG['MAX_POINTS']:
                            theta = math.radians(angle)
                            points[point_count] = [distance * math.cos(theta), distance * math.sin(theta)]
                            point_count += 1
                    except ValueError as e:
                        logger.warning(f"Invalid data format: {line}, error: {e}")
                        continue

                # Update plot periodically
                if time.time() - last_update > CONFIG['UPDATE_INTERVAL'] and point_count > 0:
                    start_time = time.time()
                    active_points = points[:point_count]
                    scan_plot.set_data(active_points[:, 0], active_points[:, 1])

                    box, prev_angle = fit_fixed_rectangle(active_points, prev_angle=prev_angle)
                    rect_plot.set_data(box[:, 0], box[:, 1]) if box is not None else rect_plot.set_data([], [])

                    try:
                        fig.canvas.draw_idle()
                        fig.canvas.flush_events()
                    except Exception as e:
                        logger.error(f"Plotting error: {e}")

                    point_count = 0  # Reset point count
                    logger.debug(f"Plot update time: {time.time()-start_time:.3f}s")
                    last_update = time.time()

            except subprocess.SubprocessError as e:
                logger.error(f"Subprocess error: {e}")
                break

    except KeyboardInterrupt:
        logger.info("Visualization stopped by user")
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("LIDAR process did not terminate gracefully, forcing kill")
                proc.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")

        plt.ioff()
        try:
            plt.show()
        except Exception as e:
            logger.error(f"Error displaying final plot: {e}")
        logger.info("LIDAR visualization terminated")

if __name__ == "__main__":
    main()

