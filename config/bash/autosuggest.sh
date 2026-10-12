# Neovim-style inline suggestions and automatic completion menus.

__niri_blesh=''
for __niri_blesh_candidate in \
    "$HOME/.local/share/blesh/ble.sh" \
    /usr/share/blesh/ble.sh \
    /usr/share/ble.sh/ble.sh \
    /usr/local/share/blesh/ble.sh
do
    if [[ -r $__niri_blesh_candidate ]]; then
        __niri_blesh=$__niri_blesh_candidate
        break
    fi
done

if [[ -n $__niri_blesh ]]; then
    # --norc keeps these settings deterministic while preserving user inputrc keys.
    source "$__niri_blesh" --norc

    bleopt complete_auto_complete=1
    bleopt complete_auto_delay=120
    bleopt complete_auto_history=1
    bleopt complete_auto_menu=220
    bleopt complete_limit_auto=2000
    bleopt complete_limit_auto_menu=200
    bleopt complete_menu_filter=1
    bleopt complete_menu_style=desc
    ble-face auto_complete='fg=243'

    if declare -F __niri_complete_current_word >/dev/null 2>&1; then
        # C-@ and C-SP both represent Ctrl+Space in terminals.
        ble-bind -m emacs -x 'C-@' '__niri_complete_current_word'
        ble-bind -m emacs -x 'C-SP' '__niri_complete_current_word'
        ble-bind -m emacs -x 'M-/' '__niri_complete_current_word'
        ble-bind -m vi_imap -x 'C-@' '__niri_complete_current_word'
        ble-bind -m vi_imap -x 'C-SP' '__niri_complete_current_word'
        ble-bind -m vi_imap -x 'M-/' '__niri_complete_current_word'
    fi
fi

unset __niri_blesh __niri_blesh_candidate
