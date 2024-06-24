#!/bin/bash

# Define the path to the panel.conf file
panel_conf="/home/sparky/.config/lxqt/panel.conf"
# Define the path to SparkyBotMini.desktop
SPARKYBOT_DESKTOP="/home/sparky/SparkyBotMini.desktop"


# Count the number of existing apps in quicklaunch
SIZE=$(grep -oP 'apps\\\d+' "$PANEL_CONF" | wc -l)
NEXT_INDEX=$((SIZE + 1))

# Add SparkyBotMini.desktop to panel.conf
echo "apps\\$NEXT_INDEX\\desktop=$SPARKYBOT_DESKTOP" >> "$PANEL_CONF"
echo "apps\\size=$((SIZE + 1))" >> "$PANEL_CONF"

echo "App added to panel"
