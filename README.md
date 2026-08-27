# Flyxbot

A single-guild Discord bot built on [discord.py](https://discordpy.readthedocs.io/) 2.7.

## Requirements

- Python 3.11 or newer (3.14 recommended)
- A bot application at the [Discord Developer Portal](https://discord.com/developers/applications)

In the portal, under **Bot → Privileged Gateway Intents**, enable:

- **Server Members Intent** — needed for join handling and member lookups
- **Message Content Intent** — needed for prefix commands and edit/delete alerts

## Setup

```sh
# with uv
uv sync
cp .env.example .env   # then fill in DISCORD_TOKEN

# or with pip
python -m venv .venv && .venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -e .
```

Put your token in `.env` (git-ignored) or export `DISCORD_TOKEN` in the environment.

## Running

```sh
python bot.py
```

Slash commands are **not** synced automatically — a global sync on every startup
burns rate limits. Sync manually as the bot's owner once your commands change:

```
>sync ~     # sync to the current guild (instant)
>sync       # sync globally (can take up to an hour to propagate)
>sync ^     # clear this guild's commands
```

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
