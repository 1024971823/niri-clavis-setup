#!/usr/bin/env bash
set -euo pipefail

# Arch x86_64. Run as the desktop user; sudo is used only for distribution packages.
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
release=v2026.9.25
installer_sha=967a0ee90529f6f95a313380fba60a45cd762ce751aa210fb9cb9faf08fb8e86
installer_asset=587584822
config_only=false
dry_run=false
wallpaper=''
pet_start=''
pet_process_match=''

usage() {
    cat <<'EOF'
Usage: ./install.sh [--config-only] [--dry-run] [--wallpaper FILE]
                    [--pet-start FILE] [--pet-process-match PATTERN]

Installs the pinned Clavis release and dependencies, then applies this Niri setup.
--config-only reuses already installed packages. --dry-run validates configuration
without changing files or packages.
EOF
}

while (($#)); do
    case $1 in
        --config-only) config_only=true; shift ;;
        --dry-run) dry_run=true; config_only=true; shift ;;
        --wallpaper|--pet-start|--pet-process-match)
            (($# >= 2)) || { usage >&2; exit 2; }
            case $1 in
                --wallpaper) wallpaper=$2 ;;
                --pet-start) pet_start=$2 ;;
                --pet-process-match) pet_process_match=$2 ;;
            esac
            shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

[[ $(uname -m) == x86_64 && -f /etc/arch-release ]] || {
    echo 'This setup supports Arch-compatible x86_64 systems.' >&2; exit 1;
}
[[ $EUID != 0 ]] || { echo 'Run as your desktop user, not root.' >&2; exit 1; }
for command in curl sha256sum systemctl; do
    command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
if $config_only; then
    for command in python3 niri; do
        command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
    done
fi

if ! $config_only; then
    command -v sudo >/dev/null || { echo 'sudo is required for package installation.' >&2; exit 1; }
    temporary=$(mktemp -d)
    trap 'rm -rf -- "$temporary"' EXIT
    installer="$temporary/install-arch.sh"
    url="https://github.com/StatIndet/quickshell/releases/download/$release/install-arch.sh"
    if ! curl -4 -fLsS --retry 3 --connect-timeout 10 --max-time 90 "$url" -o "$installer"; then
        echo 'Release download failed; trying the GitHub release asset API.' >&2
        curl -4 -fLsS --retry 3 --connect-timeout 10 --max-time 90 \
            -H 'Accept: application/octet-stream' \
            "https://api.github.com/repos/StatIndet/quickshell/releases/assets/$installer_asset" \
            -o "$installer"
    fi
    (cd "$temporary" && printf '%s  install-arch.sh\n' "$installer_sha" | sha256sum --check --status) || {
        echo 'The upstream installer checksum did not match.' >&2; exit 1;
    }

    # The pinned upstream installer uses a pacman -Qp option unsupported by
    # pacman 7.1. The shim affects only that read-only package-name lookup.
    mkdir "$temporary/bin"
    cat > "$temporary/bin/pacman" <<'SH'
#!/bin/sh
if [ "$#" -eq 4 ] && [ "$1" = '-Qp' ] && [ "$2" = '--print-format' ] && [ "$3" = '%n' ]; then
    /usr/bin/pacman -Qp "$4" | cut -d ' ' -f 1
else
    exec /usr/bin/pacman "$@"
fi
SH
    chmod 700 "$temporary/bin/pacman"
    if ! PATH="$temporary/bin:$PATH" bash "$installer" --non-interactive \
        --keyboard-access=no --power-access=no \
        --enable-shell=no --enable-clipboard=no --start-now=no; then
        # An old user service override can make upstream diagnostics return 1
        # after the packages have installed. The configuration step handles an
        # identical old clipboard unit; do not continue after a package failure.
        for package in clavis-shell key-cli quickshell qt6-m3shapes-git; do
            pacman -Q "$package" >/dev/null || {
                echo "Upstream installation failed before $package was installed." >&2
                exit 1
            }
        done
        pacman -T 'clavis-shell>=2026.9.25' 'key-cli>=2026.9.25' >/dev/null || {
            echo 'Installed Clavis or key-cli is older than the pinned release.' >&2
            exit 1
        }
        echo 'Upstream diagnostics reported a conflict; installed packages are present.' >&2
    fi

    sudo pacman -S --needed --noconfirm \
        alacritty fcitx5 fuzzel polkit-kde-agent \
        swaybg swayidle swaylock playerctl brightnessctl
fi

options=()
[[ -z $wallpaper ]] || options+=(--wallpaper "$wallpaper")
[[ -z $pet_start ]] || options+=(--pet-start "$pet_start")
[[ -z $pet_process_match ]] || options+=(--pet-process-match "$pet_process_match")
$dry_run && options+=(--dry-run)
python3 "$root/scripts/apply_config.py" "${options[@]}"
