#!/usr/bin/env bash
set -u

command_name=${1-}
candidate=${2-}

print_help() {
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

preview_path() {
    local path=$1 resolved

    if [[ $path == '~/'* ]]; then
        path=$HOME/${path#~/}
    fi
    resolved=$(realpath -m -- "$path" 2>/dev/null) || resolved=$path

    if [[ -d $resolved ]]; then
        printf '目录：%s\n\n' "$resolved"
        command ls -la --color=always -- "$resolved"
    elif [[ -f $resolved ]]; then
        printf '文件：%s\n' "$resolved"
        file --brief -- "$resolved"
        printf '\n'
        if file --mime --brief -- "$resolved" | grep -q '^text/'; then
            sed -n '1,180p' -- "$resolved"
        fi
    else
        printf '候选路径：%s\n' "$path"
    fi
}

if [[ $candidate == -* ]]; then
    printf '命令：%s\n\n可用选项预览\n\n' "$command_name"
    print_help "$command_name" | sed -n '1,220p'
elif [[ -e $candidate || $candidate == */* || $candidate == '~'* ]]; then
    preview_path "$candidate"
else
    printf '命令：%s\n\n' "$candidate"
    type -a -- "$candidate" 2>&1 || true
    if command -v whatis >/dev/null 2>&1; then
        printf '\n'
        whatis -- "$candidate" 2>/dev/null || true
    fi
    printf '\n帮助预览\n\n'
    print_help "$candidate" | sed -n '1,220p'
fi
