import os
import re
import time
import math
import numpy as np
import subprocess
from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1

def run_slam(show_map=False, verbose=True, update_rate=0.2, loop_distance_thresh=0.8):
    if show_map:
        import matplotlib.pyplot as plt
        plt.ion()
        fig, ax = plt.subplots(figsize=(6, 6))
        img = ax.imshow(np.zeros((500, 500)), cmap='gray', origin='lower')
        robot_pos, = ax.plot([], [], 'ro')
        ax.set_xlim(0, 500)
        ax.set_ylim(0, 500)

    os.environ["QT_QPA_PLATFORM"] = "xcb"
    PORT, BAUD = '/dev/ttyUSB0', '460800'
    ULTRA_SIMPLE_PATH = './ultra_simple'
    MAP_PIXELS, MAP_METERS = 500, 10
    POSE_LOG, OPT_POSE_LOG, G2O_EXEC = 'graph.g2o', 'graph_optimized.g2o', 'g2o'

    slam = RMHC_SLAM(RPLidarA1(), MAP_PIXELS, MAP_METERS)
    scan = [0] * 360
    pose_history = []
    origin_estimates = []

    proc = subprocess.Popen(
        [ULTRA_SIMPLE_PATH, '--channel', '--serial', PORT, BAUD],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if verbose:
        print("Lidar started. Ctrl+C to stop.")

    pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')
    skip_first, origin_set, pose_locked = True, False, False
    prev_x = prev_y = prev_theta = None
    last_update = time.time()

    try:
        for line in proc.stdout:
            match = pattern.search(line)
            if match:
                angle = int(float(match[1]))
                dist = int(float(match[2]))
                if 0 <= angle < 360:
                    scan[angle] = dist if 0 < dist < 6000 else 0

            if time.time() - last_update > update_rate and any(scan):
                slam.update(scan)
                x, y, theta = slam.getpos()

                if not origin_set:
                    if skip_first:
                        skip_first = False
                    else:
                        origin_estimates.append((x, y, theta))
                        if len(origin_estimates) == 5:
                            ox, oy, ot = map(lambda l: sum(l) / 5, zip(*origin_estimates))
                            origin_x, origin_y, origin_theta = ox, oy, ot + 90
                            origin_set = True
                            if verbose:
                                print("Calibration done")
                    scan = [0] * 360
                    last_update = time.time()
                    continue

                rx = x - origin_x
                ry = y - origin_y
                rtheta = ((theta - origin_theta + 360) % 360) - 180
                rad = math.radians(rtheta)

                if prev_x is not None:
                    dx = abs(rx - prev_x)
                    dy = abs(ry - prev_y)
                    dtheta = abs(rtheta - math.degrees(prev_theta))
                    if pose_locked and (dx > 500 or dy > 500 or dtheta > 60):
                        if verbose:
                            print("Jump detected. Skipping.")
                        scan = [0] * 360
                        last_update = time.time()
                        continue
                else:
                    pose_locked = True

                prev_x, prev_y, prev_theta = rx, ry, rad
                if verbose:
                    print(f"Lidar pose: ({rx / 1000:.2f}m, {ry / 1000:.2f}m, {rtheta:.1f}°)")
                pose_history.append((rx, ry, rad))

                if show_map:
                    px = [x / (MAP_METERS * 1000 / MAP_PIXELS) for x, _, _ in pose_history]
                    py = [y / (MAP_METERS * 1000 / MAP_PIXELS) for _, y, _ in pose_history]
                    robot_pos.set_data(px, py)
                    plt.pause(0.001)

                scan = [0] * 360
                last_update = time.time()

    except KeyboardInterrupt:
        if verbose:
            print("Stopped.")
    finally:
        proc.terminate()
        proc.wait()
        if show_map:
            plt.ioff()
            plt.show()

    if verbose:
        print(f"Total poses: {len(pose_history)}")
        print("Writing graph file...")

    with open(POSE_LOG, 'w') as f:
        for i, (x, y, th) in enumerate(pose_history):
            f.write(f"VERTEX_SE2 {i} {x / 1000:.4f} {y / 1000:.4f} {th:.6f}\n")

        for i in range(1, len(pose_history)):
            dx = (pose_history[i][0] - pose_history[i - 1][0]) / 1000.0
            dy = (pose_history[i][1] - pose_history[i - 1][1]) / 1000.0
            dth = pose_history[i][2] - pose_history[i - 1][2]
            f.write(f"EDGE_SE2 {i - 1} {i} {dx:.4f} {dy:.4f} {dth:.6f} 1000 0 0 1000 0 1000\n")

        # Robust loop closure logic with FULL debug (log distances to an explicit path)
        loop_count = 0
        min_pose_gap = 5
        log_path = '/home/bo/Desktop/rplidar/C1/loop_distances.log'
        with open(log_path, 'w') as flog:
            flog.write('i,j,dist\n')
            for i, (x1, y1, th1) in enumerate(pose_history[:-min_pose_gap]):
                for j in range(i + min_pose_gap, len(pose_history)):
                    x2, y2, th2 = pose_history[j]
                    dist = math.hypot(x2 - x1, y2 - y1) / 1000.0
                    flog.write(f'{i},{j},{dist:.4f}\n')
                    if verbose:
                        print(f"Testing loop i={i} j={j} dist={dist:.3f}")
                    if dist < loop_distance_thresh:
                        dx = (x2 - x1) / 1000.0
                        dy = (y2 - y1) / 1000.0
                        dth = th2 - th1
                        f.write(f"EDGE_SE2 {i} {j} {dx:.4f} {dy:.4f} {dth:.6f} 5000 0 0 5000 0 5000\n")
                        loop_count += 1
                        if verbose:
                            print(f"🔁 Loop closure edge added: {i} ↔ {j} | Δx={dx:.2f}m, Δy={dy:.2f}m, Δθ={math.degrees(dth):.1f}°")
        f.write("FIX 0\n")
        if verbose:
            print(f"🔗 Total loop closures added: {loop_count}")
        print(f"Loop distances log written to: {log_path}")

    if verbose:
        print(f"Optimizing {POSE_LOG}...")
    subprocess.run([G2O_EXEC, "-o", OPT_POSE_LOG, POSE_LOG])
    if verbose:
        print(f"✅ Saved optimized graph to {OPT_POSE_LOG}")

    if show_map:
        with open(OPT_POSE_LOG, "r") as f:
            opt = [(float(x), float(y)) for l in f if l.startswith("VERTEX_SE2")
                   for _, _, x, y, _ in [l.strip().split()]]
        opt_x = [x * MAP_PIXELS / MAP_METERS for x, _ in opt]
        opt_y = [y * MAP_PIXELS / MAP_METERS for _, y in opt]

        fig2, ax2 = plt.subplots(figsize=(6, 6))
        ax2.plot(opt_x, opt_y, 'g-', label='Optimized Path')
        ax2.set_title("Optimized Path with Loop Closures")
        ax2.set_xlim(0, MAP_PIXELS)
        ax2.set_ylim(0, MAP_PIXELS)
        ax2.set_aspect('equal')
        ax2.legend()
        plt.show()

if __name__ == "__main__":
    run_slam(show_map=False, verbose=True)
