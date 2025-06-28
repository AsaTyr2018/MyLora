#!/usr/bin/env bash
# Restart the MyLora service via systemd.
set -e
SERVICE="mylora.service"
# Stop service if running
if systemctl is-active --quiet "$SERVICE"; then
    systemctl stop "$SERVICE"
fi
# Start service
systemctl start "$SERVICE"
