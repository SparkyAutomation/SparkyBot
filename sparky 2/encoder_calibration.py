'''
Place robot at 0 mark on a meter tape.
Run the code.
After it moves, measure how far it really moved (e.g. 0.5 meters).
Plug that number into measured_distance_m.
Run a few times and average the ticks_per_meter.

Ticks per meter:3190
'''

from Sparky_Packages import Sparky
import time

bot = Sparky(com="/dev/ttyUSB0", debug=True)
bot.create_receive_threading()
time.sleep(0.5)

# Step 1: Get initial encoder readings
initial_ticks = bot.get_motor_encoder()

# Step 2: Move forward with all wheels
speed = 50
move_time = 2.0  # seconds
print("Moving forward...")
bot.set_motor(speed, speed, speed, speed)
time.sleep(move_time)
bot.set_motor(0, 0, 0, 0)

# Step 3: Get encoder values after motion
final_ticks = bot.get_motor_encoder()
delta_ticks = [f - i for f, i in zip(final_ticks, initial_ticks)]
print("Encoder tick changes:", delta_ticks)

# Step 4: Compute average ticks
avg_ticks = sum([abs(t) for t in delta_ticks]) / 4.0

# Step 5: Replace with measured distance in meters
measured_distance_m = 1.70  # update based on ruler or tape
ticks_per_meter = avg_ticks / measured_distance_m

# Step 6: Show result
print(f"\n Calibration Results:")
print(f"  Avg encoder ticks: {avg_ticks:.2f}")
print(f"  Measured distance: {measured_distance_m} m")
print(f"  ➤ Ticks per meter: {ticks_per_meter:.2f}")
print(f"  ➤ Estimated distance from encoders: {avg_ticks / ticks_per_meter:.3f} m")
