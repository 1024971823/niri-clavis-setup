# A compact Bash prompt with Arch identity, location, and detailed Git status.

__niri_git_prompt() {
    local output line branch='' staged=0 unstaged=0 untracked=0 conflicts=0
    local ahead=0 behind=0 xy ahead_token behind_token
    local -a status_parts=()

    output=$(git status --porcelain=v2 --branch --untracked-files=normal --ignore-submodules=dirty 2>/dev/null) || return 1

    while IFS= read -r line; do
        case $line in
            '# branch.head '*)
                branch=${line#\# branch.head }
                ;;
            '# branch.ab '*)
                read -r ahead_token behind_token <<< "${line#\# branch.ab }"
                ahead=${ahead_token#+}
                behind=${behind_token#-}
                ;;
            '1 '*|'2 '*)
                xy=${line:2:2}
                [[ ${xy:0:1} == . ]] || staged=$((staged + 1))
                [[ ${xy:1:1} == . ]] || unstaged=$((unstaged + 1))
                ;;
            'u '*)
                conflicts=$((conflicts + 1))
                ;;
            '? '*)
                untracked=$((untracked + 1))
                ;;
        esac
    done <<< "$output"

    if [[ -z $branch || $branch == '(detached)' ]]; then
        branch=@$(git rev-parse --short HEAD 2>/dev/null)
    fi

    ((staged == 0)) || status_parts+=("+$staged")
    ((unstaged == 0)) || status_parts+=("~$unstaged")
    ((untracked == 0)) || status_parts+=("?$untracked")
    ((conflicts == 0)) || status_parts+=("!$conflicts")
    ((ahead == 0)) || status_parts+=("⇡$ahead")
    ((behind == 0)) || status_parts+=("⇣$behind")
    ((${#status_parts[@]} > 0)) || status_parts=('✓')

    printf '%s %s' "$branch" "${status_parts[*]}"
}

__niri_prompt_update() {
    local last_status=$?
    local reset='\[\e[0m\]'
    local blue='\[\e[38;5;31m\]'
    local green='\[\e[38;5;65m\]'
    local yellow='\[\e[38;5;179m\]'
    local coral='\[\e[38;5;167m\]'
    local prompt_color=$blue
    local git_part=''
    local git_summary=''
    local path_part=${PWD/#$HOME/'~'}

    if git_summary=$(__niri_git_prompt); then
        if [[ $git_summary == *' ✓' ]]; then
            git_part="  ${green} ${git_summary}${reset}"
        else
            git_part="  ${yellow} ${git_summary}${reset}"
        fi
    fi

    ((last_status == 0)) || prompt_color=$coral
    PS1="\n${blue}󰣇${reset} ${blue}${path_part}${reset}${git_part}\n${prompt_color}❯${reset} "
}

case ";${PROMPT_COMMAND:-};" in
    *';__niri_prompt_update;'*) ;;
    *) PROMPT_COMMAND="${PROMPT_COMMAND:+${PROMPT_COMMAND};}__niri_prompt_update" ;;
esac
