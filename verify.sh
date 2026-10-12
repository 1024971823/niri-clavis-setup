#!/usr/bin/env bash
set -euo pipefail

niri validate -c "$HOME/.config/niri/config.kdl"
python3 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path.home().joinpath(".config/alacritty/alacritty.toml").read_text())'
command -v tmux >/dev/null
tmux -f "$HOME/.config/tmux/tmux.conf" -L niri-clavis-verify new-session -d
[[ $(tmux -L niri-clavis-verify show -gv status) == 2 ]]
grep -q 'status-format\[0\].*#\[fill=#fff8f5' <(tmux -L niri-clavis-verify show -g status-format)
grep -q 'status-format\[1\].*status-left' <(tmux -L niri-clavis-verify show -g status-format)
tmux -L niri-clavis-verify kill-server
bash -n "$HOME/.local/share/niri-clavis-setup/bash-prompt.sh"
bash -n "$HOME/.local/share/niri-clavis-setup/cd-menu.sh"
grep -q '󰣇' "$HOME/.local/share/niri-clavis-setup/bash-prompt.sh"
grep -q '__niri_git_prompt' "$HOME/.local/share/niri-clavis-setup/bash-prompt.sh"
PROMPT_SCRIPT="$HOME/.local/share/niri-clavis-setup/bash-prompt.sh" python3 - <<'PY'
import os
from pathlib import Path
import subprocess
import tempfile

prompt_script = os.environ['PROMPT_SCRIPT']
with tempfile.TemporaryDirectory(prefix='niri-prompt-check-') as fixture:
    repo = Path(fixture)
    subprocess.run(['git', 'init', '-q', '-b', 'main'], cwd=repo, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Prompt Check'], cwd=repo, check=True)
    subprocess.run(
        ['git', 'config', 'user.email', 'prompt-check@example.invalid'],
        cwd=repo,
        check=True,
    )
    (repo / 'tracked').write_text('base\n')
    (repo / 'staged').write_text('base\n')
    subprocess.run(['git', 'add', 'tracked', 'staged'], cwd=repo, check=True)
    subprocess.run(['git', 'commit', '-qm', 'base'], cwd=repo, check=True)
    with (repo / 'tracked').open('a') as handle:
        handle.write('modified\n')
    with (repo / 'staged').open('a') as handle:
        handle.write('staged\n')
    subprocess.run(['git', 'add', 'staged'], cwd=repo, check=True)
    (repo / 'untracked').write_text('new\n')
    result = subprocess.run(
        [
            'bash',
            '--noprofile',
            '--norc',
            '-c',
            'source "$1"; cd "$2"; __niri_git_prompt',
            '_',
            prompt_script,
            str(repo),
        ],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    if result != 'main +1 ~1 ?1':
        raise SystemExit(f'Unexpected Git prompt summary: {result}')
PY
command -v fzf >/dev/null
bash -ic 'declare -F __niri_cd_menu >/dev/null' >/dev/null 2>&1
grep -q '# >>> niri-clavis-setup:terminal-prompt >>>' "$HOME/.bashrc"
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
