import math
from sparkybotio import setMotor

# Constants
L = 140        # Wheelbase in mm
V_MAX = 50     # Max speed

def angle_wrap(angle):
    """Wrap angle to [-π, π]."""
    return math.atan2(math.sin(angle), math.cos(angle))

def set_left_motor(speed):
    setMotor(2, -speed)
    setMotor(4, -speed)

def set_right_motor(speed):
    setMotor(1, -speed)
    setMotor(3, -speed)

def stop_motors():
    for m in [1, 2, 3, 4]:
        setMotor(m, 0)

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose):
    """
    Point-to-point controller for differential-drive robot.

    Args:
        x, y, heading: Current robot state.
        waypoint: Dict with 'x' and 'y' (in mm).
        dt: Time step (seconds).
        is_sim: True if running in simulation.
        get_hw_pose: Function to get real pose (x, y, heading).

    Returns:
        x_new, y_new, heading_new, done, debug_dict
    """
    dx = waypoint['x'] - x
    dy = waypoint['y'] - y
    distance = math.hypot(dx, dy)
    angle_to_goal = math.atan2(dy, dx)
    heading_error = angle_wrap(angle_to_goal - heading)

    # Control laws
    v = V_MAX * math.exp(-2 * abs(heading_error))   # forward velocity
    w = 2.0 * heading_error                         # angular velocity

    # Convert to motor speeds
    left_speed = int(max(min(v - (w * L / 2), V_MAX), -V_MAX))
    right_speed = int(max(min(v + (w * L / 2), V_MAX), -V_MAX))

    done = distance < (5 if is_sim else 30)

    if is_sim:
        x_new = x + v * math.cos(heading) * dt
        y_new = y + v * math.sin(heading) * dt
        heading_new = angle_wrap(heading + w * dt)
        stop_motors()
    else:
        set_left_motor(left_speed)
        set_right_motor(right_speed)
        x_new, y_new, heading_new = get_hw_pose()

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
