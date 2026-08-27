# Flyxbot

Flyxbot is a moderation and entertainment bot for a single Discord server. It
provides kick, ban, and slowmode commands for
moderators, a set of games and lookup commands for everyone, and direct-message
alerts when someone edits or deletes a message that mentions you.

Every command works two ways: as a text command with the `>` prefix, and as a
slash command.

Flyxbot is built on [discord.py](https://discordpy.readthedocs.io/) 2.7 and runs
on Python 3.11 or later.

## Contents

- [Before you begin](#before-you-begin)
- [Create the Discord application](#create-the-discord-application)
- [Invite the bot to your server](#invite-the-bot-to-your-server)
- [Install on Linux](#install-on-linux)
- [Install on Windows](#install-on-windows)
- [Configure the bot](#configure-the-bot)
- [Start the bot](#start-the-bot)
- [Register the slash commands](#register-the-slash-commands)
- [Command reference](#command-reference)
- [Update to a new version](#update-to-a-new-version)
- [Troubleshoot](#troubleshoot)
- [Uninstall](#uninstall)
- [Modify the bot](#modify-the-bot)

## Before you begin

You need the following:

| Requirement | Notes |
| --- | --- |
| A Discord account with **Manage Server** permission | You need it on the server that hosts the bot. |
| Ubuntu 22.04 or later, or Windows 10 or later | Other Linux distributions work if they use `apt`. |
| Git | Used to clone this repository. |
| An internet connection | The installer downloads Python and the bot's dependencies. |

You don't need to install Python yourself. The installers do it for you if a
suitable version is missing.

If you're redeploying and already have a bot token, skip to
[Install on Linux](#install-on-linux) or
[Install on Windows](#install-on-windows).

## Create the Discord application

Do this once per bot. If you already have a token, go to
[Install on Linux](#install-on-linux).

1. Sign in to the
   [Discord Developer Portal](https://discord.com/developers/applications).
1. Select **New Application**, enter a name, accept the terms, and select
   **Create**.
1. In the left sidebar, select **Bot**.
1. Under **Privileged Gateway Intents**, turn on both of the following:
   - **Server Members Intent**. The bot uses it to detect members joining and to
     look members up.
   - **Message Content Intent**. The bot uses it to read `>` commands and to
     report edited or deleted messages.
1. Select **Save Changes**.
1. Under the bot's username, select **Reset Token**, confirm, and then select
   **Copy**.

> [!IMPORTANT]
> The token is a password for your bot. Anyone who has it can control the bot.
> Store it only in the `.env` file described in
> [Configure the bot](#configure-the-bot), which Git ignores. Never commit it. If
> you leak it, return to this page and select **Reset Token** to invalidate the
> old one.

Paste the token somewhere safe for now. You need it during installation.

## Invite the bot to your server

1. Copy the following URL and replace `YOUR_CLIENT_ID` with the **Application ID**
   from the portal's **General Information** page:

   ```text
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268520534&scope=bot+applications.commands
   ```

1. Open the URL in a browser.
1. Select your server, and then select **Authorize**.

The `permissions=268520534` value grants exactly what Flyxbot's commands need:

| Permission | Required by |
| --- | --- |
| View Channels, Send Messages, Read Message History | Every command |
| Embed Links | `whois`, `av`, `quickpoll`, and the DM alerts |
| Add Reactions | `quickpoll` |
| Kick Members | `kick`, `modroulette`, `roulette kick` |
| Ban Members | `ban`, `unban`, `modroulette`, `roulette ban` |
| Manage Roles | Restricting blacklisted users on join (see `JOIN_BLACKLIST`) |
| Manage Channels | `sm set`, `sm off` |

> [!CAUTION]
> Discord permissions aren't enough on their own. In **Server Settings > Roles**,
> drag the bot's role *above* every role it needs to act on. A bot can't kick,
> ban, or change the roles of a member whose highest role sits above its own,
> even with Administrator. This is the most common cause of "I don't have
> permission to do that" after a working install.

## Install on Linux

These steps target Ubuntu. They also work on Debian and other `apt`-based
distributions.

1. Install Git if it's missing:

   ```sh
   sudo apt-get update && sudo apt-get install -y git
   ```

1. Clone the repository and change into it:

   ```sh
   git clone https://github.com/FlyxHub/Flyxbot.git
   cd Flyxbot
   ```

1. Run the installer:

   ```sh
   ./scripts/install.sh
   ```

   The installer finds a Python 3.11 or later interpreter, or installs one from
   `apt`. It then creates a virtual environment in `.venv`, installs the bot's
   dependencies, and creates `.env` from `.env.example`.

1. Continue to [Configure the bot](#configure-the-bot).

To preview the installation without changing anything, run
`./scripts/install.sh --dry-run` first. It prints every command it would run.

### install.sh options

| Option | Description |
| --- | --- |
| `--systemd` | Also creates a `systemd` service so the bot starts at boot. The installer writes the service but doesn't start it, so you can add your token first. |
| `--service-user NAME` | Sets the user the service runs as. Defaults to the user running the installer. |
| `--dry-run` | Prints each command instead of running it. Changes nothing. |
| `--help` | Prints usage and exits. |

> [!NOTE]
> The installer is safe to run again. It reuses an existing `.venv` if the
> version is new enough, and it never overwrites an existing `.env`.

### If your distribution ships an old Python

Ubuntu 22.04 ships Python 3.10, which is older than this bot requires. The
installer handles this: it installs a newer Python from `apt`, and if the release
offers nothing new enough, it adds the
[deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) and
installs from there. No action is needed from you.

## Install on Windows

1. Install [Git for Windows](https://git-scm.com/install/windows) if it's missing.
   Alternatively, run `winget install --id Git.Git -e`.
1. Open PowerShell.
1. Clone the repository and change into it:

   ```powershell
   git clone https://github.com/FlyxHub/Flyxbot.git
   cd Flyxbot
   ```

1. Run the installer:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\install.ps1
   ```

   The installer finds a Python 3.11 or later interpreter, or installs one with
   `winget`. It then creates a virtual environment in `.venv`, installs the bot's
   dependencies, and creates `.env` from `.env.example`.

1. Continue to [Configure the bot](#configure-the-bot).

> [!NOTE]
> `-ExecutionPolicy Bypass` applies only to that one command. It doesn't change
> your system's script policy. Without it, PowerShell refuses to run the
> installer and reports that "running scripts is disabled on this system".

### install.ps1 options

| Option | Description |
| --- | --- |
| `-Force` | Deletes and recreates `.venv`. Use it if the environment is broken. |
| `-DryRun` | Prints each command instead of running it. Changes nothing. |

If `winget` isn't available, the installer downloads the Python installer from
[python.org](https://www.python.org/downloads/) instead.

## Configure the bot

The bot reads its settings from a `.env` file in the repository root. The
installer creates this file for you.

1. Open `.env` in a text editor:

   ```sh
   nano .env          # Linux
   notepad .env       # Windows
   ```

1. Set `DISCORD_TOKEN` to the token you copied earlier:

   ```ini
   DISCORD_TOKEN=your-token-here
   ```

1. Save the file and close the editor.

Only `DISCORD_TOKEN` is required. Every other setting has a working default.

### Settings

| Variable | Default | Description |
| --- | --- | --- |
| `DISCORD_TOKEN` | *(none)* | The bot token. Required. |
| `COMMAND_PREFIX` | `>` | The prefix for text commands. Mentioning the bot always works as a prefix too. |
| `NO_IMAGES_ROLE_ID` | `1041203946817081365` | The role given to blacklisted users when they join. Only used when `JOIN_BLACKLIST` is non-empty. |
| `OWNER_USER_ID` | `307688449811415041` | The user who receives DM alerts about edited and deleted messages that mention them. |
| `JOIN_BLACKLIST` | *(empty)* | Users who receive the restriction role as soon as they join. Empty by default, so nobody is restricted on join. Separate multiple IDs with commas or spaces. |

Every command works in any server as soon as the bot is invited - they all gate on
Discord permissions and read their targets from the invocation. The only settings
that name a specific server are `NO_IMAGES_ROLE_ID` and `JOIN_BLACKLIST`, and they
matter only if you use the join blacklist.

> [!TIP]
> To find an ID, turn on **User Settings > Advanced > Developer Mode** in Discord.
> You can then right-click any role, user, or channel and select **Copy ID**.

## Start the bot

### Run it in a terminal

Use this to test a new install, because you see errors immediately.

On Linux:

```sh
.venv/bin/python bot.py
```

On Windows:

```powershell
.venv\Scripts\python.exe bot.py
```

A working start logs a line like this:

```text
[2026-08-27 10:43:19] [INFO    ] flyxbot: Connected as Flyxbot (id=946718954217299999)
```

To stop the bot, press `Ctrl+C`.

> [!NOTE]
> Always start the bot with the interpreter inside `.venv`. A bare `python bot.py`
> uses your system Python, which doesn't have discord.py installed and fails with
> `ModuleNotFoundError: No module named 'discord'`.

### Run it as a service on Linux

A `systemd` service restarts the bot if it crashes and starts it at boot. This is
the recommended way to run Flyxbot long term.

1. If you didn't use `--systemd` during installation, run the installer again
   with that option:

   ```sh
   ./scripts/install.sh --systemd
   ```

1. Start the service and enable it at boot:

   ```sh
   sudo systemctl enable --now flyxbot
   ```

1. Confirm that it's running:

   ```sh
   systemctl status flyxbot
   ```

Manage the service with these commands:

| Task | Command |
| --- | --- |
| Follow the logs | `journalctl -u flyxbot -f` |
| Read recent errors | `journalctl -u flyxbot -p err -n 50` |
| Restart after a change | `sudo systemctl restart flyxbot` |
| Stop the bot | `sudo systemctl stop flyxbot` |
| Stop it starting at boot | `sudo systemctl disable flyxbot` |

The service reads `.env` when it starts, so restart it after you change any
setting.

### Run it at sign-in on Windows

Windows has no direct equivalent of `systemd`. To start the bot when you sign in,
create a scheduled task:

1. Open **Task Scheduler** and select **Create Task**.
1. On the **General** tab, enter `Flyxbot` as the name.
1. On the **Triggers** tab, select **New**, and then set **Begin the task** to
   **At log on**.
1. On the **Actions** tab, select **New**, and then set the following:
   - **Program/script**: the full path to `.venv\Scripts\python.exe`
   - **Add arguments**: `bot.py`
   - **Start in**: the full path to the repository folder
1. Select **OK**.

> [!NOTE]
> **Start in** is required. Without it, the bot can't find its `.env` file or its
> `cogs` folder.

## Register the slash commands

Text commands work as soon as the bot starts. Slash commands need to be
registered with Discord once.

Flyxbot doesn't register them automatically, because doing so on every start
wastes Discord's rate limits.

1. Start the bot.
1. In any channel on your server, send:

   ```text
   >sync ~
   ```

The bot replies with the number of commands it registered. The slash commands
appear in Discord immediately.

> [!NOTE]
> Only the bot's owner can run `>sync`. Discord treats the owner as the account
> or team that owns the application in the Developer Portal.

Run `>sync ~` again whenever you add a command or change a command's name or
options. You don't need it after other code changes.

| Command | Effect |
| --- | --- |
| `>sync ~` | Registers commands on the current server. Takes effect immediately. |
| `>sync` | Registers commands on every server. Can take up to an hour to appear. |
| `>sync ^` | Removes this server's commands. |

## Command reference

Run each of these as `>command` or `/command`.

### Everyone

| Command | Description |
| --- | --- |
| `ping` | Shows the bot's current latency. |
| `poop` | Sends a joke message. |
| `coinflip` | Flips a coin. |
| `dice` | Rolls a six-sided die. |
| `number <num1> <num2>` | Returns a random number between two numbers. |
| `quickpoll <question>` | Posts a yes/no poll with reactions. |
| `av [member]` | Shows a member's avatar. Defaults to you. |
| `whois [member]` | Shows a member's join date, roles, and ID. Defaults to you. |
| `roulette kick` | One-in-six chance of kicking you. |
| `roulette ban` | One-in-six chance of banning you. |

### Moderators

The **Who can run it** column lists the Discord permission a member needs.

| Command | Description | Who can run it |
| --- | --- | --- |
| `kick <member> [reason]` | Kicks a member. | Kick Members |
| `ban <member> [reason]` | Bans a member. | Ban Members |
| `unban <user> [reason]` | Unbans a user. Accepts a user ID. | Ban Members |
| `modroulette <member> [kick\|ban]` | One-in-six chance of kicking or banning the member. | Kick Members, plus Ban Members to pick `ban` |
| `sm set <seconds>` | Sets slowmode in the current channel, up to 21600 seconds. | Manage Channels |
| `sm off` | Turns off slowmode in the current channel. | Manage Channels |

### Owner

These are text commands only. They have no slash equivalent.

| Command | Description |
| --- | --- |
| `>sync [~\|*\|^]` | Registers slash commands. See [Register the slash commands](#register-the-slash-commands). |
| `>reload <extension>` | Reloads one cog without restarting, for example `>reload cogs.fun`. |

## Update to a new version

On Linux:

```sh
cd Flyxbot
git pull
.venv/bin/python -m pip install --upgrade -e .
sudo systemctl restart flyxbot        # omit if you run it in a terminal
```

On Windows:

```powershell
cd Flyxbot
git pull
.venv\Scripts\python.exe -m pip install --upgrade -e .
```

Run `>sync ~` afterwards if the update added or renamed a command.

## Troubleshoot

| Symptom | Cause | Fix |
| --- | --- | --- |
| `No bot token found` | `.env` is missing or `DISCORD_TOKEN` is empty. | Follow [Configure the bot](#configure-the-bot). |
| `Discord rejected the token` | The token is wrong, or it was reset in the portal. | Reset the token in the Developer Portal and update `.env`. |
| `This bot needs the Server Members and Message Content intents` | The privileged intents are off. | Turn both on, as described in [Create the Discord application](#create-the-discord-application). |
| `ModuleNotFoundError: No module named 'discord'` | You started the bot with the system Python. | Use the interpreter in `.venv`. See [Start the bot](#start-the-bot). |
| Slash commands don't appear in Discord | They were never registered. | Run `>sync ~`. See [Register the slash commands](#register-the-slash-commands). |
| `>` commands do nothing, but slash commands work | The Message Content intent is off. | Turn it on in the Developer Portal, then restart the bot. |
| The bot replies "I don't have permission to do that" | The bot's role sits below the target member's role. | Move the bot's role higher in **Server Settings > Roles**. |
| The bot replies "You don't have permission to do that" | Your account is missing the Discord permission the command needs. | Check the **Who can run it** column in [Commands](#commands), then grant that permission to one of your roles. |
| `bad interpreter: /usr/bin/env bash^M` | The script has Windows line endings, usually from copying files instead of cloning. | Clone the repository with Git instead of copying it, or run `sed -i 's/\r$//' scripts/install.sh`. |
| `running scripts is disabled on this system` | PowerShell's execution policy blocks the installer. | Start it with `powershell -ExecutionPolicy Bypass -File scripts\install.ps1`. |
| `error: externally-managed-environment` | You ran `pip` outside the virtual environment. | Use `.venv/bin/pip`, or rerun `./scripts/install.sh`. |

To see what the bot is doing, read its log output. In a terminal it prints to the
screen. As a service, read it with `journalctl -u flyxbot -f`.

## Uninstall

1. Stop and remove the service, if you created one:

   ```sh
   sudo systemctl disable --now flyxbot
   sudo rm /etc/systemd/system/flyxbot.service
   sudo systemctl daemon-reload
   ```

1. Delete the repository folder.
1. In the Developer Portal, delete the application, or select **Reset Token** so
   the old token stops working.

Removing the bot from a server without deleting it: in Discord, open
**Server Settings > Members**, find the bot, and remove it.

## Modify the bot

### Project layout

| Path | Contents |
| --- | --- |
| `bot.py` | Startup, cog loading, and the global error handler. |
| `config.py` | Settings, read from the environment. |
| `cogs/fun.py` | Commands available to everyone. |
| `cogs/moderation.py` | Moderator commands. |
| `cogs/listeners.py` | Join handling and the owner's DM alerts. |
| `cogs/owner.py` | `sync` and `reload`. |
| `scripts/` | The installers. |

### Add a command

1. Create a `.py` file in `cogs/`.
1. Define a `commands.Cog` subclass that holds your commands.
1. Add an `async def setup(bot)` function that calls `await bot.add_cog(...)`.
1. Restart the bot, or run `>reload cogs.yourfile`.
1. Run `>sync ~` to register the slash version.

The bot loads every file in `cogs/` at startup, so there's no list to update.
Your command doesn't need its own error handler; the global handler in `bot.py`
reports the common failures.

### Check your changes

Install the development dependencies once:

```sh
.venv/bin/python -m pip install -e ".[dev]"
```

Then run the linter and formatter:

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format .
```
