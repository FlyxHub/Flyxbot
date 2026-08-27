# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flyxbot is a single-guild Discord bot on `discord.py` 2.7 (Python 3.11+). The whole
project is `bot.py`, `config.py`, and four cogs. There is no test suite; `ruff` is the
only tooling (configured in `pyproject.toml`).

See `README.md` for setup, required privileged intents, and the env-var table.

## Running

```
./scripts/install.sh                        # Ubuntu; --systemd also writes a unit
powershell -File scripts\install.ps1        # Windows
.venv/bin/python bot.py
```

Both installers are idempotent and support `--dry-run` / `-DryRun`, which prints
every command instead of running it — use that when changing them. `install.sh`
is pinned to LF by `.gitattributes`; a CRLF shebang breaks it on Linux.

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
read from the environment. Never hardcode a snowflake in a cog — add a field to
`Settings` and a line to `.env.example`.

**Prefer a per-guild default to a configured ID.** `Settings` holds one snowflake shared
by every guild the bot is in, so it can only ever be correct in one of them. Resolve from
`ctx`/`guild` wherever Discord already gives an answer (`guild.default_role`, `ctx.channel`,
`ctx.me`). Gate commands on Discord permissions (`@commands.has_permissions`), never on a
configured role ID: a `commands.has_role(id)` check is bound at import time and locks the
command out of every other guild, including for its owner.

`no_images_role_id` is the only configured snowflake left, and no command uses it: note the
inverted naming — it is a *restriction* role, and the only thing that applies it is
`on_member_join` in `cogs/listeners.py`, for users listed in `join_blacklist` (empty by
default, so that handler is normally inert).

**Command surface.** Prefix is `>` (or a bot mention) and nearly everything is a
`commands.hybrid_command`, reachable both as `>name` and as a slash command. The
`roulette` and `sm` groups are `hybrid_group(invoke_without_command=True)` —
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
- Gate destructive commands with both `@commands.has_permissions(...)` and
  `@commands.bot_has_permissions(...)`, plus `@commands.guild_only()` wherever `ctx.guild`
  is dereferenced. Where an argument escalates what a command does (`modroulette`'s
  `ban`), check the extra permission in the body — the decorator only sees the floor, and
  make sure the loop variable doesn't shadow the command's own `member` parameter.
- Pass `reason=` on every audit-logged action (kick, ban, role change, channel edit).
- Use `app_commands.describe(...)` so slash options get help text.
- Nothing blocking in a coroutine — no `time.sleep`, no sync HTTP. Ruff's `ASYNC` rules
  are enabled to catch this.

## Git

Work happens on `Dev`; `main` is what PRs target.

**Commit continuously, not in one batch at the end.** Every completed unit of work is a
commit, and the tree should import and pass `ruff check` at each one. Batching a whole
session into a single commit loses the reasoning, and anything built and then reworked
later in the same session never reaches the log at all.

- Run `ruff check .` and `ruff format --check .` before staging. A commit that fails
  lint is one someone else has to bisect through later.
- Keep a commit to one logical change. Reach for a second commit rather than a subject
  line with "and" in it.
- Stage deliberately: read `git status` and `git diff --stat` first. Drop line-ending
  churn — a file that shows as modified but has an empty `git diff` is CRLF noise, not
  a change, and `git checkout --` it.
- Subject in the imperative mood ("Remove the lockdown commands", not "Removed"). Use
  the body for *why*; the diff already covers *what*.
- Prefer a new commit to amending or force-pushing one that has been pushed.
- Never commit `.env` — it holds the token and is gitignored. `.env.example` is where a
  new setting gets recorded.
- Removing a command changes its slash-command registration too: note that the change
  needs a manual `>sync` (see **Command tree is never auto-synced**).
