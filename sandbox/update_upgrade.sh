#!/bin/bash
################ Phase 1: Update and upgrade ################
sudo apt-get update
sudo apt-get upgrade -y

echo "##################################################################"
echo "########################## Phase 1 done ##########################"
sleep 2

script1_path="$HOME/update_upgrade.sh"
script2_path="$HOME/install_desktop.sh"

# Add script2 to crontab and remove script1
(crontab -l 2>/dev/null; echo "@reboot $script2_path") | crontab -
(crontab -l | grep -v "@reboot $script1_path") | crontab -

sudo reboot
