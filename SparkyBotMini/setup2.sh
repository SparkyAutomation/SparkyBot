#!/bin/bash

# Define the path to panel.conf
PANEL_CONF="$HOME/.config/lxqt/panel.conf"

# Define the path to SparkyBotMini.desktop
SPARKYBOT_DESKTOP="$HOME/SparkyBotMini.desktop"

# Check if panel.conf exists
if [ ! -f "$PANEL_CONF" ]; then
    echo "Error: panel.conf not found at $PANEL_CONF"
    exit 1
fi

# Find the current apps size
CURRENT_SIZE=$(grep -oP 'apps\\size=\K[0-9]+' "$PANEL_CONF")

# Check if the size was found
if [ -z "$CURRENT_SIZE" ]; then
    echo "Error: apps size not found in $PANEL_CONF"
    exit 1
fi

# Calculate the new size
NEW_SIZE=$((CURRENT_SIZE + 1))

# Define the new entry
NEW_ENTRY="apps\\$NEW_SIZE\\desktop=$SPARKYBOT_DESKTOP"

# Use sed to insert the new entry before the pattern and update the size
sed -i "/apps\\\\size=$NEW_SIZE/i $NEW_ENTRY" "$PANEL_CONF"
sed -i "s/apps\\\\size=$NEW_SIZE/apps\\\\size=$NEW_SIZE/" "$PANEL_CONF"

echo "New entry added as apps\\$NEW_SIZE\\desktop added."
