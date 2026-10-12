#!/usr/bin/env python3
"""Install the pinned ble.sh dependency used for inline shell suggestions."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen

VERSION = "v0.4.0-devel3"
URL = (
    "https://github.com/akinomyoga/ble.sh/releases/download/"
    f"{VERSION}/ble-{VERSION[1:]}.tar.xz"
)
SHA256 = "c8612ee612bc6b10dbfd6e85c6cbdfd7caf152a12d1f9de22ea0a9d735b3080c"
ARCHIVE_ROOT = f"ble-{VERSION[1:]}"

SYSTEM_LOCATIONS = (
    Path("/usr/share/blesh/ble.sh"),
    Path("/usr/share/ble.sh/ble.sh"),
    Path("/usr/local/share/blesh/ble.sh"),
)


def user_ble_path(home: Path) -> Path:
    return home / ".local/share/blesh/ble.sh"


def find_ble_sh(home: Path) -> Path | None:
    candidates = (
        user_ble_path(home),
        *SYSTEM_LOCATIONS,
    )
    return next((path for path in candidates if path.is_file() and os.access(path, os.R_OK)), None)


def validate_archive(path: Path) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != SHA256:
        raise RuntimeError(f"ble.sh checksum mismatch: expected {SHA256}, got {digest}")

    with tarfile.open(path, "r:xz") as archive:
        members = archive.getmembers()
        if not members:
            raise RuntimeError("ble.sh archive is empty")
        for member in members:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != ARCHIVE_ROOT:
                raise RuntimeError(f"Unexpected path in ble.sh archive: {member.name}")
            if member.isdev() or member.issym() or member.islnk():
                raise RuntimeError(f"Unsafe entry in ble.sh archive: {member.name}")


def download(path: Path) -> None:
    request = Request(URL, headers={"User-Agent": "niri-clavis-setup/1.0"})
    with urlopen(request, timeout=45) as response, path.open("wb") as output:
        shutil.copyfileobj(response, output)


def verify_loaded_version(ble_sh: Path) -> str:
    result = subprocess.run(
        ["bash", str(ble_sh), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    version = result.stdout.strip()
    if "ble.sh" not in version:
        raise RuntimeError(f"Unexpected ble.sh version output from {ble_sh}: {version}")
    return version


def check(home: Path) -> None:
    ble_sh = find_ble_sh(home)
    if ble_sh is None:
        raise RuntimeError("ble.sh is not installed; run bash install.sh again")
    print(f"ble.sh is ready: {verify_loaded_version(ble_sh)} ({ble_sh})")


def install(home: Path) -> None:
    existing = find_ble_sh(home)
    if existing is not None:
        print(f"Using installed ble.sh: {verify_loaded_version(existing)} ({existing})")
        return

    target_dir = home / ".local/share/blesh"
    if target_dir.exists() and not user_ble_path(home).is_file():
        raise RuntimeError(
            f"Incomplete or custom installation at {target_dir}; move it aside and retry"
        )

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="niri-blesh-", dir=target_dir.parent) as temporary:
        temporary_path = Path(temporary)
        archive = temporary_path / "ble.tar.xz"
        download(archive)
        validate_archive(archive)
        staging = temporary_path / "stage"
        staging.mkdir()
        with tarfile.open(archive, "r:xz") as extracted:
            extracted.extractall(staging, filter="data")

        source = staging / ARCHIVE_ROOT
        if not (source / "ble.sh").is_file():
            raise RuntimeError("ble.sh archive did not contain ble.sh")
        if target_dir.exists():
            raise RuntimeError(f"ble.sh installation directory appeared during setup: {target_dir}")
        os.replace(source, target_dir)

    marker = target_dir / ".niri-clavis-blesh-version"
    marker.write_text(f"{VERSION}\nsha256:{SHA256}\n")
    print(f"Installed {verify_loaded_version(user_ble_path(home))} to {target_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify an existing installation")
    parser.add_argument("--dry-run", action="store_true", help="Validate without downloading")
    args = parser.parse_args()
    home = Path.home().resolve()

    try:
        if args.check:
            check(home)
        elif args.dry_run:
            existing = find_ble_sh(home)
            if existing:
                print(f"Would use installed ble.sh: {existing}")
            else:
                print(f"Would download pinned ble.sh {VERSION} from GitHub")
        else:
            install(home)
    except (OSError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"ble.sh installation failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
