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

    # Calculate raw motor speeds based on standard X-drive logic
    # Your original code was:
    # setMotor(1, int(vy - vx))  # Front Left
    # setMotor(2, int(vy + vx))  # Front Right
    # setMotor(3, int(vy - vx))  # Back Left
    # setMotor(4, int(vy + vx))  # Back Right

    # But your numbering is:
    # FL = 4, BL = 2, FR = 3, BR = 1
    # Also positive = backward rotation, so flip sign

    # Compute motor speeds (before sign flip)
    fl_speed = vy + vx  # Front Left wheel (usually combined like this)
    bl_speed = vy - vx  # Back Left wheel
    fr_speed = vy - vx  # Front Right wheel
    br_speed = vy + vx  # Back Right wheel

    # Flip signs for your positive=backward convention
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
    # Target position
    xT = waypoint['x']
    yT = waypoint['y']

    # Calculate position error
    dx = xT - x
    dy = yT - y
    distance = math.hypot(dx, dy)

    # Proportional velocity command
    vx = K_P * dx
    vy = K_P * dy

    # Velocity magnitude
    mag = math.hypot(vx, vy)

    # Position threshold to consider goal reached
    position_threshold = 5 if is_sim else 30  # mm

    # Clamp velocity to max speed and apply minimum velocity if needed
    if mag > V_MAX:
        vx *= V_MAX / mag
        vy *= V_MAX / mag
    elif mag < MIN_VELOCITY and distance > position_threshold:
        # Boost velocity commands to minimum velocity in direction of error
        vx = (vx / mag) * MIN_VELOCITY if mag != 0 else 0
        vy = (vy / mag) * MIN_VELOCITY if mag != 0 else 0
    elif distance < position_threshold:
        # Stop if within threshold
        vx, vy = 0, 0

    # Check if done
    done = distance < position_threshold

    # Simulation or hardware actuation
    if is_sim:
        # Update pose using simple kinematics
        x_new = x + vx * dt
        y_new = y + vy * dt
        heading_new = heading  # Heading remains unchanged for pure translation
        stop_motors()
    else:
        # Send velocity commands to hardware motors
        set_omni_velocity(vx, vy)
        x_new, y_new, heading_new = get_hw_pose()

    # Debug info for monitoring
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
