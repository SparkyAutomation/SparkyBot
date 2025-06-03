import math
import sys
import os

# Get the absolute path of the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from sparkybotio import setMotor


def angle_wrap(a):
    """
    Wrap angle a to [-pi, pi]
    """
    return math.atan2(math.sin(a), math.cos(a))

def set_left_motor(left_speed):
    setMotor(1, -left_speed)
    setMotor(3, -left_speed)
    
def set_left_motor(right_speed):
    setMotor(2, -right_speed)
    setMotor(4, -right_speed)
    

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose, set_hw_motor):
    """
    Point-to-point control for differential drive robot.
    - x, y, heading: current pose
    - waypoint: dict with 'x' and 'y' (target position)
    - dt: timestep (s)
    - is_sim: True for simulation
    - get_hw_pose: function returning (x, y, heading)
    - set_hw_motor: function accepting (left_speed, right_speed)
    Returns: x_new, y_new, heading_new, done, debug
    """

    # --- Compute control errors ---
    dx, dy = waypoint['x'] - x, waypoint['y'] - y
    distance = math.hypot(dx, dy)
    angle_to_goal = math.atan2(dy, dx)
    heading_error = angle_wrap(angle_to_goal - heading)

    # --- Control law ---
    v_max = 50
    v = v_max * math.exp(-2 * abs(heading_error))  # Slow down if not facing the target
    w = 2.0 * heading_error                        # Proportional steering

    # --- Differential drive mapping ---
    L = 140  # mm, track width
    left_speed = v - w * L / 2
    right_speed = v + w * L / 2

    # Clip wheel speeds to +/- v_max
    left_speed = int(max(min(left_speed, v_max), -v_max))
    right_speed = int(max(min(right_speed, v_max), -v_max))

    # --- Completion criterion ---
    position_threshold = 5 if is_sim else 30
    done = distance < position_threshold

    # --- Simulation or hardware update ---
    if is_sim:
        # Unicycle model simulation
        x_new = x + v * math.cos(heading) * dt
        y_new = y + v * math.sin(heading) * dt
        heading_new = angle_wrap(heading + w * dt)
        set_left_motor(0)
        set_right_motor(0)  
    else:
        # Get updated pose from hardware
        x_new, y_new, heading_new = get_hw_pose()
        set_left_motor(left_speed)
        set_right_motor(right_speed) 

    # --- Debugging info, rounded to 2 decimal places ---
    debug = {
        'v': round(v, 2),
        'w': round(w, 2),
        'heading_error': round(heading_error, 2),
        'distance': round(distance, 2),
        'x': round(x, 2),
        'y': round(y, 2),
        'heading': round(math.degrees(heading), 2),
        'left_speed': left_speed,
        'right_speed': right_speed,
        'done': done,
    }
    return x_new, y_new, heading_new, done, debug
