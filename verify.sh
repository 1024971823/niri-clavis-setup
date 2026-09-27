#!/usr/bin/env bash
set -euo pipefail

niri validate -c "$HOME/.config/niri/config.kdl"
systemctl --user is-enabled --quiet clavis-shell.service
systemctl --user is-enabled --quiet clavis-clipboard.service

library_path=$(systemctl --user show clavis-shell.service -p Environment --value | grep -o 'LD_LIBRARY_PATH=[^ ]*' | cut -d = -f 2-)
[[ -n $library_path ]] || { echo 'Clavis library path is missing.' >&2; exit 1; }
for plugin in /usr/lib/qt6/qml/Clavis/*/libClavis*plugin.so /usr/lib/qt6/qml/M3Shapes/*plugin.so; do
    if LD_LIBRARY_PATH=$library_path ldd "$plugin" | grep -q 'not found'; then
        echo "Unresolved library: $plugin" >&2
        exit 1
    fi
done

if systemctl --user is-active --quiet niri.service; then
    systemctl --user is-active --quiet clavis-shell.service || {
        echo 'Clavis service is not running in this Niri session.' >&2
        exit 1
    }
    niri msg layers | grep -q 'clavis-shell-bar'
    niri msg layers | grep -q 'clavis-wallpaper'
    echo 'Niri and Clavis are running with bar and wallpaper layers.'
else
    echo 'Configuration and libraries are valid. Enter Niri to check the live desktop.'
fi
