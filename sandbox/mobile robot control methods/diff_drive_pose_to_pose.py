import math

def angle_wrap(a):
    """
    Wrap angle a to [-pi, pi]
    """
    return math.atan2(math.sin(a), math.cos(a))

def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose, set_hw_motor):
    """
    Pose-to-pose control for a differential drive robot, using unicycle model.
    
    Parameters:
    - x, y, heading: Robot's current pose [mm, mm, radians]
    - waypoint: dict with keys 'x', 'y', 'theta' [mm, mm, radians]
    - dt: timestep [s]
    - is_sim: True for simulation, False for hardware
    - get_hw_pose: function to get hardware pose (x, y, heading) [used only if is_sim==False]
    - set_hw_motor: function to set left/right wheel speeds

    Returns:
    - x_new, y_new, heading_new: updated pose
    - done: True if at target pose
    - debug: dictionary with debug values
    """

    # ===== Parameters =====
    v_max = 40  # Max forward speed [mm/s]
    k_alpha = 2.5  # Gain for heading to goal
    k_beta = 2.5  # Gain for final orientation (must be negative!)

    # Stopping thresholds
    position_threshold = 5 if is_sim else 30  # mm
    heading_threshold = math.radians(10)      # radians

    # ===== Compute pose errors =====
    xT, yT, thetaT = waypoint["x"], waypoint["y"], waypoint["theta"]
    dx = xT - x
    dy = yT - y
    rho = math.hypot(dx, dy)  # Distance to goal

    phi = math.atan2(dy, dx)  # Angle to goal (global)
    alpha = angle_wrap(phi - heading)      # Heading error to goal (relative to robot)
    beta = angle_wrap(phi - thetaT)        # Desired final orientation relative to path to goal

    # ===== Control Law =====
    # Linear and angular velocity (unicycle model)
    v = v_max
    w = k_alpha * alpha + k_beta * beta

    # Limit forward velocity (optionally modulate by heading error)
    if abs(alpha) > math.pi / 2:
        # If the goal is behind, drive backwards
        v = -v

    # Saturate linear speed to v_max
    v = max(min(v, v_max), -v_max)

    # ===== Completion Condition =====
    done = (rho < position_threshold) and (abs(angle_wrap(thetaT - heading)) < heading_threshold)

    # ===== Sim or Hardware Step =====
    if is_sim:
        # Simulate robot motion using unicycle model
        # Use old heading to update pose (Euler integration)
        x_new = x + v * dt * math.cos(heading)
        y_new = y + v * dt * math.sin(heading)
        heading_new = angle_wrap(heading + w * dt)
        set_hw_motor(0, 0)  # No-op for simulation (can remove)
    else:
        # Get current pose from hardware
        x_new, y_new, heading_new = get_hw_pose()

        # Differential drive mapping: simple proportional wheel speeds
        # Map v (linear) and w (angular) to left/right wheel speeds
        L = 160  # mm, distance between wheels (set to your robot's actual wheelbase!)
        left_speed = v - w * L / 2
        right_speed = v + w * L / 2

        # Saturate wheel speeds
        left_speed = max(min(left_speed, v_max), -v_max)
        right_speed = max(min(right_speed, v_max), -v_max)

        set_hw_motor(left_speed, right_speed)

    # ===== Debugging info =====
    debug = {
        'rho': rho,
        'alpha': alpha,
        'beta': beta,
        'v': v,
        'w': w,
        'x': x,
        'y': y,
        'heading': heading,
        'xT': xT,
        'yT': yT,
        'thetaT': thetaT,
        'left_speed': left_speed if not is_sim else None,
        'right_speed': right_speed if not is_sim else None,
        'done': done
    }

    return x_new, y_new, heading_new, done, debug

