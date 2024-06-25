################ Phase 4: Configure the desktop for LXQt ################

echo "##################################################################"
echo "########################## Phase 4 done ##########################"
sleep 2

script3_path="$HOME/config_desktop.sh"

# Remove script3 from crontab
crontab -l | grep -v "@reboot $script3_path" | crontab -

sudo reboot
