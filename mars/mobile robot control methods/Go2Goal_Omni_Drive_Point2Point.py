import math
from sparkybotio import setMotor

# Constants
V_MAX = 80          # Max translational speed [mm/s]
LOOKAHEAD = 120     # Lookahead distance [mm]
MIN_VELOCITY = 5    # Minimum velocity to overcome friction [mm/s]
K_P = 1.0           # Gain (optional for velocity ramp)

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
    """
    vx = max(min(vx, V_MAX), -V_MAX)
    vy = max(min(vy, V_MAX), -V_MAX)

    # Your motor map: FL=4, BL=2, FR=3, BR=1; positive is backward rotation, so sign flip.
    fl_speed = vy + vx
    bl_speed = vy - vx
    fr_speed = vy - vx
    br_speed = vy + vx

    setMotor(4, -int(fl_speed))  # Front Left
    setMotor(2, -int(bl_speed))  # Back Left
    setMotor(3, -int(fr_speed))  # Front Right
    setMotor(1, -int(br_speed))  # Back Right

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose):
    """
    Pure pursuit point-to-point for omni-directional robot.

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

    # --- Pure pursuit logic: get lookahead point ---
    if distance > LOOKAHEAD:
        scale = LOOKAHEAD / distance
        lx = x + dx * scale
        ly = y + dy * scale
        to_lookahead_x = lx - x
        to_lookahead_y = ly - y
        lookahead_distance = LOOKAHEAD
    else:
        # If within lookahead, just go to goal
        to_lookahead_x = dx
        to_lookahead_y = dy
        lookahead_distance = distance

    # --- Compute velocity command toward lookahead point ---
    if lookahead_distance > 1e-4:
        vx = K_P * to_lookahead_x
        vy = K_P * to_lookahead_y
        mag = math.hypot(vx, vy)
        # Clamp to V_MAX
        if mag > V_MAX:
            vx *= V_MAX / mag
            vy *= V_MAX / mag
        elif mag < MIN_VELOCITY and distance > (5 if is_sim else 30):
            # Enforce minimum velocity if not done
            vx = (vx / mag) * MIN_VELOCITY if mag != 0 else 0
            vy = (vy / mag) * MIN_VELOCITY if mag != 0 else 0
    else:
        vx, vy = 0, 0

    # --- Completion criterion ---
    position_threshold = 5 if is_sim else 30
    done = distance < position_threshold

    # --- Sim or hardware ---
    if is_sim:
        x_new = x + vx * dt
        y_new = y + vy * dt
        heading_new = heading
        stop_motors()
    else:
        set_omni_velocity(vx, vy)
        x_new, y_new, heading_new = get_hw_pose()

    debug = {
        'x': round(x, 2),
        'y': round(y, 2),
        'lookahead_x': round(x + to_lookahead_x, 2),
        'lookahead_y': round(y + to_lookahead_y, 2),
        'vx': round(vx, 2),
        'vy': round(vy, 2),
        'distance': round(distance, 2),
        'lookahead_distance': round(lookahead_distance, 2),
        'done': done
    }

    return x_new, y_new, heading_new, done, debug
