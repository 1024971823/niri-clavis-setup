#!/usr/bin/env python3
"""Install the Bash completion loader when the system package is unavailable."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

SYSTEM_LOADER = Path("/usr/share/bash-completion/bash_completion")
LOCAL_ROOT = Path.home() / ".local/share/niri-clavis-setup/bash-completion"
LOCAL_LOADER = LOCAL_ROOT / "usr/share/bash-completion/bash_completion"
PACKAGE_URL = "https://archlinux.org/packages/extra/any/bash-completion/download"


def usable_loaders() -> list[Path]:
    return [path for path in (SYSTEM_LOADER, LOCAL_LOADER) if path.is_file()]


def download_package(destination: Path) -> None:
    request = urllib.request.Request(
        PACKAGE_URL,
        headers={"User-Agent": "niri-clavis-setup/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                with destination.open("wb") as output:
                    shutil.copyfileobj(response, output)
            return
        except Exception as error:  # Network errors vary across Python versions.
            last_error = error
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Could not download bash-completion: {last_error}")


def install_fallback() -> None:
    if shutil.which("bsdtar") is None:
        raise RuntimeError("bsdtar is required to unpack the local bash-completion fallback")
    if LOCAL_ROOT.exists():
        raise RuntimeError(f"Incomplete local bash-completion directory exists: {LOCAL_ROOT}")

    LOCAL_ROOT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bash-completion-", dir=LOCAL_ROOT.parent) as temporary:
        staging = Path(temporary)
        package = staging / "bash-completion.pkg.tar.zst"
        extracted = staging / "root"
        extracted.mkdir()
        download_package(package)
        subprocess.run(["bsdtar", "-xf", str(package), "-C", str(extracted)], check=True)
        loader = extracted / "usr/share/bash-completion/bash_completion"
        if not loader.is_file():
            raise RuntimeError("Downloaded package did not contain the Bash completion loader")
        os.replace(extracted, LOCAL_ROOT)
    if not LOCAL_LOADER.is_file():
        raise RuntimeError("Local bash-completion installation is incomplete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    loaders = usable_loaders()
    if loaders:
        print(f"Using Bash completion loader: {loaders[0]}")
        return
    if args.check:
        raise SystemExit("Bash completion loader is missing")
    if args.dry_run:
        print("Would install a user-local Bash completion loader")
        return

    install_fallback()
    print(f"Installed Bash completion loader: {LOCAL_LOADER}")


if __name__ == "__main__":
    main()
