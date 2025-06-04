import math
from sparkybotio import setMotor

# Constants
L = 160       # Wheelbase in mm (adjust for your robot)
V_MAX = 40    # Max linear speed [mm/s]
K_ALPHA = 2.5 # Gain for angle to goal
K_BETA = -2.5 # Gain for final heading alignment

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
    Pose-to-pose control for a differential-drive robot.

    Args:
        x, y, heading: Current robot state [mm, mm, rad]
        waypoint: Dict with keys 'x', 'y', 'theta' [mm, mm, rad]
        dt: Time step [s]
        is_sim: True if running in simulation
        get_hw_pose: Function returning (x, y, heading)

    Returns:
        x_new, y_new, heading_new, done, debug
    """
    # Goal pose
    xT, yT, theta = waypoint['x'], waypoint['y'], waypoint['theta']

    # Errors
    dx = xT - x
    dy = yT - y
    rho = math.hypot(dx, dy)                      # Distance to target
    phi = math.atan2(dy, dx)
    alpha = angle_wrap(phi - heading)             # Heading to target
    beta = angle_wrap(theta - phi)               # Final orientation error
    #print(theta, heading, phi)

    # Directional control
    v = V_MAX if abs(alpha) < math.pi / 2 else -V_MAX
    w = K_ALPHA * alpha + K_BETA * beta
    v = max(min(v, V_MAX), -V_MAX)

    # Completion condition
    position_threshold = 5 if is_sim else 30
    heading_threshold = math.radians(10)
    done = (rho < position_threshold) and (abs(angle_wrap(theta - heading)) < heading_threshold)

    if is_sim:
        # Euler integration using unicycle model
        x_new = x + v * math.cos(heading) * dt
        y_new = y + v * math.sin(heading) * dt
        heading_new = angle_wrap(heading + w * dt)
        stop_motors()
        left_speed = right_speed = None
    else:
        if done:
            stop_motors()
            left_speed = right_speed = 0
        else:
            left_speed = int(max(min(v - w * L / 2, V_MAX), -V_MAX))
            right_speed = int(max(min(v + w * L / 2, V_MAX), -V_MAX))
            set_left_motor(left_speed)
            set_right_motor(right_speed)
        x_new, y_new, heading_new = get_hw_pose()

    debug = {
        'x': round(x, 2),
        'y': round(y, 2),
        'heading': round(math.degrees(heading), 2),
        'xT': xT,
        'yT': yT,
        'theta': round(math.degrees(theta), 2),
        'rho': round(rho, 2),
        'alpha': round(math.degrees(alpha), 2),
        'beta': round(math.degrees(beta), 2),
        'v': round(v, 2),
        'w': round(w, 2),
        'left_speed': left_speed,
        'right_speed': right_speed,
        'done': done,
    }

    return x_new, y_new, heading_new, done, debug
