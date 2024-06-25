#!/bin/bash

# 1. Download shell scripts
sudo wget "https://raw.githubusercontent.com/MechatronicsWhiz/SparkyBot/main/sandbox/update_upgrade.sh"
sudo wget "https://raw.githubusercontent.com/MechatronicsWhiz/SparkyBot/main/sandbox/install_desktop.sh"
sudo wget "https://raw.githubusercontent.com/MechatronicsWhiz/SparkyBot/main/sandbox/config_desktop.sh"
sudo chmod +x update_upgrade.sh
sudo chmod +x install_desktop.sh
sudo chmod +x config_desktop.sh

# 2. Add a script to crontab
add_to_crontab() {
    local script_path=$1
    (crontab -l; echo "@reboot $script_path") | crontab -
}

# 3. Add script1 to crontab
script1_path="$HOME/update_upgrade.sh" 

# Add script1 to crontab
add_to_crontab $SCRIPT1

sudo reboot
