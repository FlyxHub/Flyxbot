# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flyxbot is a single-guild Discord bot built on `discord.py` (v2.x — it uses `bot.tree`, `hybrid_command`, and async `load_extension`, all 2.0+ APIs). There is no README, requirements file, test suite, or lint config; the whole project is `bot.py` plus three cogs.

## Running

```
pip install -U discord.py
python bot.py
```

**The bot does not run as checked in.** `bot.py` ends with `bot.run(TOKEN)`, but the `TOKEN` assignment is commented out (`#TOKEN = '(insert token here)'`) so the module raises `NameError` at startup. Restore a token definition — reading it from an env var (`os.environ["TOKEN"]`, `os` is already imported) is preferable to hardcoding, and keeps it out of commits.

## Architecture

**Cog auto-loading happens in `on_ready`, not before `bot.run`.** `bot.py:11-16` walks the `cogs/` directory and turns each path into a module name via `root.replace("\\", ".")` — that only produces `cogs.funCommands` on Windows path separators. On POSIX the `/` is left intact and `load_extension` fails. Two other consequences of loading in `on_ready`:

- `on_ready` fires again on every reconnect/resume, so a re-fire raises `ExtensionAlreadyLoaded`. Any change here should either move loading into `setup_hook` or guard against reloading.
- `await bot.tree.sync()` runs in the same handler, so slash commands are re-synced globally on each ready.

Adding a command means dropping a `.py` file in `cogs/` with a `commands.Cog` subclass and an `async def setup(bot)` — no registration list to update.

**Command surface.** Prefix is `>` and nearly everything is a `commands.hybrid_command`, so each command is reachable both as `>name` and as a slash command. Two subcommand groups (`sm`, `ld`, plus `roulette` in Fun) are `hybrid_group`s whose parent callback just replies with the group name.

`ban` and `sm set` take arguments through `commands.FlagConverter` subclasses defined inline in the cog class (`banFlags`, `smFlags`) rather than plain parameters, which is what makes the slash-command variants show named options. Prefix invocation therefore needs `key: value` syntax (`>ban member: @user reason: spam`).

Error handling is per-command: each command has a sibling `@<command>.error` handler that pattern-matches on `commands.MissingRequiredArgument`, `CommandInvokeError`, `MemberNotFound`, `MissingRole`, etc. and replies with a user-facing string. There is no global error handler — new commands need their own.

## Hardcoded guild IDs

Every ID is a literal in the source; there is no config layer. If the bot is moved to another guild, all of these must change:

| ID | Meaning | Used in |
| --- | --- | --- |
| `1041203946817081365` | "no images" restriction role | `modCommands.py` (`takeimg`/`giveimg`), `listeners.py` (`on_member_join`) |
| `1042085580034539580` | Moderator role gating `takeimg`, `giveimg`, `modroulette`, `sm` | `modCommands.py` |
| `1036799478608429116` | Role whose `send_messages` is toggled by `ld enable`/`ld disable` | `modCommands.py` |
| `307688449811415041` | Owner ("flyx") who receives DM alerts on edited/deleted messages that mention them | `listeners.py` |
| `787885272594513950`, `514143503471738910` | Join blacklist — these users get the restriction role on join | `listeners.py` |

Note the inverted naming: `1041203946817081365` is a *restriction* role, so `takeimg` **adds** it and `giveimg` **removes** it.

## Permission gating

Mixed and inconsistent by design of whoever wrote it — `kick`/`ban`/`unban` use `@commands.has_permissions(...)`, `ld` uses `has_permissions(administrator=True)`, and the image/roulette/slowmode commands use `@commands.has_role(1042085580034539580)`. Several error handlers catch `MissingRole` on commands that actually raise `MissingPermissions`, so those branches are dead. Match the surrounding style when extending a cog, but be aware the handler may not fire.
