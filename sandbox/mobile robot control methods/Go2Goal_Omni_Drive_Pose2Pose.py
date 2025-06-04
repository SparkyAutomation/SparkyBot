import math
from sparkybotio import setMotor

# Constants
V_MAX = 80            # Max translational speed [mm/s]
K_P = 1.2             # Gain for position control
MIN_VELOCITY = 40     # Minimum linear velocity [mm/s]

K_THETA = 0.5         # Gain for heading control
W_MAX = 25            # Max angular velocity (arbitrary units, tuned for hardware)

def angle_wrap(a):
    """Wrap angle to [-π, π]."""
    return math.atan2(math.sin(a), math.cos(a))

def stop_motors():
    """Stop all motors."""
    for m in [1, 2, 3, 4]:
        setMotor(m, 0)

def set_omni_velocity(vx, vy, w=0):
    """
    Convert vx, vy, w into individual motor speeds.
    vx, vy: linear velocities [mm/s]
    w: angular velocity command (unitless, for now)
    """
    vx = max(min(vx, V_MAX), -V_MAX)
    vy = max(min(vy, V_MAX), -V_MAX)
    w = max(min(w, W_MAX), -W_MAX)

    # Motor mapping: FL=4, BL=2, FR=3, BR=1
    fl_speed = vy + vx + w
    bl_speed = vy - vx + w
    fr_speed = vy - vx - w
    br_speed = vy + vx - w

    setMotor(4, -int(fl_speed))  # Front Left
    setMotor(2, -int(bl_speed))  # Back Left
    setMotor(3, -int(fr_speed))  # Front Right
    setMotor(1, -int(br_speed))  # Back Right

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose):
    """
    Pose-to-pose controller: aligns both position and heading.

    Args:
        x, y, heading: current robot pose [mm, mm, rad]
        waypoint: {'x': mm, 'y': mm, 'heading': rad}
        dt: timestep [s]
        is_sim: True for simulation mode
        get_hw_pose: function returning (x, y, heading)

    Returns:
        x_new, y_new, heading_new, done, debug
    """
    # Goal pose
    xT, yT, theta = waypoint['x'], waypoint['y'], waypoint['theta']

    # Position error
    dx = xT - x
    dy = yT - y
    distance = math.hypot(dx, dy)

    # Heading error
    dtheta = angle_wrap(theta - heading)
    dtheta_deg = math.degrees(dtheta)
    
    # Thresholds
    pos_threshold = 5 if is_sim else 30  # mm
    heading_threshold = math.radians(5)  # radians (~5 deg)

    # Check if done (both position and heading aligned)
    done = (distance < pos_threshold) and (abs(dtheta) < heading_threshold)

    # Translational velocity
    if distance > pos_threshold:
        angle_to_goal = math.atan2(dy, dx)
        velocity = min(K_P * distance, V_MAX)
        if velocity < MIN_VELOCITY:
            velocity = MIN_VELOCITY
        vx = velocity * math.cos(angle_to_goal)
        vy = velocity * math.sin(angle_to_goal)
    else:
        vx = vy = 0

    # Angular velocity
    if abs(dtheta) > heading_threshold:
        w = K_THETA * dtheta
        w = max(min(w, W_MAX), -W_MAX)
    else:
        w = 0

    if done:
        vx = vy = w = 0

    if is_sim:  # simulation mode
        if not done:
            x_new = x + vx * dt
            y_new = y + vy * dt
            heading_new = angle_wrap(heading + w * dt)
        else:
            x_new, y_new, heading_new = x, y, heading
        stop_motors()
    else:  # hardware mode
        if done:
            stop_motors()
        else:
            set_omni_velocity(vx, vy, w)
        x_new, y_new, heading_new = get_hw_pose()

    debug = {
        'x': round(x, 2),
        'y': round(y, 2),
        'heading': round(math.degrees(heading), 2),
        'dx': round(dx, 2),
        'dy': round(dy, 2),
        'dtheta_deg': round(dtheta_deg, 2),
        'vx': round(vx, 2),
        'vy': round(vy, 2),
        'w': round(w, 2),
        'distance': round(distance, 2),
        'done': done
    }

    return x_new, y_new, heading_new, done, debug
