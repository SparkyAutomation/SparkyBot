#!/usr/bin/env python3
# coding: utf-8

import struct
import time
import serial
import threading

class Sparky:
    __uart_state = 0

    def __init__(self, car_type=1, com="/dev/myserial", delay=0.002, debug=False):
        self.ser = serial.Serial(com, 115200)
        self.__delay_time = delay
        self.__debug = debug

        self.__HEAD = 0xFF
        self.__DEVICE_ID = 0xFC
        self.__COMPLEMENT = 257 - self.__DEVICE_ID
        self.__CAR_TYPE = car_type
        self.__CAR_ADJUST = 0x80

        self.FUNC_AUTO_REPORT = 0x01
        self.FUNC_BEEP = 0x02
        self.FUNC_PWM_SERVO = 0x03
        self.FUNC_PWM_SERVO_ALL = 0x04
        self.FUNC_RGB = 0x05
        self.FUNC_RGB_EFFECT = 0x06
        self.FUNC_REPORT_SPEED = 0x0A
        self.FUNC_REPORT_IMU_RAW = 0x0B
        self.FUNC_REPORT_IMU_ATT = 0x0C
        self.FUNC_REPORT_ENCODER = 0x0D
        self.FUNC_MOTOR = 0x10
        self.FUNC_CAR_RUN = 0x11
        self.FUNC_MOTION = 0x12
        self.FUNC_SET_MOTOR_PID = 0x13
        self.FUNC_SET_YAW_PID = 0x14
        self.FUNC_SET_CAR_TYPE = 0x15
        self.FUNC_UART_SERVO = 0x20
        self.FUNC_UART_SERVO_ID = 0x21
        self.FUNC_UART_SERVO_TORQUE = 0x22
        self.FUNC_ARM_CTRL = 0x23
        self.FUNC_ARM_OFFSET = 0x24
        self.FUNC_AKM_DEF_ANGLE = 0x30
        self.FUNC_AKM_STEER_ANGLE = 0x31
        self.FUNC_REQUEST_DATA = 0x50
        self.FUNC_VERSION = 0x51
        self.FUNC_RESET_FLASH = 0xA0

        self.CARTYPE_X3 = 0x01
        self.CARTYPE_X3_PLUS = 0x02
        self.CARTYPE_X1 = 0x04
        self.CARTYPE_R2 = 0x05

        self.__ax = self.__ay = self.__az = 0
        self.__gx = self.__gy = self.__gz = 0
        self.__mx = self.__my = self.__mz = 0
        self.__vx = self.__vy = self.__vz = 0
        self.__yaw = self.__roll = self.__pitch = 0
        self.__encoder_m1 = self.__encoder_m2 = self.__encoder_m3 = self.__encoder_m4 = 0
        self.__read_id = self.__read_val = 0
        self.__read_arm_ok = 0
        self.__read_arm = [-1] * 6
        self.__version_H = self.__version_L = self.__version = 0
        self.__pid_index = self.__kp1 = self.__ki1 = self.__kd1 = 0
        self.__arm_offset_state = self.__arm_offset_id = 0
        self.__arm_ctrl_enable = True
        self.__battery_voltage = 0
        self.__akm_def_angle = 100
        self.__akm_readed_angle = False
        self.__AKM_SERVO_ID = 0x01

        if self.__debug:
            print(f"cmd_delay={self.__delay_time}s")
        if self.ser.isOpen():
            print("Sparky Serial Opened! Baudrate=115200")
        else:
            print("Serial Open Failed!")
        time.sleep(self.__delay_time)

    def __del__(self):
        try:
            self.ser.close()
            self.__uart_state = 0
            print("serial Close!")
        except Exception:
            pass

    def __parse_data(self, ext_type, ext_data):
        if ext_type == self.FUNC_REPORT_SPEED:
            self.__vx = int(struct.unpack('h', bytearray(ext_data[0:2]))[0]) / 1000.0
            self.__vy = int(struct.unpack('h', bytearray(ext_data[2:4]))[0]) / 1000.0
            self.__vz = int(struct.unpack('h', bytearray(ext_data[4:6]))[0]) / 1000.0
            self.__battery_voltage = struct.unpack('B', bytearray(ext_data[6:7]))[0]
        elif ext_type == self.FUNC_REPORT_IMU_RAW:
            gyro_ratio = 1 / 3754.9
            self.__gx = struct.unpack('h', bytearray(ext_data[0:2]))[0] * gyro_ratio
            self.__gy = struct.unpack('h', bytearray(ext_data[2:4]))[0] * -gyro_ratio
            self.__gz = struct.unpack('h', bytearray(ext_data[4:6]))[0] * -gyro_ratio
            accel_ratio = 1 / 1671.84
            self.__ax = struct.unpack('h', bytearray(ext_data[6:8]))[0] * accel_ratio
            self.__ay = struct.unpack('h', bytearray(ext_data[8:10]))[0] * accel_ratio
            self.__az = struct.unpack('h', bytearray(ext_data[10:12]))[0] * accel_ratio
            mag_ratio = 1
            self.__mx = struct.unpack('h', bytearray(ext_data[12:14]))[0] * mag_ratio
            self.__my = struct.unpack('h', bytearray(ext_data[14:16]))[0] * mag_ratio
            self.__mz = struct.unpack('h', bytearray(ext_data[16:18]))[0] * mag_ratio
        elif ext_type == self.FUNC_REPORT_IMU_ATT:
            self.__roll = struct.unpack('h', bytearray(ext_data[0:2]))[0] / 10000.0
            self.__pitch = struct.unpack('h', bytearray(ext_data[2:4]))[0] / 10000.0
            self.__yaw = struct.unpack('h', bytearray(ext_data[4:6]))[0] / 10000.0
        elif ext_type == self.FUNC_REPORT_ENCODER:
            self.__encoder_m1 = struct.unpack('i', bytearray(ext_data[0:4]))[0]
            self.__encoder_m2 = struct.unpack('i', bytearray(ext_data[4:8]))[0]
            self.__encoder_m3 = struct.unpack('i', bytearray(ext_data[8:12]))[0]
            self.__encoder_m4 = struct.unpack('i', bytearray(ext_data[12:16]))[0]
        elif ext_type == self.FUNC_UART_SERVO:
            self.__read_id = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__read_val = struct.unpack('h', bytearray(ext_data[1:3]))[0]
            if self.__debug:
                print("FUNC_UART_SERVO:", self.__read_id, self.__read_val)
        elif ext_type == self.FUNC_ARM_CTRL:
            for i in range(6):
                self.__read_arm[i] = struct.unpack('h', bytearray(ext_data[i*2:(i+1)*2]))[0]
            self.__read_arm_ok = 1
            if self.__debug:
                print("FUNC_ARM_CTRL:", self.__read_arm)
        elif ext_type == self.FUNC_VERSION:
            self.__version_H = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__version_L = struct.unpack('B', bytearray(ext_data[1:2]))[0]
            if self.__debug:
                print("FUNC_VERSION:", self.__version_H, self.__version_L)
        elif ext_type == self.FUNC_SET_MOTOR_PID:
            self.__pid_index = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__kp1 = struct.unpack('h', bytearray(ext_data[1:3]))[0]
            self.__ki1 = struct.unpack('h', bytearray(ext_data[3:5]))[0]
            self.__kd1 = struct.unpack('h', bytearray(ext_data[5:7]))[0]
            if self.__debug:
                print("FUNC_SET_MOTOR_PID:", self.__pid_index, [self.__kp1, self.__ki1, self.__kd1])
        elif ext_type == self.FUNC_SET_YAW_PID:
            self.__pid_index = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__kp1 = struct.unpack('h', bytearray(ext_data[1:3]))[0]
            self.__ki1 = struct.unpack('h', bytearray(ext_data[3:5]))[0]
            self.__kd1 = struct.unpack('h', bytearray(ext_data[5:7]))[0]
            if self.__debug:
                print("FUNC_SET_YAW_PID:", self.__pid_index, [self.__kp1, self.__ki1, self.__kd1])
        elif ext_type == self.FUNC_ARM_OFFSET:
            self.__arm_offset_id = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__arm_offset_state = struct.unpack('B', bytearray(ext_data[1:2]))[0]
            if self.__debug:
                print("FUNC_ARM_OFFSET:", self.__arm_offset_id, self.__arm_offset_state)
        elif ext_type == self.FUNC_AKM_DEF_ANGLE:
            _id = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__akm_def_angle = struct.unpack('B', bytearray(ext_data[1:2]))[0]
            self.__akm_readed_angle = True
            if self.__debug:
                print("FUNC_AKM_DEF_ANGLE:", _id, self.__akm_def_angle)

    def __receive_data(self):
        while True:
            head1 = bytearray(self.ser.read())[0]
            if head1 == self.__HEAD:
                head2 = bytearray(self.ser.read())[0]
                if head2 == self.__DEVICE_ID - 1:
                    ext_len = bytearray(self.ser.read())[0]
                    ext_type = bytearray(self.ser.read())[0]
                    ext_data = []
                    check_sum = ext_len + ext_type
                    data_len = ext_len - 2
                    rx_check_num = 0
                    while len(ext_data) < data_len:
                        value = bytearray(self.ser.read())[0]
                        ext_data.append(value)
                        if len(ext_data) == data_len:
                            rx_check_num = value
                        else:
                            check_sum += value
                    if check_sum % 256 == rx_check_num:
                        self.__parse_data(ext_type, ext_data)
                    elif self.__debug:
                        print("check sum error:", ext_len, ext_type, ext_data)

    def __request_data(self, function, param=0):
        cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_REQUEST_DATA, int(function) & 0xff, int(param) & 0xff]
        checksum = sum(cmd, self.__COMPLEMENT) & 0xff
        cmd.append(checksum)
        self.ser.write(cmd)
        if self.__debug:
            print("request:", cmd)
        time.sleep(self.__delay_time)

    def __limit_motor_value(self, value):
        if value == 127:
            return 127
        return max(-100, min(100, int(value)))

    def create_receive_threading(self):
        try:
            if self.__uart_state == 0:
                task_receive = threading.Thread(target=self.__receive_data, name="task_serial_receive", daemon=True)
                task_receive.start()
                print("----------------create receive threading--------------")
                self.__uart_state = 1
        except Exception:
            print('---create_receive_threading error!---')

    def set_auto_report_state(self, enable, forever=False):
        try:
            state1 = 1 if enable else 0
            state2 = 0x5F if forever else 0
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_AUTO_REPORT, state1, state2]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("report:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_auto_report_state error!---')

    def set_beep(self, on_time):
        try:
            if on_time < 0:
                print("beep input error!")
                return
            value = bytearray(struct.pack('h', int(on_time)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_BEEP, value[0], value[1]]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("beep:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_beep error!---')

    def set_pwm_servo(self, servo_id, angle):
        try:
            if not (1 <= servo_id <= 4):
                if self.__debug:
                    print("set_pwm_servo input invalid")
                return
            angle = max(0, min(180, int(angle)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_PWM_SERVO, int(servo_id), angle]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("pwmServo:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_pwm_servo error!---')

    def set_pwm_servo_all(self, angle_s1, angle_s2, angle_s3, angle_s4):
        try:
            angles = [angle_s1, angle_s2, angle_s3, angle_s4]
            for i in range(4):
                if angles[i] < 0 or angles[i] > 180:
                    angles[i] = 255
            cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_PWM_SERVO_ALL, *map(int, angles)]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("all Servo:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_pwm_servo_all error!---')

    #0ed_id =[0, 13], control the CORRESPONDING numbered RGB lights;  led_id =0xFF, controls all lights.
    def set_led(self, led_id, red, green, blue):
        try:
            cmd = [
                self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_RGB,
                int(led_id) & 0xff, int(red) & 0xff, int(green) & 0xff, int(blue) & 0xff
            ]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("LED:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_led error!---')

    # Effect =[0, 6], 0: stop light effect, 1: running light, 2: running horse light, 3: breathing light, 4: gradient light, 5: starlight, 6: power display 
    # Speed =[1, 10], the smaller the value, the faster the speed changes
    # Parm, left blank, as an additional argument.  Usage 1: The color of breathing lamp can be modified by the effect of breathing lamp [0, 6]
    def set_led_pattern(self, effect, speed=255, parm=255):
        try:
            cmd = [
                self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_RGB_EFFECT,
                int(effect) & 0xff, int(speed) & 0xff, int(parm) & 0xff
            ]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("LED_pattern:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_led_pattern error!---')

    def set_motor(self, speed_1, speed_2, speed_3, speed_4):
        try:
            vals = [
                self.__limit_motor_value(speed_1),
                self.__limit_motor_value(speed_2),
                self.__limit_motor_value(speed_3),
                self.__limit_motor_value(speed_4)
            ]
            packed = [bytearray(struct.pack('b', v))[0] for v in vals]
            cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_MOTOR, *packed]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("motor:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_motor error!---')

    def set_uart_servo(self, servo_id, pulse_value, run_time=500):
        try:
            if not self.__arm_ctrl_enable:
                return
            if servo_id < 1 or pulse_value < 96 or pulse_value > 4000 or run_time < 0:
                print("set uart servo input error")
                return
            if run_time > 2000:
                run_time = 2000
            if run_time < 0:
                run_time = 0
            s_id = int(servo_id) & 0xff
            value = bytearray(struct.pack('h', int(pulse_value)))
            r_time = bytearray(struct.pack('h', int(run_time)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_UART_SERVO,
                   s_id, value[0], value[1], r_time[0], r_time[1]]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("uartServo:", servo_id, int(pulse_value), cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_uart_servo error!---')

    def set_uart_servo_angle(self, s_id, s_angle, run_time=500):
        try:
            valid = [
                (s_id == 1 and 0 <= s_angle <= 180),
                (s_id == 2 and 0 <= s_angle <= 180),
                (s_id == 3 and 0 <= s_angle <= 180),
                (s_id == 4 and 0 <= s_angle <= 180),
                (s_id == 5 and 0 <= s_angle <= 270),
                (s_id == 6 and 0 <= s_angle <= 180)
            ]
            if any(valid):
                value = self.__arm_convert_value(s_id, s_angle)
                self.set_uart_servo(s_id, value, run_time)
            else:
                print(f"angle_{s_id} set error!")
        except Exception:
            print(f'---set_uart_servo_angle error! ID={s_id}---')

    def set_uart_servo_id(self, servo_id):
        try:
            if servo_id < 1 or servo_id > 250:
                print("servo id input error!")
                return
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x04, self.FUNC_UART_SERVO_ID, int(servo_id)]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("uartServo_id:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_uart_servo_id error!---')

    def set_uart_servo_torque(self, enable):
        try:
            on = 1 if enable else 0
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x04, self.FUNC_UART_SERVO_TORQUE, on]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("uartServo_torque:", cmd)
            time.sleep(self.__delay_time)
        except Exception:
            print('---set_uart_servo_torque error!---')

    def set_uart_servo_ctrl_enable(self, enable):
        self.__arm_ctrl_enable = bool(enable)

    def set_uart_servo_angle_array(self, angle_s=[90, 90, 90, 90, 90, 180], run_time=500):
        try:
            if not self.__arm_ctrl_enable:
                return
            if 0 <= angle_s[0] <= 180 and 0 <= angle_s[1] <= 180 and 0 <= angle_s[2] <= 180 and \
                0 <= angle_s[3] <= 180 and 0 <= angle_s[4] <= 270 and 0 <= angle_s[5] <= 180:
                if run_time > 2000:
                    run_time = 2000
                if run_time < 0:
                    run_time = 0
                temp_val = [self.__arm_convert_value(i+1, angle_s[i]) for i in range(6)]
                values = [bytearray(struct.pack('h', v)) for v in temp_val]
                r_time = bytearray(struct.pack('h', int(run_time)))
                cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_ARM_CTRL] + \
                      [b for val in values for b in val] + [r_time[0], r_time[1]]
                cmd[2] = len(cmd) - 1
                checksum = sum(cmd, self.__COMPLEMENT) & 0xff
                cmd.append(checksum)
                self.ser.write(cmd)
                if self.__debug:
                    print("arm:", cmd)
                    print("value:", temp_val)
                time.sleep(self.__delay_time)
            else:
                print("angle_s input error!")
        except Exception:
            print('---set_uart_servo_angle_array error!---')

    def set_uart_servo_offset(self, servo_id):
        try:
            self.__arm_offset_id = 0xff
            self.__arm_offset_state = 0
            s_id = int(servo_id) & 0xff
            cmd = [self.__HEAD, self.__DEVICE_ID, 0, self.FUNC_ARM_OFFSET, s_id]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("uartServo_offset:", cmd)
            time.sleep(self.__delay_time)
            for _ in range(200):
                if self.__arm_offset_id == servo_id:
                    if self.__debug:
                        if self.__arm_offset_id == 0:
                            print("Arm Reset Offset Value")
                        else:
                            print("Arm Offset State:", self.__arm_offset_id, self.__arm_offset_state, _)
                    return self.__arm_offset_state
                time.sleep(.001)
            return self.__arm_offset_state
        except Exception:
            print('---set_uart_servo_offset error!---')

    def reset_flash_value(self):
        try:
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x04, self.FUNC_RESET_FLASH, 0x5F]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("flash:", cmd)
            time.sleep(self.__delay_time)
            time.sleep(.1)
        except Exception:
            print('---reset_flash_value error!---')

    def clear_auto_report_data(self):
        self.__battery_voltage = 0
        self.__vx, self.__vy, self.__vz = 0, 0, 0
        self.__ax, self.__ay, self.__az = 0, 0, 0
        self.__gx, self.__gy, self.__gz = 0, 0, 0
        self.__mx, self.__my, self.__mz = 0, 0, 0
        self.__yaw, self.__roll, self.__pitch = 0, 0, 0

    def get_uart_servo_value(self, servo_id):
        try:
            if servo_id < 1 or servo_id > 250:
                print("get servo id input error!")
                return
            self.__read_id = 0
            self.__read_val = 0
            self.__request_data(self.FUNC_UART_SERVO, int(servo_id) & 0xff)
            timeout = 30
            while timeout > 0:
                if self.__read_id > 0:
                    return self.__read_id, self.__read_val
                timeout -= 1
                time.sleep(.001)
            return -1, -1
        except Exception:
            print('---get_uart_servo_value error!---')
            return -2, -2

    def get_uart_servo_angle(self, s_id):
        try:
            angle = -1
            read_id, value = self.get_uart_servo_value(s_id)
            valid = [
                (s_id == 1 and read_id == 1 and 0 <= self.__arm_convert_angle(s_id, value) <= 180),
                (s_id == 2 and read_id == 2 and 0 <= self.__arm_convert_angle(s_id, value) <= 180),
                (s_id == 3 and read_id == 3 and 0 <= self.__arm_convert_angle(s_id, value) <= 180),
                (s_id == 4 and read_id == 4 and 0 <= self.__arm_convert_angle(s_id, value) <= 180),
                (s_id == 5 and read_id == 5 and 0 <= self.__arm_convert_angle(s_id, value) <= 270),
                (s_id == 6 and read_id == 6 and 0 <= self.__arm_convert_angle(s_id, value) <= 180)
            ]
            if any(valid):
                angle = self.__arm_convert_angle(s_id, value)
            else:
                if self.__debug:
                    print(f"read servo:{s_id} error or out of range!")
                angle = -1
            if self.__debug:
                print(f"request angle {s_id}: {read_id}, {value}")
            return angle
        except Exception:
            print('---get_uart_servo_angle error!---')
            return -2

    def get_uart_servo_angle_array(self):
        try:
            angle = [-1] * 6
            self.__read_arm = [-1] * 6
            self.__read_arm_ok = 0
            self.__request_data(self.FUNC_ARM_CTRL, 1)
            timeout = 30
            while timeout > 0:
                if self.__read_arm_ok == 1:
                    for i in range(6):
                        if self.__read_arm[i] > 0:
                            angle[i] = self.__arm_convert_angle(i+1, self.__read_arm[i])
                    if self.__debug:
                        print("angle_array:", 30-timeout, angle)
                    break
                timeout -= 1
                time.sleep(.001)
            return angle
        except Exception:
            print('---get_uart_servo_angle_array error!---')
            return [-2] * 6

    def get_yaw_roll_pitch(self, ToAngle=True):
        if ToAngle:
            RtA = 57.2957795
            roll = self.__roll * RtA
            pitch = self.__pitch * RtA
            yaw = self.__yaw * RtA
        else:
            roll, pitch, yaw = self.__roll, self.__pitch, self.__yaw
        return roll, pitch, yaw

    def get_battery_voltage(self):
        vol = self.__battery_voltage / 10.0
        return vol

    def get_motor_encoder(self):
        m1, m2, m3, m4 = self.__encoder_m1, self.__encoder_m2, self.__encoder_m3, self.__encoder_m4
        return m1, m2, m3, m4

    def get_version(self):
        if self.__version_H == 0:
            self.__request_data(self.FUNC_VERSION)
            for _ in range(20):
                if self.__version_H != 0:
                    val = self.__version_H * 1.0
                    self.__version = val + self.__version_L / 10.0
                    if self.__debug:
                        print(f"get_version:V{self.__version}, i:{_}")
                    return self.__version
                time.sleep(.001)
        else:
            return self.__version
        return -1