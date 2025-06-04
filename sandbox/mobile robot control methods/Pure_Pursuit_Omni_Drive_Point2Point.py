import math
from sparkybotio import setMotor

# Constants
V_MAX = 80          # Max translational speed [mm/s]
K_P = 1.2           # Proportional gain for position control
MIN_VELOCITY = 5    # Minimum velocity command to overcome friction [mm/s]

def angle_wrap(a):
    """Wrap angle to [-π, π]."""
    return math.atan2(math.sin(a), math.cos(a))

def stop_motors():
    """Stop all motors."""
    for m in [1, 2, 3, 4]:
        setMotor(m, 0)

def set_omni_velocity(vx, vy, w=0):
    """
    Convert vx, vy, w into individual motor speeds for your motor numbering and sign convention.
    vx, vy: linear velocities in mm/s
    w: angular velocity (optional, set 0 if unused)
    """
    # Clamp input velocities
    vx = max(min(vx, V_MAX), -V_MAX)
    vy = max(min(vy, V_MAX), -V_MAX)

    # Motor mixing for X-drive (your custom numbering and sign)
    fl_speed = vy + vx  # Front Left
    bl_speed = vy - vx  # Back Left
    fr_speed = vy - vx  # Front Right
    br_speed = vy + vx  # Back Right

    # Flip sign for your convention
    setMotor(4, -int(fl_speed))  # Front Left
    setMotor(2, -int(bl_speed))  # Back Left
    setMotor(3, -int(fr_speed))  # Front Right
    setMotor(1, -int(br_speed))  # Back Right

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose):
    """
    Point-to-point controller for omni-directional robot.

    Args:
        x, y, heading: Current pose (mm, mm, rad)
        waypoint: {'x': mm, 'y': mm}
        dt: timestep (s)
        is_sim: True if sim mode
        get_hw_pose: function returning (x, y, heading)

    Returns:
        x_new, y_new, heading_new, done, debug
    """
    xT = waypoint['x']
    yT = waypoint['y']

    dx = xT - x
    dy = yT - y
    distance = math.hypot(dx, dy)

    vx = K_P * dx
    vy = K_P * dy
    mag = math.hypot(vx, vy)

    position_threshold = 5 if is_sim else 30  # mm

    # Clamp and minimum velocity logic
    if mag > V_MAX:
        vx *= V_MAX / mag
        vy *= V_MAX / mag
    elif mag < MIN_VELOCITY and distance > position_threshold:
        if mag != 0:
            vx = (vx / mag) * MIN_VELOCITY
            vy = (vy / mag) * MIN_VELOCITY
        else:
            vx = 0
            vy = 0
    elif distance < position_threshold:
        vx, vy = 0, 0

    done = distance < position_threshold

    if is_sim:
        x_new = x + vx * dt
        y_new = y + vy * dt
        heading_new = heading  # Heading stays the same
        stop_motors()
    else:
        set_omni_velocity(vx, vy)
        x_new, y_new, heading_new = get_hw_pose()

    debug = {
        'x': round(x, 2),
        'y': round(y, 2),
        'dx': round(dx, 2),
        'dy': round(dy, 2),
        'vx': round(vx, 2),
        'vy': round(vy, 2),
        'distance': round(distance, 2),
        'done': done
    }

    return x_new, y_new, heading_new, done, debug
