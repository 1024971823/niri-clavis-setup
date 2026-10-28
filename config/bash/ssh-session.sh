# Send the directory menu and completion to an interactive SSH session.

__niri_ssh_payload() {
    local share tmp payload
    share=$HOME/.local/share/niri-clavis-setup
    [[ -f $share/cd-menu.sh && -f $share/command-completion.sh && -f $share/completion-preview.sh && -f $share/autosuggest.sh && -f $share/ssh-remote.sh ]] || return 1
    tmp=$(mktemp -d) || return 1
    cp -- "$share/cd-menu.sh" "$share/command-completion.sh" "$share/completion-preview.sh" "$share/autosuggest.sh" "$share/ssh-remote.sh" "$tmp/" || {
        rm -rf -- "$tmp"
        return 1
    }
    if base64 -w 0 </dev/null >/dev/null 2>&1; then
        payload=$(tar -C "$tmp" -cf - cd-menu.sh command-completion.sh completion-preview.sh autosuggest.sh ssh-remote.sh | base64 -w 0)
    else
        payload=$(tar -C "$tmp" -cf - cd-menu.sh command-completion.sh completion-preview.sh autosuggest.sh ssh-remote.sh | base64 | tr -d '\n\r')
    fi
    rm -rf -- "$tmp"
    [[ -n $payload ]] || return 1
    printf '%s' "$payload"
}

__niri_ssh_launch() {
    local payload=$1
    cat <<EOF
sh -c 'if ! command -v bash >/dev/null 2>&1; then exec "\${SHELL:-/bin/sh}" -l; fi
mkdir -p "\$HOME/.local/share/niri-clavis-setup"
if command -v base64 >/dev/null 2>&1; then
base64 -d << NIRI_KIT_END | tar -xf - -C "\$HOME/.local/share/niri-clavis-setup"
${payload}
NIRI_KIT_END
fi
if [ -f "\$HOME/.local/share/niri-clavis-setup/ssh-remote.sh" ]; then
exec bash --rcfile "\$HOME/.local/share/niri-clavis-setup/ssh-remote.sh" -i
fi
exec "\${SHELL:-/bin/sh}" -l'
EOF
}

ssh() {
    if [[ $- != *i* ]] || [[ ! -t 0 || ! -t 1 ]]; then
        command ssh "$@"
        return
    fi

    local -a options=() original=("$@")
    local passthrough=0 destination="" arg
    while (($#)); do
        arg=$1
        if [[ $arg == -- ]]; then
            shift
            break
        fi
        if [[ $arg != -* ]]; then
            break
        fi
        case $arg in
            -N|-f|-G|-s|-T) passthrough=1 ;;
        esac
        options+=("$arg")
        case $arg in
            -[bcDeEFIiJLlmOoPpQRSwWB])
                shift
                if (($#)); then
                    options+=("$1")
                fi
                ;;
        esac
        shift
    done

    if (($# == 0)); then
        passthrough=1
    else
        destination=$1
        shift
        if (($#)); then
            passthrough=1
        fi
    fi
    if [[ $destination == git@* || $destination == *github.com ]]; then
        passthrough=1
    fi
    if ((passthrough)); then
        command ssh "${original[@]}"
        return
    fi

    local payload launcher
    payload=$(__niri_ssh_payload) || {
        command ssh "${original[@]}"
        return
    }
    launcher=$(__niri_ssh_launch "$payload")
    if ((${#options[@]})); then
        command ssh -t "${options[@]}" "$destination" "$launcher"
    else
        command ssh -t "$destination" "$launcher"
    fi
}
