#!/usr/bin/env bash
set -euo pipefail

niri validate -c "$HOME/.config/niri/config.kdl"
python3 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path.home().joinpath(".config/alacritty/alacritty.toml").read_text())'
command -v kitty >/dev/null
NIRI_KITTY_CONFIG="$HOME/.config/kitty/kitty.conf" kitty +runpy '
import os
from kitty.config import load_config
bad = []
opts = load_config(os.environ["NIRI_KITTY_CONFIG"], accumulate_bad_lines=bad)
assert not bad, bad
assert opts.cursor_trail > 0, "cursor trail is disabled"
assert opts.cursor_trail_decay == (0.12, 0.42), opts.cursor_trail_decay
assert opts.background_opacity == 0.82, opts.background_opacity
assert opts.font_size == 14.0, opts.font_size
'
grep -q 'Mod+T.*spawn "kitty"' "$HOME/.config/niri/config.kdl"
command -v tmux >/dev/null
tmux -f "$HOME/.config/tmux/tmux.conf" -L niri-clavis-verify new-session -d
[[ $(tmux -L niri-clavis-verify show -gv status) == 2 ]]
grep -q 'status-format\[0\].*#\[fill=#fff8f5' <(tmux -L niri-clavis-verify show -g status-format)
grep -q 'status-format\[1\].*status-left' <(tmux -L niri-clavis-verify show -g status-format)
tmux -L niri-clavis-verify kill-server
bash -n "$HOME/.local/share/niri-clavis-setup/bash-prompt.sh"
bash -n "$HOME/.local/share/niri-clavis-setup/cd-menu.sh"
bash -n "$HOME/.local/share/niri-clavis-setup/command-completion.sh"
bash -n "$HOME/.local/share/niri-clavis-setup/completion-preview.sh"
bash -n "$HOME/.local/share/niri-clavis-setup/autosuggest.sh"
python3 "$(dirname "$0")/scripts/install_blesh.py" --check
grep -q 'bleopt complete_auto_complete=1' "$HOME/.local/share/niri-clavis-setup/autosuggest.sh"
grep -q 'bleopt complete_auto_menu=220' "$HOME/.local/share/niri-clavis-setup/autosuggest.sh"
grep -q "ble-face auto_complete='fg=243'" "$HOME/.local/share/niri-clavis-setup/autosuggest.sh"
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
bash -ic 'declare -F __niri_cd_menu >/dev/null && declare -F __niri_complete_current_word >/dev/null' >/dev/null 2>&1
bash "$HOME/.local/share/niri-clavis-setup/completion-preview.sh" git --help | grep -qi 'usage\|用法'
bash --noprofile --norc <<'SH'
set -e
source "$HOME/.local/share/niri-clavis-setup/command-completion.sh"
fzf() {
    cat >/dev/null
    if [[ $__NIRI_COMPLETE_COMMAND == git ]]; then
        printf '%s\n' --help
    else
        printf '%s\n' kitty
    fi
}
READLINE_LINE='kitt'
READLINE_POINT=4
__niri_complete_current_word
[[ $READLINE_LINE == kitty && $READLINE_POINT == 5 ]]
READLINE_LINE='git --h'
READLINE_POINT=7
__niri_complete_current_word
[[ $READLINE_LINE == 'git --help' && $READLINE_POINT == 10 ]]
SH
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
