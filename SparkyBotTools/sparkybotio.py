#!/usr/bin/python3
# coding=utf8

import os
import sys
import time
import cv2
import RPi.GPIO as GPIO
from smbus2 import SMBus, i2c_msg


# Constants for I2C addresses and GPIO pins
__ADC_BAT_ADDR = 0
__SERVO_ADDR = 21
__MOTOR_ADDR = 31
__SERVO_ADDR_CMD = 40
__i2c = 1
__i2c_addr = 0x7A

# Initialize GPIO settings
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) 
#In this mode, the pins are identified by their physical pin numbers on the Raspberry Pi board. 

# Initialize motor and servo control variables
__motor_speed = [0, 0, 0, 0]
__servo_angle = [0, 0, 0, 0, 0, 0]
__servo_pulse = [0, 0, 0, 0, 0, 0]


# Function to set motor speed
def setMotor(index, speed):
    """
    Set motor speed.
    :param index: Motor index (1 to 4).
    :param speed: Speed value (-100 to 100).
    :return: Current motor speed.
    """
    if index < 1 or index > 4:
        raise AttributeError("Invalid motor num: %d" % index)
    if index == 2 or index == 4:
        speed = speed
    else:
        speed = -speed
    index -= 1
    speed = 100 if speed > 100 else speed
    speed = -100 if speed < -100 else speed
    reg = __MOTOR_ADDR + index
    with SMBus(__i2c) as bus:
        try:
            msg = i2c_msg.write(__i2c_addr, [reg, speed.to_bytes(1, 'little', signed=True)[0]])
            bus.i2c_rdwr(msg)
            __motor_speed[index] = speed
        except:
            msg = i2c_msg.write(__i2c_addr, [reg, speed.to_bytes(1, 'little', signed=True)[0]])
            bus.i2c_rdwr(msg)
            __motor_speed[index] = speed
    return __motor_speed[index]

# Function to get motor speed
def getMotor(index):
    """
    Get motor speed.
    :param index: Motor index (1 to 4).
    :return: Current motor speed.
    """
    if index < 1 or index > 4:
        raise AttributeError("Invalid motor num: %d" % index)
    index -= 1
    return __motor_speed[index]

# Function to set PWM servo angle
def setServoAngle(index, angle):
    """
    Set PWM servo angle.
    :param index: Servo index (1 to 6).
    :param angle: Angle value (0 to 180).
    :return: Current servo angle.
    """
    if index < 1 or index > 6:
        raise AttributeError("Invalid Servo ID: %d" % index)
    index -= 1
    angle = 180 if angle > 180 else angle
    angle = 0 if angle < 0 else angle
    reg = __SERVO_ADDR + index
    with SMBus(__i2c) as bus:
        try:
            msg = i2c_msg.write(__i2c_addr, [reg, angle])
            bus.i2c_rdwr(msg)
            __servo_angle[index] = angle
            __servo_pulse[index] = int(((200 * angle) / 9) + 500)
        except:
            msg = i2c_msg.write(__i2c_addr, [reg, angle])
            bus.i2c_rdwr(msg)
            __servo_angle[index] = angle
            __servo_pulse[index] = int(((200 * angle) / 9) + 500)
    return __servo_angle[index]


# Function to set PWM servo pulse
def setServoPulse(servo_id, pulse=1500, use_time=1000):
    """
    Set PWM servo pulse.
    :param servo_id: Servo index (1 to 6).
    :param pulse: Pulse value (500 to 2500).
    :param use_time: Time value (0 to 30000).
    :return: Current servo pulse.
    """
    if servo_id < 1 or servo_id > 6:
        raise AttributeError("Invalid Servo ID: %d" % servo_id)
    index = servo_id - 1
    pulse = 500 if pulse < 500 else pulse
    pulse = 2500 if pulse > 2500 else pulse
    use_time = 0 if use_time < 0 else use_time
    use_time = 30000 if use_time > 30000 else use_time
    buf = [__SERVO_ADDR_CMD, 1] + list(use_time.to_bytes(2, 'little')) + [servo_id, ] + list(pulse.to_bytes(2, 'little'))
    with SMBus(__i2c) as bus:
        try:
            msg = i2c_msg.write(__i2c_addr, buf)
            bus.i2c_rdwr(msg)
            __servo_pulse[index] = pulse
            __servo_angle[index] = int((pulse - 500) * 0.09)
        except BaseException as e:
            print(e)
            msg = i2c_msg.write(__i2c_addr, buf)
            bus.i2c_rdwr(msg)
            __servo_pulse[index] = pulse
            __servo_angle[index] = int((pulse - 500) * 0.09)


# Function to set PWM servos pulse
def setServosPulse(args):
    '''
    Set PWM servos pulse.
    :param args: List of arguments [time, number, id1, pos1, id2, pos2, ...]
    '''
    arglen = len(args)
    servos = args[2:arglen:2]
    pulses = args[3:arglen:2]
    use_time = args[0]
    use_time = 0 if use_time < 0 else use_time
    use_time = 30000 if use_time > 30000 else use_time
    servo_number = args[1]
    buf = [__SERVO_ADDR_CMD, servo_number] + list(use_time.to_bytes(2, 'little'))
    dat = zip(servos, pulses)
    for (s, p) in dat:
        buf.append(s)
        p = 500 if p < 500 else p
        p = 2500 if p > 2500 else p
        buf += list(p.to_bytes(2, 'little'))
        __servo_pulse[s - 1] = p
        __servo_angle[s - 1] = int((p - 500) * 0.09)
    with SMBus(__i2c) as bus:
        try:
            msg = i2c_msg.write(__i2c_addr, buf)
            bus.i2c_rdwr(msg)
        except:
            msg = i2c_msg.write(__i2c_addr, buf)
            bus.i2c_rdwr(msg)

# Function to get PWM servo angle
def getServoAngle(servo_id):
    '''
    Get PWM servo angle.
    :param servo_id: Servo index (1 to 6).
    :return: Current servo angle.
    '''
    if servo_id < 1 or servo_id > 6:
        raise AttributeError("Invalid Servo ID: %d" % servo_id)
    index = servo_id - 1
    return __servo_angle[index]

# Function to get PWM servo pulse
def getServoPulse(servo_id):
    '''
    Get PWM servo pulse.
    :param servo_id: Servo index (1 to 6).
    :return: Current servo pulse.
    '''
    if servo_id < 1 or servo_id > 6:
        raise AttributeError("Invalid Servo ID: %d" % servo_id)
    index = servo_id - 1
    return __servo_angle[index]

# Function to get battery level
#


# Function to set servo ID
def setBusServoID(oldid, newid):
    """
    Configure servo id number, default is 1.
    :param oldid: Original id, default is 1.
    :param newid: New id.
    """
    serial_serro_wirte_cmd(oldid, LOBOT_SERVO_ID_WRITE, newid)

# Function to get servo ID
def getBusServoID(id=None):
    """
    Read servo id.
    :param id: Default is None.
    :return: Servo id.
    """
    while True:
        if id is None:
            serial_servo_read_cmd(0xfe, LOBOT_SERVO_ID_READ)
        else:
            serial_servo_read_cmd(id, LOBOT_SERVO_ID_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_ID_READ)
        if msg is not None:
            return msg

# Function to set servo pulse
def setBusServoPulse(id, pulse, use_time):
    """
    Drive servo to the specific position.
    :param id: Servo ID to be driven.
    :param pulse: Position.
    :param use_time: Running time.
    """
    pulse = 0 if pulse < 0 else pulse
    pulse = 1000 if pulse > 1000 else pulse
    use_time = 0 if use_time < 0 else use_time
    use_time = 30000 if use_time > 30000 else use_time
    serial_serro_wirte_cmd(id, LOBOT_SERVO_MOVE_TIME_WRITE, pulse, use_time)

# Function to stop servo
def stopBusServo(id=None):
    '''
    Stop servo running.
    :param id:
    '''
    serial_serro_wirte_cmd(id, LOBOT_SERVO_MOVE_STOP)

# Function to set servo deviation
def setBusServoDeviation(id, d=0):
    """
    Adjust deviation.
    :param id: Servo ID.
    :param d: Deviation.
    """
    serial_serro_wirte_cmd(id, LOBOT_SERVO_ANGLE_OFFSET_ADJUST, d)

# Function to save servo deviation
def saveBusServoDeviation(id):
    """
    Configure deviation, power off protection.
    :param id: Servo ID.
    """
    serial_serro_wirte_cmd(id, LOBOT_SERVO_ANGLE_OFFSET_WRITE)

# Function to get servo deviation
def getBusServoDeviation(id):
    '''
    Read deviation.
    :param id: Servo ID.
    :return: Deviation.
    '''
    count = 0
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_ANGLE_OFFSET_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_ANGLE_OFFSET_READ)
        count += 1
        if msg is not None:
            return msg
        if count > time_out:
            return None

# Function to set servo angle limit
def setBusServoAngleLimit(id, low, high):
    '''
    Set servo turning range.
    :param id:
    :param low:
    :param high:
    '''
    serial_serro_wirte_cmd(id, LOBOT_SERVO_ANGLE_LIMIT_WRITE, low, high)

# Function to get servo angle limit
def getBusServoAngleLimit(id):
    '''
    Read servo turning range.
    :param id:
    :return: Tuple (low-bit, high-bit).
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_ANGLE_LIMIT_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_ANGLE_LIMIT_READ)
        if msg is not None:
            return msg

# Function to set servo voltage limit
def setBusServoVinLimit(id, low, high):
    '''
    Set servo voltage range.
    :param id:
    :param low:
    :param high:
    '''
    serial_serro_wirte_cmd(id, LOBOT_SERVO_VIN_LIMIT_WRITE, low, high)

# Function to get servo voltage limit
def getBusServoVinLimit(id):
    '''
    Read servo turning range.
    :param id:
    :return: Tuple (low-bit, high-bit).
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_VIN_LIMIT_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_VIN_LIMIT_READ)
        if msg is not None:
            return msg

# Function to set servo maximum temperature
def setBusServoMaxTemp(id, m_temp):
    '''
    Set servo maximum temperature alarm.
    :param id:
    :param m_temp:
    '''
    serial_serro_wirte_cmd(id, LOBOT_SERVO_TEMP_MAX_LIMIT_WRITE, m_temp)

# Function to get servo temperature limit
def getBusServoTempLimit(id):
    '''
    Read temperature alarming range.
    :param id:
    :return:
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_TEMP_MAX_LIMIT_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_TEMP_MAX_LIMIT_READ)
        if msg is not None:
            return msg

# Function to get servo pulse
def getBusServoPulse(id):
    '''
    Read servo current position.
    :param id:
    :return:
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_POS_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_POS_READ)
        if msg is not None:
            return msg

# Function to get servo temperature
def getBusServoTemp(id):
    '''
    Read servo temperature.
    :param id:
    :return:
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_TEMP_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_TEMP_READ)
        if msg is not None:
            return msg

# Function to get servo voltage
def getBusServoVin(id):
    '''
    Read servo voltage.
    :param id:
    :return:
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_VIN_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_VIN_READ)
        if msg is not None:
            return msg

# Function to reset servo pulse
def restBusServoPulse(oldid):
    '''
    Reset servo pulse.
    :param oldid:
    '''
    serial_servo_set_deviation(oldid, 0)
    time.sleep(0.1)
    serial_serro_wirte_cmd(oldid, LOBOT_SERVO_MOVE_TIME_WRITE, 500, 100)

# Function to unload servo
def unloadBusServo(id):
    '''
    Power off servo.
    :param id:
    '''
    serial_serro_wirte_cmd(id, LOBOT_SERVO_LOAD_OR_UNLOAD_WRITE, 0)

# Function to get servo load status
def getBusServoLoadStatus(id):
    '''
    Read whether servo is power off.
    :param id:
    :return:
    '''
    while True:
        serial_servo_read_cmd(id, LOBOT_SERVO_LOAD_OR_UNLOAD_READ)
        msg = serial_servo_get_rmsg(LOBOT_SERVO_LOAD_OR_UNLOAD_READ)
        if msg is not None:
            return msg

#  Function to test USB camera.
def usb_camera_test(cam_index):

    cap = cv2.VideoCapture(cam_index)

    if not cap.isOpened():
        print("Cannot open camera")
        return

    cv2.namedWindow("USBCameraTest", cv2.WINDOW_AUTOSIZE)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot receive frames. Exiting")
            break
        
        cv2.imshow("USBCameraTest", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# Function to beep
def beep(new_state):
    '''
    Set buzzer state.
    :param new_state: New state of the buzzer (0 or 1).
    '''
    GPIO.setup(31, GPIO.OUT)
    GPIO.output(31, new_state)


# Function to test the infrared line sensor
def readInfrared():
    register=0x01
    address=0x78
    bus=1
    value = SMBus(bus).read_byte_data(address, register)
    return [True if value & v > 0 else False for v in [0x01, 0x02, 0x04, 0x08]]
    
def readDistance():
    i2c_addr = 0x77
    i2c = 1
    dist = 99999
    try:
        with SMBus(i2c) as bus:
            msg = i2c_msg.write(i2c_addr, [0,])
            bus.i2c_rdwr(msg)
            read = i2c_msg.read(i2c_addr, 1)
            bus.i2c_rdwr(read)
            dist = int.from_bytes(bytes(list(read)), byteorder='little', signed=False)
            if dist > 5000:
                dist = 5000
    except BaseException as e:
        print(e)
    return dist
