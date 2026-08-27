#!/usr/bin/env bash
#
# Bootstrap Flyxbot on Ubuntu (or any apt-based Debian derivative).
#
# Installs a suitable Python, creates .venv in the repo root, installs the
# project's dependencies, and seeds .env. Safe to re-run.
#
#   ./scripts/install.sh                 # install dependencies
#   ./scripts/install.sh --systemd       # also write a systemd unit
#   ./scripts/install.sh --dry-run       # print what would run, change nothing
#
set -euo pipefail

# discord.py 2.7 runs on 3.8+, but this project's code uses 3.11 syntax.
readonly MIN_MAJOR=3
readonly MIN_MINOR=11

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly REPO_ROOT

DRY_RUN=0
SUDO=()
WITH_SYSTEMD=0
SERVICE_USER=${SUDO_USER:-$(id -un)}

# ---------------------------------------------------------------- output ----

if [ -t 1 ]; then
    readonly C_RED=$'\033[31m' C_GREEN=$'\033[32m' C_YELLOW=$'\033[33m' C_BOLD=$'\033[1m' C_OFF=$'\033[0m'
else
    readonly C_RED='' C_GREEN='' C_YELLOW='' C_BOLD='' C_OFF=''
fi

step() { printf '%s==>%s %s\n' "$C_BOLD" "$C_OFF" "$*"; }
ok() { printf '%s  ok%s %s\n' "$C_GREEN" "$C_OFF" "$*"; }
warn() { printf '%swarn%s %s\n' "$C_YELLOW" "$C_OFF" "$*" >&2; }
die() {
    printf '%serror%s %s\n' "$C_RED" "$C_OFF" "$*" >&2
    exit 1
}

# Run a command, or just print it under --dry-run.
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '     + %s\n' "$*"
        return 0
    fi
    "$@"
}

usage() {
    sed -n '3,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

# ----------------------------------------------------------------- setup ----

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --systemd) WITH_SYSTEMD=1 ;;
            --service-user)
                [ $# -ge 2 ] || die "--service-user needs a username"
                SERVICE_USER=$2
                shift
                ;;
            --dry-run) DRY_RUN=1 ;;
            -h | --help) usage ;;
            *) die "Unknown option: $1 (try --help)" ;;
        esac
        shift
    done
}

require_apt() {
    command -v apt-get >/dev/null 2>&1 ||
        die "This script needs apt-get (Ubuntu/Debian). On another distro, install Python ${MIN_MAJOR}.${MIN_MINOR}+ and run: python3 -m venv .venv && .venv/bin/pip install -e ."
}

# Populate SUDO with 'sudo' when we aren't already root.
detect_sudo() {
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=()
        return
    fi
    command -v sudo >/dev/null 2>&1 ||
        die "Not running as root and sudo is not installed. Re-run as root."
    SUDO=(sudo)
    step "Requesting sudo (needed to install system packages)"
    [ "$DRY_RUN" -eq 1 ] || sudo -v
}

# ---------------------------------------------------------------- python ----

# True if $1 is an interpreter new enough for this project.
python_is_new_enough() {
    "$1" -c "import sys; raise SystemExit(0 if sys.version_info >= ($MIN_MAJOR, $MIN_MINOR) else 1)" \
        >/dev/null 2>&1
}

# Echo the path of the newest usable interpreter already on the system.
find_python() {
    local candidate resolved
    for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
        resolved=$(command -v "$candidate" 2>/dev/null) || continue
        if python_is_new_enough "$resolved"; then
            printf '%s\n' "$resolved"
            return 0
        fi
    done
    return 1
}

apt_has_package() {
    apt-cache show "$1" 2>/dev/null | grep -q '^Package:'
}

# Ubuntu-only PPA carrying Python versions the release itself doesn't ship.
add_deadsnakes() {
    local distro_id=''
    [ -r /etc/os-release ] && distro_id=$(. /etc/os-release && printf '%s' "${ID:-}")
    [ "$distro_id" = "ubuntu" ] || return 1

    step "Adding the deadsnakes PPA"
    run "${SUDO[@]}" apt-get install -y software-properties-common
    run "${SUDO[@]}" add-apt-repository -y ppa:deadsnakes/ppa
    run "${SUDO[@]}" apt-get update
}

install_python() {
    local pkg
    step "Installing Python (nothing new enough was found)"

    for pkg in python3.14 python3.13 python3.12 python3.11; do
        if apt_has_package "$pkg"; then
            run "${SUDO[@]}" apt-get install -y "$pkg" "$pkg-venv"
            return 0
        fi
    done

    if add_deadsnakes; then
        for pkg in python3.13 python3.12 python3.11; do
            if apt_has_package "$pkg"; then
                run "${SUDO[@]}" apt-get install -y "$pkg" "$pkg-venv"
                return 0
            fi
        done
    fi

    die "Could not find a Python ${MIN_MAJOR}.${MIN_MINOR}+ package for this release. Install one manually and re-run."
}

# Debian/Ubuntu ship venv separately; make sure the module actually works.
ensure_venv_module() {
    local python=$1 base
    if "$python" -m venv --help >/dev/null 2>&1; then
        return 0
    fi

    base=$(basename "$python")
    step "Installing the venv module for $base"
    if apt_has_package "$base-venv"; then
        run "${SUDO[@]}" apt-get install -y "$base-venv"
    else
        run "${SUDO[@]}" apt-get install -y python3-venv
    fi
}

# ------------------------------------------------------------------ main ----

install_system_packages() {
    step "Installing system packages"
    run "${SUDO[@]}" apt-get update
    run "${SUDO[@]}" apt-get install -y ca-certificates curl git
    ok "base packages present"
}

create_venv() {
    local python=$1
    local venv="$REPO_ROOT/.venv"

    if [ -x "$venv/bin/python" ] && python_is_new_enough "$venv/bin/python"; then
        ok "reusing existing virtualenv at $venv"
    else
        if [ -e "$venv" ]; then
            warn "replacing the virtualenv at $venv (it was missing or too old)"
            run rm -rf "$venv"
        fi
        step "Creating a virtualenv at $venv"
        run "$python" -m venv "$venv"
    fi

    step "Installing project dependencies"
    run "$venv/bin/python" -m pip install --quiet --upgrade pip
    run "$venv/bin/python" -m pip install --quiet -e "$REPO_ROOT"
    ok "dependencies installed"
}

seed_env_file() {
    local env_file="$REPO_ROOT/.env"

    if [ -f "$env_file" ]; then
        ok ".env already exists, leaving it alone"
        return
    fi

    step "Creating .env from .env.example"
    run cp "$REPO_ROOT/.env.example" "$env_file"
    run chmod 600 "$env_file"
    warn "Edit $env_file and set DISCORD_TOKEN before starting the bot."
}

install_systemd_unit() {
    local unit=/etc/systemd/system/flyxbot.service

    command -v systemctl >/dev/null 2>&1 || die "--systemd was passed but systemctl is not available."
    id "$SERVICE_USER" >/dev/null 2>&1 || die "No such user: $SERVICE_USER"

    step "Writing $unit (running as $SERVICE_USER)"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '     + write %s\n' "$unit"
    else
        "${SUDO[@]}" tee "$unit" >/dev/null <<UNIT
[Unit]
Description=Flyxbot Discord bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$REPO_ROOT
EnvironmentFile=$REPO_ROOT/.env
ExecStart=$REPO_ROOT/.venv/bin/python $REPO_ROOT/bot.py
Restart=on-failure
RestartSec=10s
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
UNIT
    fi

    run "${SUDO[@]}" systemctl daemon-reload
    ok "unit installed (not started)"
}

main() {
    parse_args "$@"
    [ "$DRY_RUN" -eq 1 ] && warn "dry run: no changes will be made"

    require_apt
    detect_sudo
    install_system_packages

    local python=''
    if ! python=$(find_python); then
        install_python
        if ! python=$(find_python); then
            # Under --dry-run nothing was actually installed, so this is expected.
            [ "$DRY_RUN" -eq 1 ] || die "Python still not found after installing."
            python=python3
            warn "dry run: assuming $python exists once the packages are installed"
        fi
    fi
    if python_is_new_enough "$python"; then
        ok "using $("$python" --version 2>&1) at $python"
    fi

    ensure_venv_module "$python"
    create_venv "$python"
    seed_env_file
    [ "$WITH_SYSTEMD" -eq 1 ] && install_systemd_unit

    cat <<SUMMARY

${C_GREEN}${C_BOLD}Flyxbot is installed.${C_OFF}

  1. Put your bot token in ${C_BOLD}$REPO_ROOT/.env${C_OFF}
  2. Enable the Server Members and Message Content intents in the
     Discord Developer Portal (Bot -> Privileged Gateway Intents)
  3. Start it:  ${C_BOLD}cd $REPO_ROOT && .venv/bin/python bot.py${C_OFF}
  4. In Discord, run ${C_BOLD}>sync ~${C_OFF} once to register the slash commands
SUMMARY

    if [ "$WITH_SYSTEMD" -eq 1 ]; then
        cat <<SUMMARY

  To run it as a service instead:
      ${C_BOLD}sudo systemctl enable --now flyxbot${C_OFF}
      ${C_BOLD}journalctl -u flyxbot -f${C_OFF}
SUMMARY
    fi
}

main "$@"
