#!/bin/bash

echo "1. Updating package list..."
sudo apt update

echo "2. Installing required system packages..."
sudo apt install -y python3-pip python3-dev build-essential

echo "3. Installing Python packages for RPLIDAR A1..."
pip3 install --break-system-packages rplidar matplotlib numpy

echo "4. Adding current user to the 'dialout' group for serial port access..."
sudo usermod -a -G dialout $USER

echo "✅ RPLIDAR dependencies installed successfully."
echo "5. Please reboot your Raspberry Pi to apply group changes:"
echo "    sudo reboot"
