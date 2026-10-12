# Fuzzy command and argument completion with contextual previews.

__niri_completion_help() {
    local command_name=$1 executable

    case $command_name in
        '')
            return
            ;;
        help)
            help 2>&1
            return
            ;;
    esac

    if [[ $command_name == */* ]]; then
        executable=$command_name
    else
        executable=$(type -P -- "$command_name" 2>/dev/null) || executable=
    fi

    if [[ -n $executable && -x $executable ]]; then
        if command -v timeout >/dev/null 2>&1; then
            timeout 3 "$executable" --help 2>&1 && return
            timeout 3 "$executable" -h 2>&1 && return
        else
            "$executable" --help 2>&1 && return
            "$executable" -h 2>&1 && return
        fi
    fi

    if command -v man >/dev/null 2>&1; then
        MANWIDTH=100 man -- "$command_name" 2>/dev/null | col -b 2>/dev/null
    fi
}

__niri_completion_candidates() {
    local command_name=$1 current_word=$2 context=$3
    local -a source_candidates=()
    local candidate

    case $context in
        command)
            mapfile -t source_candidates < <(compgen -c -- "$current_word")
            ;;
        variable)
            mapfile -t source_candidates < <(compgen -v -- "${current_word#\$}")
            source_candidates=("${source_candidates[@]/#/\$}")
            ;;
        option)
            mapfile -t source_candidates < <(
                __niri_completion_help "$command_name" |
                    grep -Eo -- '(^|[[:space:]])(--?[A-Za-z0-9][A-Za-z0-9_-]*)' |
                    sed 's/^[[:space:]]*//' |
                    grep -F -- "$current_word"
            )
            ;;
        path)
            mapfile -t source_candidates < <(compgen -f -- "$current_word")
            ;;
        directory)
            mapfile -t source_candidates < <(compgen -d -- "$current_word")
            ;;
        *)
            if [[ $command_name == cd || $command_name == pushd ]]; then
                mapfile -t source_candidates < <(compgen -d -- "$current_word")
            else
                mapfile -t source_candidates < <(compgen -f -- "$current_word")
            fi
            ;;
    esac

    ((${#source_candidates[@]} > 0)) || return 0
    printf '%s\n' "${source_candidates[@]}" | awk '!seen[$0]++' | LC_ALL=C sort
}

__niri_complete_current_word() {
    command -v fzf >/dev/null 2>&1 || {
        printf '\n命令补全需要 fzf，请重新运行安装脚本。\n' >&2
        return 127
    }

    local line=${READLINE_LINE-}
    local cursor=${READLINE_POINT-${#line}}
    local before word_start character current_word prefix command_name
    local context selection replacement status
    local -a words=()

    ((cursor >= 0 && cursor <= ${#line})) || cursor=${#line}
    before=${line:0:cursor}
    word_start=$cursor
    while ((word_start > 0)); do
        character=${before:word_start-1:1}
        [[ $character == ' ' || $character == $'\t' ]] && break
        word_start=$((word_start - 1))
    done

    current_word=${before:word_start}
    prefix=${before:0:word_start}
    read -r -a words <<< "$prefix"
    command_name=${words[0]-}

    if [[ -z $command_name ]]; then
        context=command
    elif [[ $current_word == \$* ]]; then
        context=variable
    elif [[ $current_word == -* ]]; then
        context=option
    elif [[ $current_word == */* || $current_word == '~'* ]]; then
        context=path
    else
        context=argument
    fi

    selection=$(
        __niri_completion_candidates "$command_name" "$current_word" "$context" |
            __NIRI_COMPLETE_COMMAND="$command_name" fzf \
                --height=72% \
                --layout=reverse \
                --border=rounded \
                --prompt='指令预览补全 > ' \
                --header="Ctrl+Space / Alt+/ 打开    ↑↓ 选择    Enter 补全    Esc 取消" \
                --info=inline-right \
                --no-multi \
                --color='fg:#fff8f5,bg:-1,hl:#bfe8ed,fg+:#bfe8ed,bg+:-1,hl+:#fff8f5,info:#c4874c,border:#62534c,prompt:#5c9fb1,pointer:#d57a58' \
                --preview="bash \"$HOME/.local/share/niri-clavis-setup/completion-preview.sh\" \"\$__NIRI_COMPLETE_COMMAND\" {}" \
                --preview-window='right,60%,border-left'
    )
    status=$?
    ((status == 0)) || return 130
    [[ -n $selection ]] || return 1

    replacement=$selection
    if [[ $context != command && $context != variable && $context != option ]] &&
        [[ $selection == *[[:space:]\*\?\[\]\&\;\|\(\)\<\>\"\']* ]]; then
        printf -v replacement '%q' "$selection"
    fi

    READLINE_LINE=${line:0:word_start}${replacement}${line:cursor}
    READLINE_POINT=$((word_start + ${#replacement}))

    # Immediately refresh the inline suggestion after an explicit selection.
    if [[ $(type -t ble) == function ]] && declare -F ble/widget/auto-complete-enter >/dev/null 2>&1; then
        ble widget auto-complete-enter >/dev/null 2>&1 || true
    fi
}

if [[ $- == *i* ]]; then
    bind -m emacs-standard -x '"\C- ":__niri_complete_current_word' >/dev/null 2>&1 || true
    bind -m emacs-standard -x '"\e/":__niri_complete_current_word' >/dev/null 2>&1 || true
    bind -m vi-insert -x '"\C- ":__niri_complete_current_word' >/dev/null 2>&1 || true
    bind -m vi-insert -x '"\e/":__niri_complete_current_word' >/dev/null 2>&1 || true
fi
