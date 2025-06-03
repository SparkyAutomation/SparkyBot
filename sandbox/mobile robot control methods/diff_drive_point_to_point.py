# point_to_point.py
import math


def control_step(x, y, heading, waypoint, dt, is_sim, get_hw_pose, set_hw_motor):
    dx, dy = waypoint['x'] - x, waypoint['y'] - y
    distance = math.hypot(dx, dy)
    angle_to_goal = math.atan2(dy, dx)
    heading_error = math.atan2(math.sin(angle_to_goal - heading), math.cos(angle_to_goal - heading))
    v = 50 * math.exp(-2 * abs(heading_error))
    w = 2.0 * heading_error

    if is_sim:
        x_new = x + v * math.cos(heading) * dt
        y_new = y + v * math.sin(heading) * dt
        heading_new = heading + w * dt
        set_hw_motor(0, 0)  # No-op in sim
    else:
        # Hardware: update pose from get_hw_pose()
        pose = get_hw_pose()
        x_new, y_new, heading_new = pose
        base_speed = 50
        left_speed = base_speed - w * 30
        right_speed = base_speed + w * 30
        set_hw_motor(left_speed, right_speed)
    done = distance < (5 if is_sim else 30)
    debug = {'v': v, 'w': w, 'heading_error': heading_error, 'distance': distance}
    return x_new, y_new, heading_new, done, debug
