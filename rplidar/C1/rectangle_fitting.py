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

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LIDAR")

# Configuration
CONFIG = {
    'ULTRA_SIMPLE_PATH': './ultra_simple',
    'PORT': '/dev/ttyUSB0',
    'BAUD': '460800',
    'RECT_WIDTH': 3600, # 3600
    'RECT_HEIGHT': 4200, # 4200
    'MAX_DISTANCE': 6000,
    'UPDATE_INTERVAL': 0.1,
    'MIN_POINTS': 20,
    'ANGLE_SMOOTHING_FACTOR': 0.7,
    'KMEANS_POINTS': 100,
    'OUTLIER_THRESHOLD': 2.0,
    'MAX_POINTS': 1000,
}

# Utility functions
def validate_environment() -> bool:
    return os.path.exists(CONFIG['ULTRA_SIMPLE_PATH']) and \
           os.access(CONFIG['ULTRA_SIMPLE_PATH'], os.X_OK) and \
           os.path.exists(CONFIG['PORT'])

def start_lidar_process() -> Optional[subprocess.Popen]:
    try:
        return subprocess.Popen(
            [CONFIG['ULTRA_SIMPLE_PATH'], '--channel', '--serial', CONFIG['PORT'], CONFIG['BAUD']],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to start LIDAR process: {e}")
        return None

def remove_outliers(points: np.ndarray) -> np.ndarray:
    if len(points) < CONFIG['MIN_POINTS']:
        return points
    centroid = np.mean(points, axis=0)
    dists = np.linalg.norm(points - centroid, axis=1)
    q25, q75 = np.percentile(dists, [25, 75])
    iqr = q75 - q25
    return points[(dists >= q25 - CONFIG['OUTLIER_THRESHOLD'] * iqr) &
                  (dists <= q75 + CONFIG['OUTLIER_THRESHOLD'] * iqr)]

def angle_wrap(angle: float) -> float:
    return (angle + 180) % 360 - 180

def smooth_angle(prev_angle: float, new_angle: float, alpha: float) -> float:
    delta = angle_wrap(new_angle - prev_angle)
    return angle_wrap(prev_angle + alpha * delta)

def fit_fixed_rectangle(points: np.ndarray,
                        prev_angle: Optional[float]) -> Tuple[Optional[np.ndarray], Optional[float], Optional[Tuple[float, float]]]:
    if len(points) < CONFIG['MIN_POINTS']:
        return None, prev_angle, None
    try:
        if len(points) > CONFIG['KMEANS_POINTS']:
            points = points[np.random.choice(len(points), CONFIG['KMEANS_POINTS'], replace=False)]
        points = remove_outliers(points)
        if len(points) < CONFIG['MIN_POINTS']:
            return None, prev_angle, None

        rect = cv2.minAreaRect(points)
        center, (w, h), raw_angle = rect

        # Always use the longer side as the heading reference
        if h > w:
            angle = raw_angle
        else:
            angle = raw_angle + 90

        # Handle 180-degree ambiguity: choose the angle closest to the previous angle
        angle = angle_wrap(angle)
        angle_alt = angle_wrap(angle + 180)
        if prev_angle is not None:
            if abs(angle_wrap(angle - prev_angle)) > abs(angle_wrap(angle_alt - prev_angle)):
                angle = angle_alt
            angle = smooth_angle(prev_angle, angle, CONFIG['ANGLE_SMOOTHING_FACTOR'])
        else:
            angle = angle_wrap(angle)

        fixed_rect = (center, (CONFIG['RECT_WIDTH'], CONFIG['RECT_HEIGHT']), angle)
        box = cv2.boxPoints(fixed_rect)
        box = np.append(box, [box[0]], axis=0)
        return box, angle, tuple(center)
    except Exception as e:
        logger.error(f"Rectangle fitting failed: {e}")
        return None, prev_angle, None

def draw_heading_arrow(ax, center: Tuple[float, float], angle_deg: float, length: float = 500):
    angle_rad = math.radians(angle_deg)
    dx = length * math.cos(angle_rad)
    dy = length * math.sin(angle_rad)
    end = (center[0] + dx, center[1] + dy)

    # Remove existing LIDAR heading arrow
    for artist in ax.lines:
        if hasattr(artist, "_is_lidar_heading") and artist._is_lidar_heading:
            artist.remove()

    arrow_line, = ax.plot([center[0], end[0]], [center[1], end[1]], 'c-', linewidth=2)
    arrow_line._is_lidar_heading = True
    return arrow_line

def update_heading_text(ax, text_obj, angle: float):
    text = f"Heading: {angle:.1f}°"
    if text_obj is None:
        return ax.text(0.05, 0.95, text, transform=ax.transAxes,
                       fontsize=12, color='blue', verticalalignment='top',
                       bbox=dict(facecolor='white', alpha=0.7))
    text_obj.set_text(text)
    return text_obj

def update_lidar_text(ax, text_obj, pos: Tuple[float, float]):
    text = f"LIDAR Pos (rel. to bottom-left): ({pos[0]:.1f}, {pos[1]:.1f}) mm"
    if text_obj is None:
        return ax.text(0.05, 0.90, text, transform=ax.transAxes,
                       fontsize=12, color='purple', verticalalignment='top',
                       bbox=dict(facecolor='white', alpha=0.7))
    text_obj.set_text(text)
    return text_obj

def main():
    if not validate_environment():
        logger.error("Environment validation failed.")
        return

    proc = start_lidar_process()
    if not proc:
        return

    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-CONFIG['MAX_DISTANCE'], CONFIG['MAX_DISTANCE'])
    ax.set_ylim(-CONFIG['MAX_DISTANCE'], CONFIG['MAX_DISTANCE'])
    ax.set_aspect('equal')
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True)

    scan_plot, = ax.plot([], [], 'ro', markersize=2, label='LIDAR Points')
    rect_plot, = ax.plot([], [], 'g-', linewidth=2, label='Fitted Rectangle')
    lidar_plot, = ax.plot([], [], 'mo', markersize=8, label='LIDAR Position')
    heading_text = None
    lidar_text = None
    ax.legend()

    pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')
    points = np.zeros((CONFIG['MAX_POINTS'], 2), dtype=np.float32)
    point_count = 0
    last_update = time.time()
    prev_angle = 0.0

    logger.info("📡 Starting LIDAR visualization...")

    try:
        while True:
            line = proc.stdout.readline().strip()
            if not line and proc.poll() is not None:
                logger.error("LIDAR process terminated unexpectedly.")
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
                except ValueError:
                    continue

            if time.time() - last_update > CONFIG['UPDATE_INTERVAL'] and point_count > 0:
                active = points[:point_count]
                box, prev_angle, center = fit_fixed_rectangle(active, prev_angle)
                
                if box is not None and center is not None:
                    # Translate coordinates so left bottom corner (box[0]) is at (0, 0)
                    left_bottom = box[0]
                    translated_points = active - left_bottom
                    translated_box = box - left_bottom
                    translated_center = (center[0] - left_bottom[0], center[1] - left_bottom[1])
                    lidar_rel_pos = (-left_bottom[0], -left_bottom[1])

                    # Update Matplotlib plot
                    scan_plot.set_data(translated_points[:, 0], translated_points[:, 1])
                    rect_plot.set_data(translated_box[:, 0], translated_box[:, 1])
                    lidar_plot.set_data([lidar_rel_pos[0]], [lidar_rel_pos[1]])
                    draw_heading_arrow(ax, lidar_rel_pos, prev_angle, length=500)  # LIDAR heading only
                    heading_text = update_heading_text(ax, heading_text, prev_angle)
                    lidar_text = update_lidar_text(ax, lidar_text, lidar_rel_pos)

                    # Log LIDAR position
                    # logger.info(f"LIDAR position relative to left bottom corner (0, 0): {lidar_rel_pos}")
                else:
                    scan_plot.set_data([], [])
                    rect_plot.set_data([], [])
                    lidar_plot.set_data([], [])
                    if lidar_text is not None:
                        lidar_text.set_text("")

                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                point_count = 0
                last_update = time.time()

    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user.")
    finally:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        plt.ioff()
        plt.show()
        logger.info("✅ Visualization complete.")

if __name__ == "__main__":
    main()
