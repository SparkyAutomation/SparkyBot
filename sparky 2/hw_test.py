from Sparky_Packages import Sparky
import time

bot = Sparky(com="/dev/ttyUSB0", debug = True)
#bot.set_auto_report_state(True)         # Make sure the MCU is sending sensor data
bot.create_receive_threading()          # Start the receive thread to parse incoming data
time.sleep(0.5)                         # Give it some time to fill sensor values


print("Motor test")
bot.set_motor(50, 0, 0, 0)
time.sleep(0.5)                        
bot.set_motor(0, 50, 0, 0)
time.sleep(0.5)
bot.set_motor(0, 0, 50, 0)
time.sleep(0.5)
bot.set_motor(0, 0, 0, 50)
time.sleep(0.5)
bot.set_motor(0, 0, 0, 0)

print("battery: ", bot.get_battery_voltage())
print("motor_encoder: ", bot.get_motor_encoder())
print("yaw_roll_pitch: ", bot.get_yaw_roll_pitch())
print("version: ", bot.get_version())

print("Speaker test")
bot.set_beep(100)

print("LED test")
bot.set_led(0xFF, 255, 0, 0)
time.sleep(1)
bot.set_led_pattern(6, 5, 3)
time.sleep(5)
bot.set_led_pattern(0, 5, 3)