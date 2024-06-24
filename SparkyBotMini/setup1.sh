#!/bin/bash

# Define the path to panel.conf
PANEL_CONF="/home/sparky/.config/lxqt/panel.conf"  # Replace with the actual path to panel.conf

# Define the path to SparkyBotMini.desktop
SPARKYBOT_DESKTOP="/home/sparky/SparkyBotMini.desktop"

# Check if panel.conf exists
if [ ! -f "$PANEL_CONF" ]; then
    echo "Error: panel.conf not found at $PANEL_CONF"
    exit 1
fi

# Count the number of existing apps in quicklaunch
SIZE=$(grep -oP 'apps\\[0-9]+' "$PANEL_CONF" | wc -l)
NEXT_INDEX=$((SIZE + 1))

# Add SparkyBotMini.desktop after the existing apps in panel.conf
echo "apps\\$NEXT_INDEX\\desktop=$SPARKYBOT_DESKTOP" >> "$PANEL_CONF"

# Update apps\size to reflect the new total number of apps
echo "apps\\size=$((SIZE + 1))" >> "$PANEL_CONF"

echo "App added to panel"
