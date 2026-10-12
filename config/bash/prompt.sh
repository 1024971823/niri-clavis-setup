# A lightweight two-line Bash prompt with Git status for the Niri setup.

__niri_prompt_update() {
    local last_status=$?
    local reset='\[\e[0m\]'
    local faint='\[\e[38;5;244m\]'
    local blue='\[\e[38;5;31m\]'
    local green='\[\e[38;5;65m\]'
    local coral='\[\e[38;5;167m\]'
    local bold='\[\e[1m\]'
    local prompt_symbol='❯'
    local git_part=''
    local dirty=''
    local branch=''
    local path_part=${PWD/#$HOME/'~'}

    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null ||
            git rev-parse --short HEAD 2>/dev/null)
        if [[ -n $branch ]]; then
            if ! git diff --quiet --ignore-submodules 2>/dev/null ||
                ! git diff --cached --quiet --ignore-submodules 2>/dev/null ||
                [[ -n $(git ls-files --others --exclude-standard 2>/dev/null) ]]; then
                dirty=' ±'
            fi
            git_part="  ${faint}on${reset} ${green} ${branch}${dirty}${reset}"
        fi
    fi

    if ((last_status == 0)); then
        prompt_symbol="❯"
    else
        prompt_symbol="❯"
        coral='\[\e[38;5;167m\]'
    fi

    PS1="\n${faint}╭─${reset} ${bold}${blue}\u${reset}${faint}@${reset}${blue}\h${reset} ${faint}·${reset} ${coral}${path_part}${reset}${git_part}\n${faint}╰─${reset} ${blue}${prompt_symbol}${reset} "
}

case ";${PROMPT_COMMAND:-};" in
    *';__niri_prompt_update;'*) ;;
    *) PROMPT_COMMAND="${PROMPT_COMMAND:+${PROMPT_COMMAND};}__niri_prompt_update" ;;
esac
