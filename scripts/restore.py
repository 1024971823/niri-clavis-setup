#!/usr/bin/env python3
"""Restore files and service enablement saved before the latest install."""

import json
import os
from pathlib import Path
import shutil
import subprocess

home = Path.home().resolve()
state = home / ".local/state/niri-clavis-setup"
latest = state / "latest-backup"
if not latest.is_file():
    raise SystemExit("No niri-clavis-setup backup was found")
backup = Path(latest.read_text().strip()).resolve()
if not backup.is_relative_to((state / "backups").resolve()) or not backup.is_dir():
    raise SystemExit("Backup path is invalid")
manifest = json.loads((backup / "manifest.json").read_text())

for relative, existed in manifest["files"].items():
    target = home / relative
    source = backup / relative
    if not target.is_relative_to(home) or not source.is_relative_to(backup):
        raise SystemExit("Unsafe backup path")
    if target.exists() or target.is_symlink():
        target.unlink()
    if existed:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, target)

subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
for name, enabled in manifest["services"].items():
    subprocess.run(["systemctl", "--user", "enable" if enabled else "disable", name], check=True)
print(f"Restored configuration from {backup}")
print("Log out and back in to apply the previous Niri session configuration.")
