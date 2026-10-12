# Interactive directory navigation for the Bash cd command.

__niri_cd_menu() {
    if ! command -v fzf >/dev/null 2>&1; then
        printf '目录选择器需要 fzf，请重新运行安装脚本。\n' >&2
        return 127
    fi

    local root
    root=$(builtin pwd -P) || return
    local choice status key selection target parent
    local focus_current=false

    while true; do
        choice=$(
            {
                $focus_current && printf '%s\n' '.'
                (
                    shopt -s dotglob nullglob
                    for entry in "$root"/*; do
                        [[ -d $entry ]] && printf '%s\n' "${entry##*/}"
                    done
                ) | LC_ALL=C sort
                $focus_current || printf '%s\n' '.'
            } |
                env __NIRI_CD_MENU_ROOT="$root" fzf \
                    --height=75% \
                    --layout=reverse \
                    --border=rounded \
                    --prompt='进入目录 > ' \
                    --header="目录：$root    ↑↓ 选择    ← 上级    → 打开    Enter 进入    Esc 取消" \
                    --info=inline-right \
                    --color='fg:#fff8f5,bg:-1,hl:#bfe8ed,fg+:#bfe8ed,bg+:-1,hl+:#fff8f5,info:#c4874c,border:#62534c,prompt:#5c9fb1,pointer:#d57a58' \
                    --preview='item={}; command ls -la --color=always -- "$__NIRI_CD_MENU_ROOT/$item"' \
                    --preview-window='right,55%,border-left' \
                    --expect=left,right \
                    --no-multi
        )
        status=$?
        ((status == 0)) || return 130
        [[ $choice == *$'\n'* ]] || return 1

        key=${choice%%$'\n'*}
        selection=${choice#*$'\n'}
        [[ -n $selection ]] || return 1

        case $key in
            left)
                parent=$(builtin cd -- "$root/.." 2>/dev/null && builtin pwd -P) || continue
                root=$parent
                focus_current=true
                ;;
            right)
                [[ $selection == '.' ]] && continue
                target=$(builtin cd -- "$root/$selection" 2>/dev/null && builtin pwd -P) || continue
                root=$target
                focus_current=false
                ;;
            '')
                if [[ $selection == '.' ]]; then
                    target=$root
                else
                    target=$root/$selection
                fi
                builtin cd -- "$target"
                return
                ;;
            *)
                return 1
                ;;
        esac
    done
}

__niri_cd() {
    if (($# == 0)) || [[ $# -eq 1 && $1 == -i ]]; then
        __niri_cd_menu
        return
    fi
    builtin cd "$@"
}

cd() {
    __niri_cd "$@"
}
