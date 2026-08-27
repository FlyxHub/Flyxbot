# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flyxbot is a single-guild Discord bot on `discord.py` 2.7 (Python 3.11+). The whole
project is `bot.py`, `config.py`, and four cogs. There is no test suite; `ruff` is the
only tooling (configured in `pyproject.toml`).

See `README.md` for setup, required privileged intents, and the env-var table.

## Running

```
uv sync                # or: pip install -e .
python bot.py
```

The bot needs `DISCORD_TOKEN` in the environment or in a `.env` file. `config.py`
loads `.env` automatically if `python-dotenv` is installed; `bot.py` exits with a
readable message if no token is found.

## Architecture

**Startup.** `Flyxbot.setup_hook` loads every non-underscore `.py` in `cogs/` via
`Path.glob`, so it works on both Windows and POSIX and runs exactly once per process
(unlike an `on_ready` handler, which re-fires on every reconnect).

**Command tree is never auto-synced.** Syncing globally on each startup wastes rate
limits, so `cogs/owner.py` owns a prefix-only `sync` command (owner-gated, the standard
Umbra recipe). Any change to a command signature needs a manual `>sync ~`.

**Configuration.** All guild IDs live in `config.py` as a frozen `Settings` dataclass
read from the environment, with the original guild's IDs as fallbacks. Never hardcode
a snowflake in a cog — add a field to `Settings` and a line to `.env.example`.
Note the inverted naming on `no_images_role_id`: it is a *restriction* role, so
`takeimg` **adds** it and `giveimg` **removes** it.

**Command surface.** Prefix is `>` (or a bot mention) and nearly everything is a
`commands.hybrid_command`, reachable both as `>name` and as a slash command. The
`roulette`, `sm`, and `ld` groups are `hybrid_group(invoke_without_command=True)` —
without that flag the parent callback fires *in addition to* the subcommand on prefix
invocations. Owner commands (`sync`, `reload`) are prefix-only by design.

**Error handling is global.** `bot.py` has one `on_command_error` plus a `tree.on_error`,
both routed through `friendly_error()`, which pattern-matches the discord.py error
hierarchy and returns a user-facing string (or `None` for "unexpected", which gets
logged with a traceback). Ordering inside that `match` matters: subclasses must come
before their bases (`MemberNotFound` before `BadArgument`, `MissingPermissions` before
`CheckFailure`). New commands should not add their own `@cmd.error` handler — the global
handler skips any command or cog that defines one.

**Adding a command** means dropping a `.py` file in `cogs/` with a `commands.Cog`
subclass and an `async def setup(bot)`. No registration list to update.

## Conventions

- `from __future__ import annotations` at the top of every module; `Flyxbot` is imported
  under `TYPE_CHECKING` in cogs to avoid a circular import.
- Gate destructive commands with both `@commands.has_permissions(...)` (or
  `MODERATOR_ONLY`) and `@commands.bot_has_permissions(...)`, plus `@commands.guild_only()`
  wherever `ctx.guild` is dereferenced.
- Pass `reason=` on every audit-logged action (kick, ban, role change, channel edit).
- Use `app_commands.describe(...)` so slash options get help text.
- Nothing blocking in a coroutine — no `time.sleep`, no sync HTTP. Ruff's `ASYNC` rules
  are enabled to catch this.
