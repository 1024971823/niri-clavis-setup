#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$root/scripts/install_media.py" --restore
exec python3 "$root/scripts/restore.py"
