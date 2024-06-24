PANEL_CONF="$HOME/.config/lxqt/panel.conf"
DESKTOP_FILE="/home/sparky/SparkyBotMini/SparkyBotMini.desktop"

# Ensure the file exists before making changes
if [ -f "$PANEL_CONF" ]; then
    # Check if the entry already exists to avoid duplicates
    if ! grep -q "apps\\1\\desktop=$DESKTOP_FILE" "$PANEL_CONF"; then
        # Append the new entry to [quick launch] section
        echo -e "\n[quick launch]" >> "$PANEL_CONF"
        echo "alignment=Left" >> "$PANEL_CONF"
        echo "apps\\1\\desktop=$DESKTOP_FILE" >> "$PANEL_CONF"
        echo "apps\\size=1" >> "$PANEL_CONF"
        echo "type=quicklaunch" >> "$PANEL_CONF"
        echo "Panel configuration updated successfully."
    else
        echo "Entry already exists in panel.conf."
    fi
else
    echo "Panel configuration file not found: $PANEL_CONF"
fi
