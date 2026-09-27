#!/usr/bin/env python3
"""Install the versioned desktop configuration with a reversible backup."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def default_wallpaper(path: Path) -> None:
    """Create a small original gradient; no third-party image is redistributed."""
    width, height = 640, 360
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            shade = x / (width - 1) * 0.35 + y / (height - 1) * 0.65
            row.extend((int(19 + 28 * shade), int(24 + 32 * shade), int(42 + 56 * shade)))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def shell_escape(value: str) -> str:
    # KDL quoted string escaping is compatible for these ordinary absolute paths.
    if "\n" in value or "\r" in value:
        raise ValueError("Path contains a newline")
    return json.dumps(value, ensure_ascii=False)[1:-1]


def service_enabled(name: str) -> bool:
    return subprocess.run(["systemctl", "--user", "is-enabled", "--quiet", name]).returncode == 0


def library_path() -> str:
    clavis = Path("/usr/lib/qt6/qml/Clavis")
    m3shapes = Path("/usr/lib/qt6/qml/M3Shapes")
    if not clavis.is_dir() or not m3shapes.is_dir():
        raise RuntimeError("Clavis or M3Shapes QML modules are missing; install packages first")
    modules = sorted(
        path for path in clavis.iterdir() if path.is_dir() and list(path.glob("libClavis*.so"))
    )
    if not modules:
        raise RuntimeError("No Clavis native modules were found")
    path = os.pathsep.join([str(m3shapes), *(str(module) for module in modules)])
    environment = dict(os.environ, LD_LIBRARY_PATH=path)
    for plugin in [*clavis.glob("*/libClavis*plugin.so"), *m3shapes.glob("*plugin.so")]:
        result = subprocess.run(["ldd", str(plugin)], env=environment, capture_output=True, text=True)
        if result.returncode or "not found" in result.stdout:
            raise RuntimeError(f"Unresolved native dependency in {plugin}: {result.stdout}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wallpaper", type=Path)
    parser.add_argument("--pet-start", type=Path, help="Optional local pet launcher; files are not bundled")
    parser.add_argument("--pet-process-match", help="Optional pkill -f pattern for Super+Alt+P")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    home = Path.home().resolve()
    wallpaper = args.wallpaper or home / ".config/niri/wallpaper.jpg"
    wallpaper = wallpaper.expanduser().resolve()
    if args.wallpaper and not wallpaper.is_file():
        raise FileNotFoundError(wallpaper)
    if not wallpaper.is_file():
        wallpaper = home / ".local/share/niri-clavis-setup/default-wallpaper.png"
    if args.pet_start and not args.pet_start.expanduser().is_file():
        raise FileNotFoundError(args.pet_start)
    if args.pet_process_match and not args.pet_start:
        raise ValueError("--pet-process-match requires --pet-start")

    pet_start = "// No pet launcher was selected."
    pet_kill = "    // No pet process was selected."
    if args.pet_start:
        pet_start = f'spawn-at-startup "{shell_escape(str(args.pet_start.expanduser().resolve()))}"'
    if args.pet_process_match:
        pattern = shell_escape(args.pet_process_match)
        pet_kill = (
            '    Super+Alt+P hotkey-overlay-title="关闭桌面宠物" '
            f'{{ spawn "pkill" "-f" "{pattern}"; }}'
        )

    contents: dict[str, bytes] = {}
    niri_template = (ROOT / "config/niri/config.kdl.tpl").read_text()
    niri = (niri_template.replace("@HOME@", shell_escape(str(home)))
            .replace("@WALLPAPER@", shell_escape(str(wallpaper)))
            .replace("@PET_START_LINE@", pet_start)
            .replace("@PET_KILL_LINE@", pet_kill))
    if "@PET_" in niri or "@HOME@" in niri or "@WALLPAPER@" in niri:
        raise RuntimeError("Unexpanded Niri template token")
    contents[".config/niri/config.kdl"] = niri.encode()
    for name in ("fuzzel-zh.ini", "clavis/effects.kdl", "clavis/cursor.kdl"):
        contents[f".config/niri/{name}"] = (ROOT / "config/niri" / name).read_bytes()

    for template in (ROOT / "config/clavis").glob("*.json"):
        value = json.loads(template.read_text())
        serialized = json.dumps(value, ensure_ascii=False, indent=2)
        serialized = serialized.replace("@HOME@", str(home)).replace("@WALLPAPER@", str(wallpaper))
        json.loads(serialized)
        contents[f".config/clavis/{template.name}"] = (serialized + "\n").encode()

    modules = library_path()
    contents[".config/systemd/user/clavis-shell.service.d/10-library-path.conf"] = (
        f'[Service]\nEnvironment="LD_LIBRARY_PATH={modules}"\n'.encode()
    )
    legacy_clipboard = home / ".config/systemd/user/clavis-clipboard.service"
    packaged_clipboard = Path("/usr/lib/systemd/user/clavis-clipboard.service")
    remove_legacy_clipboard = legacy_clipboard.exists()
    if remove_legacy_clipboard and legacy_clipboard.read_bytes() != packaged_clipboard.read_bytes():
        raise RuntimeError(
            f"Custom clipboard unit at {legacy_clipboard}; move it aside before installing"
        )

    with tempfile.TemporaryDirectory(prefix="niri-clavis-check-") as temporary:
        candidate_root = Path(temporary)
        for relative, data in contents.items():
            candidate = candidate_root / relative
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_bytes(data)
        subprocess.run(
            ["niri", "validate", "-c", str(candidate_root / ".config/niri/config.kdl")],
            check=True,
        )

    print(f"Validated Niri configuration and native plugins ({len(contents)} files)")
    if args.dry_run:
        print(f"Dry run: would use wallpaper {wallpaper}")
        return

    if not wallpaper.exists():
        default_wallpaper(wallpaper)
    (home / "Pictures/Screenshots").mkdir(parents=True, exist_ok=True)

    state = home / ".local/state/niri-clavis-setup"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = state / "backups" / stamp
    backup.mkdir(parents=True)
    manifest = {
        "files": {},
        "services": {
            name: service_enabled(name)
            for name in ("clavis-shell.service", "clavis-clipboard.service")
        },
    }
    for relative in contents:
        target = home / relative
        existed = target.exists() or target.is_symlink()
        manifest["files"][relative] = existed
        if existed:
            old = backup / relative
            old.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                old.symlink_to(os.readlink(target))
            else:
                shutil.copy2(target, old)
    if remove_legacy_clipboard:
        relative = ".config/systemd/user/clavis-clipboard.service"
        old = backup / relative
        old.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_clipboard, old)
        manifest["files"][relative] = True

    (backup / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (state / "latest-backup").write_text(str(backup) + "\n")
    for relative, data in contents.items():
        target = home / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            handle.write(data)
            temp_path = Path(handle.name)
        temp_path.chmod(0o600 if relative.startswith(".config/clavis/") else 0o644)
        os.replace(temp_path, target)
    if remove_legacy_clipboard:
        legacy_clipboard.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "--user", "enable", "clavis-shell.service", "clavis-clipboard.service"],
        check=True,
    )
    print(f"Installed configuration; backup: {backup}")
    print("Log out and choose Niri at the login screen to activate the session.")


if __name__ == "__main__":
    main()
