# Flyxbot

A single-guild Discord bot built on [discord.py](https://discordpy.readthedocs.io/) 2.7.

## Requirements

- Python 3.11 or newer (3.14 recommended)
- A bot application at the [Discord Developer Portal](https://discord.com/developers/applications)

In the portal, under **Bot → Privileged Gateway Intents**, enable:

- **Server Members Intent** — needed for join handling and member lookups
- **Message Content Intent** — needed for prefix commands and edit/delete alerts

## Setup

The install scripts do everything: install Python if it's missing, create
`.venv`, install the dependencies, and seed `.env`. Both are safe to re-run.

**Ubuntu / Debian**

```sh
./scripts/install.sh
```

| Flag | Effect |
| --- | --- |
| `--systemd` | Also write `/etc/systemd/system/flyxbot.service` (installed, not started) |
| `--service-user NAME` | Which user the service runs as (default: the invoking user) |
| `--dry-run` | Print every command without running it |

It uses whatever Python the release ships if it's 3.11+, otherwise installs one
from apt, falling back to the deadsnakes PPA on older Ubuntu.

**Windows**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

`-Force` recreates the virtualenv; `-DryRun` changes nothing. Python is installed
via winget, or downloaded from python.org if winget isn't available.

**By hand**, if you'd rather:

```sh
python -m venv .venv
.venv/bin/pip install -e .          # .venv\Scripts\pip on Windows
cp .env.example .env                # then fill in DISCORD_TOKEN
```

Put your token in `.env` (git-ignored) or export `DISCORD_TOKEN` in the environment.

## Running

```sh
.venv/bin/python bot.py             # .venv\Scripts\python.exe bot.py on Windows
```

Slash commands are **not** synced automatically — a global sync on every startup
burns rate limits. Sync manually as the bot's owner once your commands change:

```
>sync ~     # sync to the current guild (instant)
>sync       # sync globally (can take up to an hour to propagate)
>sync ^     # clear this guild's commands
```

### As a service (Ubuntu)

If you installed with `--systemd`, the unit is written but left stopped so you
can fill in the token first:

```sh
sudo systemctl enable --now flyxbot   # start it, and on every boot
journalctl -u flyxbot -f              # follow the logs
sudo systemctl restart flyxbot        # after pulling changes
```

The unit reads `.env` via `EnvironmentFile`, so a token change needs a restart.

## Configuration

Everything guild-specific is read from the environment; see `.env.example` for
the full list and the defaults. Nothing needs to be set to run against the
original guild beyond `DISCORD_TOKEN`.

| Variable | Meaning |
| --- | --- |
| `DISCORD_TOKEN` | Bot token (required) |
| `COMMAND_PREFIX` | Prefix for text commands, default `>` |
| `NO_IMAGES_ROLE_ID` | Restriction role — holding it *removes* image perms |
| `MODERATOR_ROLE_ID` | Gates `takeimg`, `giveimg`, `modroulette`, `sm` |
| `LOCKDOWN_ROLE_ID` | Role whose `send_messages` `ld` toggles |
| `OWNER_USER_ID` | Receives DM alerts for edited/deleted messages mentioning them |
| `JOIN_BLACKLIST` | Users auto-restricted on join |

## Adding a command

Drop a `.py` file in `cogs/` with a `commands.Cog` subclass and an
`async def setup(bot)`. It is picked up automatically at startup — there is no
registration list. Errors do not need a per-command handler; the global one in
`bot.py` covers the usual cases.

## Development

```sh
ruff check .
ruff format .
```
