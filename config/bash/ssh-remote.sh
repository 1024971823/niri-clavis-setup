# Remote shell startup used by ssh-session.sh.
# The account's own login files load first. This file does not replace ~/.bashrc.

if [[ -f ~/.bash_profile ]]; then
    # shellcheck disable=SC1090
    source ~/.bash_profile
elif [[ -f ~/.bash_login ]]; then
    # shellcheck disable=SC1090
    source ~/.bash_login
elif [[ -f ~/.profile ]]; then
    # shellcheck disable=SC1090
    source ~/.profile
elif [[ -f ~/.bashrc ]]; then
    # shellcheck disable=SC1090
    source ~/.bashrc
fi

export HISTFILE="${HISTFILE:-$HOME/.bash_history}"
export HISTSIZE="${HISTSIZE:-5000}"
export HISTCONTROL="${HISTCONTROL:-ignoredups}"
set -o history

unalias cd 2>/dev/null || true
__niri_ssh_root=$HOME/.local/share/niri-clavis-setup
for __niri_ssh_helper in cd-menu.sh command-completion.sh autosuggest.sh; do
    if [[ -f $__niri_ssh_root/$__niri_ssh_helper ]]; then
        # shellcheck disable=SC1090
        source "$__niri_ssh_root/$__niri_ssh_helper"
    fi
done
unset __niri_ssh_root __niri_ssh_helper
