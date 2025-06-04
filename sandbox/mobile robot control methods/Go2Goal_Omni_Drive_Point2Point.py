import math
from sparkybotio import setMotor

# Constants
V_MAX = 80          # Max translational speed [mm/s]
K_P = 1.2           # Proportional gain for position control
MIN_VELOCITY = 40    # Minimum velocity to overcome friction [mm/s]

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
    vx, vy: linear velocities in mm/s
    w: angular velocity (optional)
    """
    vx = max(min(vx, V_MAX), -V_MAX)
    vy = max(min(vy, V_MAX), -V_MAX)

    # Motor configuration: FL=4, BL=2, FR=3, BR=1
    fl_speed = vy + vx
    bl_speed = vy - vx
    fr_speed = vy - vx
    br_speed = vy + vx

    # Reverse sign to match positive=backward convention
    setMotor(4, -int(fl_speed))  # Front Left
    setMotor(2, -int(bl_speed))  # Back Left
    setMotor(3, -int(fr_speed))  # Front Right
    setMotor(1, -int(br_speed))  # Back Right

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose):
    """
    Point-to-point controller for omni robot using polar velocity logic.

    Args:
        x, y, heading: current pose (mm, mm, rad)
        waypoint: {'x': mm, 'y': mm}
        dt: timestep (s)
        is_sim: True if simulation mode
        get_hw_pose: function returning (x, y, heading)

    Returns:
        x_new, y_new, heading_new, done, debug
    """
    # Target
    xT = waypoint['x']
    yT = waypoint['y']

    # Position error
    dx = xT - x
    dy = yT - y
    distance = math.hypot(dx, dy)

    # Position threshold to stop
    position_threshold = 5 if is_sim else 30  # mm

    # Calculate velocity direction and magnitude
    if distance > position_threshold:
        angle_to_goal = math.atan2(dy, dx)
        velocity = min(K_P * distance, V_MAX)
        # Enforce minimum velocity
        if velocity < MIN_VELOCITY:
            velocity = MIN_VELOCITY
        vx = velocity * math.cos(angle_to_goal)
        vy = velocity * math.sin(angle_to_goal)
    else:
        vx = vy = 0

    done = distance < position_threshold

    if is_sim:
        # Simulate pose update
        x_new = x + vx * dt
        y_new = y + vy * dt
        heading_new = heading
        stop_motors()
    else:
        if done:
            stop_motors()
        else:
            set_omni_velocity(vx, vy)
        x_new, y_new, heading_new = get_hw_pose()

    # Debug info
    debug = {
        'x': round(x, 2),
        'y': round(y, 2),
        'dx': dx,
        'dy': dy,
        'vx': round(vx, 2),
        'vy': round(vy, 2),
        'distance': round(distance, 2),
        'done': done
    }

    return x_new, y_new, heading_new, done, debug
