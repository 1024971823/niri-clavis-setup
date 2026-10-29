#!/usr/bin/env python3
"""Install portable QQ Music artwork and exclusive Clavis notifications."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "clavis-qqmusic-artwork.service"
MANAGER = Path("Services/MediaManager.qml")
VIEWS = ("Modules/Keystone/MediaContent/MediaContent.qml",
         "Modules/Keystone/LyricsContent/LyricsContent.qml",
         "Modules/Lock/Cards/MediaCard.qml")


def xdg(name, fallback):
    value = os.environ.get(name, "")
    return Path(value) if Path(value).is_absolute() else Path.home() / fallback


def locations():
    return (xdg("XDG_CONFIG_HOME", ".config"), xdg("XDG_DATA_HOME", ".local/share"),
            xdg("XDG_STATE_HOME", ".local/state") / "niri-clavis-setup/media")


def discover_shell(config):
    candidates = [config / "quickshell/clavis"]
    # Honor a running Clavis instance's actual configuration location.
    if shutil.which("qs"):
        result = subprocess.run(["qs", "list", "--all"], capture_output=True, text=True)
        candidates += [Path(line.split("Config path:", 1)[1].strip()).parent
                       for line in result.stdout.splitlines() if "Config path:" in line]
    candidates += [Path(p) / "quickshell/clavis" for p in
                   os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":") if p.startswith("/")]
    for candidate in candidates:
        if (candidate / "shell.qml").is_file() and (candidate / MANAGER).is_file():
            return candidate
    raise RuntimeError("Clavis shell was not found in the running session or XDG config directories")


def patch_qml(source):
    """Fail before writes on incompatible upstream layouts; safe to run repeatedly."""
    result = {}
    text = (source / MANAGER).read_text()
    if "function artworkFor(player)" not in text:
        for statement in ("import Quickshell.Io", "import qs.Common"):
            if statement not in text:
                text = text.replace("import QtQuick", "import QtQuick\n" + statement, 1)
        anchor = "    id: root\n"
        if anchor not in text:
            raise RuntimeError("Unsupported Clavis MediaManager layout")
        snippet = (ROOT / "config/media/qqmusic-manager.qml.inc").read_text()
        text = text.replace(anchor, anchor + "\n" + snippet, 1)
    if 'return "QQ 音乐";' not in text:
        anchor = "        let name = player.identity.toLowerCase();"
        if anchor not in text:
            raise RuntimeError("Unsupported Clavis player identity layout")
        text = text.replace(anchor, '        if (root.qqMusicArtwork[player.dbusName])\n'
                            '            return "QQ 音乐";\n' + anchor, 1)
    result[MANAGER] = text.encode()
    for relative in VIEWS:
        text = (source / relative).read_text()
        expression = ('isActive ? MediaManager.artworkFor(MediaManager.active) : ""'
                      if relative.endswith("MediaContent.qml") else "MediaManager.artworkFor(player)")
        if "property string artUrl: " + expression not in text:
            pattern = r'(property string artUrl:\s*)[^\n]*(?:\n\s*)?""(?=\s*\n)'
            # Only replace the known upstream trackArtUrl property.
            match = re.search(pattern, text)
            if not match or "trackArtUrl" not in match.group():
                raise RuntimeError(f"Unsupported artwork property in {relative}")
            text = text[:match.start()] + match.group(1) + expression + text[match.end():]
        result[Path(relative)] = text.encode()
    return result


def systemctl(*args, check=True):
    return subprocess.run(["systemctl", "--user", *args], capture_output=True,
                          text=True, check=check)


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.chmod(0o644)
    temporary.replace(path)


def restore(state):
    pointer = state / "latest-backup"
    if not pointer.exists():
        print("No media integration backup to restore")
        return
    backup = Path(pointer.read_text().strip())
    if not backup.resolve().is_relative_to((state / "backups").resolve()):
        raise RuntimeError("Invalid media backup path")
    manifest = json.loads((backup / "manifest.json").read_text())
    systemctl("stop", SERVICE, check=False)
    for item in reversed(manifest["files"]):
        target = Path(item["target"])
        target.unlink(missing_ok=True)
        if item["kind"] == "symlink":
            target.symlink_to(item["link"])
        elif item["kind"] == "file":
            shutil.copy2(backup / item["backup"], target)
    if manifest["overlay"]:
        shell = Path(manifest["shell"])
        shutil.rmtree(shell)
        if manifest["shellLink"]:
            shell.symlink_to(manifest["shellLink"])
    systemctl("daemon-reload")
    clavis_active = systemctl("is-active", "clavis-shell.service", check=False).returncode == 0
    if manifest["active"]["mako.service"] and clavis_active:
        systemctl("stop", "clavis-shell.service")
        systemctl("start", "mako.service")
        systemctl("start", "clavis-shell.service")
    elif clavis_active:
        systemctl("restart", "clavis-shell.service")
    for name, active in manifest["active"].items():
        systemctl("start" if active else "stop", name, check=False)
    pointer.unlink()
    print(f"Restored media integration backup: {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--no-restart", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.restore:
        parser.error("--dry-run and --restore cannot be combined")
    config, data, state = locations()
    if args.restore:
        restore(state)
        return
    # Check the actual interpreter used by the service before making changes.
    subprocess.run(["/usr/bin/python3", "-c", "from gi.repository import Gio, GLib"], check=True)
    source = discover_shell(config)
    patched = patch_qml(source)
    shell = config / "quickshell/clavis"
    if shell.exists() and not (shell / "shell.qml").is_file():
        raise RuntimeError(f"Existing non-shell directory needs manual review: {shell}")
    overlay = not shell.exists() or shell.is_symlink()
    if not overlay:
        for relative in patched:
            if not (shell / relative).parent.resolve().is_relative_to(shell.resolve()):
                raise RuntimeError("Clavis QML directories link outside the user shell; create a local copy first")
    script = data / "niri-clavis-setup/qqmusic-artwork.py"
    unit_dir = config / "systemd/user"
    # systemd expands percent specifiers even inside quotes.
    escaped_script = json.dumps(str(script), ensure_ascii=False).replace("%", "%%").replace("$", "$$")
    unit = (ROOT / "config/systemd/clavis-qqmusic-artwork.service.in").read_text()
    files = {shell / name: content for name, content in patched.items()}
    files[script] = (ROOT / "config/media/qqmusic-artwork.py").read_bytes()
    files[unit_dir / SERVICE] = unit.replace("@SCRIPT@", escaped_script).encode()
    links = {unit_dir / "mako.service": "/dev/null",
             unit_dir / "clavis-shell.service.wants" / SERVICE: "../" + SERVICE}
    print(f"Clavis discovered: {source}; user overlay: {shell}")
    print(f"QQ Music is detected via MPRIS and its process identity; no install path or account config required")
    if args.dry_run:
        print(f"Validated {len(files)} files and notification-service integration; no changes made")
        return
    backup = state / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True)
    manifest = {"files": [], "overlay": overlay, "shell": str(shell),
                "shellLink": os.readlink(shell) if shell.is_symlink() else None,
                "active": {name: systemctl("is-active", name, check=False).returncode == 0
                           for name in (SERVICE, "mako.service")}}
    for target in [*files, *links]:
        if overlay and target.is_relative_to(shell):
            continue
        item = {"target": str(target), "kind": "absent"}
        if target.is_symlink():
            item.update(kind="symlink", link=os.readlink(target))
        elif target.exists():
            name = str(len(manifest["files"]))
            shutil.copy2(target, backup / name)
            item.update(kind="file", backup=name)
        manifest["files"].append(item)
    atomic_write(backup / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    atomic_write(state / "latest-backup", (str(backup) + "\n").encode())
    if overlay:
        shell.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=shell.parent) as temporary:
            tree = Path(temporary) / "clavis"
            # Materialize linked directories so patches cannot reach system packages.
            shutil.copytree(source, tree, symlinks=False)
            shell.unlink(missing_ok=True)
            tree.replace(shell)
    for path, content in files.items():
        atomic_write(path, content)
    for path, link in links.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        path.symlink_to(link)
    systemctl("stop", "mako.service", check=False)
    systemctl("daemon-reload")
    if not args.no_restart and systemctl("is-active", "clavis-shell.service", check=False).returncode == 0:
        systemctl("restart", "clavis-shell.service")
        systemctl("restart", SERVICE)
    print(f"Installed. Backup: {backup}")


if __name__ == "__main__":
    main()
