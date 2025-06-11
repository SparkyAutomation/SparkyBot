#!/bin/bash
set -e

echo "=== Updating system package list ==="
sudo apt-get update

echo "=== Installing required system Python packages ==="
sudo apt-get install -y python3-opencv python3-rpi.gpio python3-smbus2 i2c-tools

echo "=== Enabling I2C interface (if not already enabled) ==="
sudo raspi-config nonint do_i2c 0

echo "=== Done installing requirements ==="
echo "If this is your first time enabling I2C, reboot your Raspberry Pi:"
echo "    sudo reboot"
echo ""
echo "To test, open Python 3 and run:"
echo "    import cv2; import RPi.GPIO; import smbus2; print('All system packages imported successfully.')"
