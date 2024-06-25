#!/bin/bash

################ Phase 2: Install desktop environment ################
echo "##################################################################"
echo "########################## Phase 2 done ##########################"
sleep 2

script2_path="$HOME/install_desktop.sh"
script3_path="$HOME/config_desktop.sh"

# Add script3 to crontab and remove script2
(crontab -l 2>/dev/null; echo "@reboot $script3_path") | crontab -
(crontab -l | grep -v "@reboot $script2_path") | crontab -

sudo reboot
