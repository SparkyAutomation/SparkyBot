import subprocess
import re
import time
import math

# Path to ultra_simple binary and serial port config
ULTRA_SIMPLE_PATH = './ultra_simple'
PORT = '/dev/ttyUSB0'
BAUD = '460800'

pattern = re.compile(r'theta:\s*([0-9.]+)\s+Dist:\s*([0-9.]+)')

proc = subprocess.Popen(
    [ULTRA_SIMPLE_PATH, '--channel', '--serial', PORT, BAUD],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

print("Reading LIDAR data as fast as possible (no plot). Ctrl+C to stop.")

count = 0
start_time = time.time()

try:
    for line in proc.stdout:
        match = pattern.search(line)
        if match:
            angle = float(match.group(1))
            distance = float(match.group(2))
            # Example filter
            if 0 < distance < 4000:
                count += 1

        if count % 500 == 0 and count > 0:
            elapsed = time.time() - start_time
            print(f"{count} points in {elapsed:.2f}s → {count/elapsed:.1f} pts/sec")

except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    proc.terminate()
    proc.wait()
    print("✅ Done.")
