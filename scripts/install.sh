#!/usr/bin/env bash
#
# Bootstrap Flyxbot on Ubuntu (or any apt-based Debian derivative).
#
# Installs a suitable Python, creates .venv in the repo root, installs the
# project's dependencies, and seeds .env. With --docker it installs Docker
# Engine instead and leaves the Python side alone. Safe to re-run.
#
#   ./scripts/install.sh                   # install dependencies
#   ./scripts/install.sh --systemd         # also write a systemd unit
#   ./scripts/install.sh --docker          # install Docker Engine + Compose v2
#   ./scripts/install.sh --docker --start  # ...and bring the container up now
#   ./scripts/install.sh --dry-run         # print what would run, change nothing
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
WITH_DOCKER=0
START_STACK=0
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
    sed -n '3,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

# ----------------------------------------------------------------- setup ----

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --systemd) WITH_SYSTEMD=1 ;;
            --docker) WITH_DOCKER=1 ;;
            --start) START_STACK=1 ;;
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

    # Compose's restart policy is what keeps the container up, so there is no
    # unit for --systemd to write in that mode.
    [ "$WITH_DOCKER" -eq 1 ] && [ "$WITH_SYSTEMD" -eq 1 ] &&
        die "--docker and --systemd are alternatives, not a pair."
    [ "$START_STACK" -eq 1 ] && [ "$WITH_DOCKER" -eq 0 ] &&
        die "--start only means something alongside --docker."
    return 0
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

# ---------------------------------------------------------------- docker ----

# Echo "<distro> <codename>" naming the Docker apt repository for this system,
# or fail if there isn't one. Derivatives (Mint, Pop!_OS) carry a codename of
# their own that Docker publishes no suite for, so the upstream one is what
# works - that is what UBUNTU_CODENAME is there for.
docker_repo_target() {
    local id='' id_like='' version_codename='' ubuntu_codename=''
    if [ -r /etc/os-release ]; then
        id=$(. /etc/os-release && printf '%s' "${ID:-}")
        id_like=$(. /etc/os-release && printf '%s' "${ID_LIKE:-}")
        version_codename=$(. /etc/os-release && printf '%s' "${VERSION_CODENAME:-}")
        ubuntu_codename=$(. /etc/os-release && printf '%s' "${UBUNTU_CODENAME:-}")
    fi

    case "$id" in
        ubuntu) printf 'ubuntu %s\n' "${ubuntu_codename:-$version_codename}" ;;
        debian) printf 'debian %s\n' "$version_codename" ;;
        *)
            case " $id_like " in
                *ubuntu*) printf 'ubuntu %s\n' "${ubuntu_codename:-$version_codename}" ;;
                *debian*) printf 'debian %s\n' "$version_codename" ;;
                *) return 1 ;;
            esac
            ;;
    esac
}

install_docker() {
    # `docker compose version` is answered by the CLI plugin alone, so this
    # works before the user has any access to the daemon socket.
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        ok "already installed: $(docker --version)"
        return
    fi

    local target distro codename
    target=$(docker_repo_target) ||
        die "Can't tell which Docker repository fits this distribution. Install it by hand: https://docs.docker.com/engine/install/"
    distro=${target%% *}
    codename=${target#* }
    [ -n "$codename" ] ||
        die "/etc/os-release names no release codename, so the Docker repository can't be selected. Install it by hand: https://docs.docker.com/engine/install/"

    # Ubuntu's own docker.io package is too old to build this image without
    # DOCKER_BUILDKIT=1 (the Dockerfile uses a cache mount), so this uses
    # Docker's repository, which is also the only source of Compose v2.
    step "Adding Docker's apt repository ($distro $codename)"
    run "${SUDO[@]}" install -m 0755 -d /etc/apt/keyrings
    run "${SUDO[@]}" curl -fsSL "https://download.docker.com/linux/$distro/gpg" -o /etc/apt/keyrings/docker.asc
    run "${SUDO[@]}" chmod a+r /etc/apt/keyrings/docker.asc

    local list=/etc/apt/sources.list.d/docker.list
    local entry
    entry="deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$distro $codename stable"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '     + write %s\n' "$list"
    else
        printf '%s\n' "$entry" | "${SUDO[@]}" tee "$list" >/dev/null
    fi
    run "${SUDO[@]}" apt-get update

    step "Installing Docker Engine and Compose v2"
    run "${SUDO[@]}" apt-get install -y \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ok "Docker installed"
}

# The docker group is root-equivalent: anyone in it can start a container that
# mounts the host filesystem. That is the accepted trade for not typing sudo in
# front of every command, but it is worth knowing you made it.
join_docker_group() {
    local user=${SUDO_USER:-$(id -un)}

    [ "$user" != root ] || return 0
    if id -nG "$user" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
        ok "$user is already in the docker group"
        return
    fi

    step "Adding $user to the docker group"
    run "${SUDO[@]}" usermod -aG docker "$user"
    warn "Log out and back in for that to take effect. Until you do, docker commands need sudo."
}

compose_up() {
    local env_file="$REPO_ROOT/.env"

    if [ "$DRY_RUN" -eq 0 ] && ! grep -Eq '^DISCORD_TOKEN=.+' "$env_file"; then
        die "DISCORD_TOKEN is empty in $env_file. Set it, then run: docker compose up -d"
    fi

    # sudo even when the group was just granted: this shell predates the change.
    step "Building the image and starting the container"
    run "${SUDO[@]}" docker compose -f "$REPO_ROOT/docker-compose.yml" up -d --build
    ok "flyxbot is running"
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

docker_summary() {
    cat <<SUMMARY

${C_GREEN}${C_BOLD}Docker is installed.${C_OFF}

  1. Put your bot token in ${C_BOLD}$REPO_ROOT/.env${C_OFF}
  2. Enable the Server Members and Message Content intents in the
     Discord Developer Portal (Bot -> Privileged Gateway Intents)
  3. Start it:  ${C_BOLD}cd $REPO_ROOT && docker compose up -d${C_OFF}
  4. In Discord, run ${C_BOLD}>sync ~${C_OFF} once to register the slash commands

  Follow the log with ${C_BOLD}docker compose logs -f${C_OFF}.
SUMMARY
}

main() {
    parse_args "$@"
    [ "$DRY_RUN" -eq 1 ] && warn "dry run: no changes will be made"

    require_apt
    detect_sudo
    install_system_packages

    if [ "$WITH_DOCKER" -eq 1 ]; then
        install_docker
        join_docker_group
        seed_env_file
        [ "$START_STACK" -eq 1 ] && compose_up
        docker_summary
        return
    fi

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
