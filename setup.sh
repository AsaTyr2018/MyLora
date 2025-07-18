#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/AsaTyr2018/MyLora.git"
INSTALL_DIR="/opt/MyLora"
SERVICE_FILE="/etc/systemd/system/mylora.service"
VENV_DIR="$INSTALL_DIR/venv"

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "This script must be run as root" >&2
        exit 1
    fi
}

clone_repo() {
    tmpdir="$HOME/MyLora"
    rm -rf "$tmpdir"
    git clone "$REPO_URL" "$tmpdir"
    rm -rf "$INSTALL_DIR"
    mv "$tmpdir" "$INSTALL_DIR"
    chown -R root:root "$INSTALL_DIR"
}

setup_venv() {
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
}

create_service() {
    cat > "$SERVICE_FILE" <<SERVICE
[Unit]
Description=LoRA database web interface
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
    systemctl daemon-reload
    systemctl enable mylora.service
}

install_app() {
    clone_repo
    setup_venv
    create_service
    systemctl start mylora.service
    echo "MyLora installed in $INSTALL_DIR"
}

update_app() {
    if [[ ! -d $INSTALL_DIR ]]; then
        echo "MyLora is not installed" >&2
        exit 1
    fi
    git -C "$INSTALL_DIR" pull
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    systemctl restart mylora.service
    echo "MyLora updated"
}

uninstall_app() {
    systemctl stop mylora.service || true
    systemctl disable mylora.service || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    rm -rf "$INSTALL_DIR"
    echo "MyLora removed"
}

case "$1" in
    install)
        check_root
        install_app
        ;;
    update)
        check_root
        update_app
        ;;
    uninstall)
        check_root
        uninstall_app
        ;;
    *)
        echo "Usage: $0 {install|update|uninstall}"
        exit 1
        ;;
 esac

