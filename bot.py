"""Entry point for Flyxbot."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import settings

log = logging.getLogger("flyxbot")

COGS_DIR = Path(__file__).parent / "cogs"

#: Errors that are noise rather than something the user needs to hear about.
SILENT_ERRORS = (commands.CommandNotFound, commands.DisabledCommand)


def _from_api_error(exc: BaseException) -> str | None:
    """Message for an exception raised *inside* a command body."""
    match exc:
        case discord.Forbidden():
            return "I don't have permission to do that. Check my role position."
        case discord.NotFound():
            return "Discord couldn't find that. Double-check the ID."
        case _:
            return None


def friendly_error(error: BaseException) -> str | None:
    """Map an error onto a user-facing message, or ``None`` if it's unexpected."""
    match error:
        case commands.HybridCommandError():
            # A slash invocation of a hybrid command wraps the real error twice.
            return friendly_error(getattr(error.original, "original", error.original))
        case commands.MissingRequiredArgument():
            return f"Missing required argument: `{error.param.name}`."
        case commands.MissingRequiredFlag():
            return f"Missing required argument: `{error.flag.name}`."
        case commands.MissingPermissions() | commands.BotMissingPermissions():
            missing = ", ".join(perm.replace("_", " ") for perm in error.missing_permissions)
            who = "I don't" if isinstance(error, commands.BotMissingPermissions) else "You don't"
            return f"{who} have permission to do that (missing: {missing})."
        case commands.MissingRole() | commands.MissingAnyRole():
            return "You don't have the role required for that command."
        case commands.NotOwner():
            return "That command is owner-only."
        case commands.NoPrivateMessage():
            return "That command only works inside a server."
        case commands.MemberNotFound() | commands.UserNotFound():
            return "I can't find that user. Are you sure you have the right person?"
        case commands.RoleNotFound() | commands.ChannelNotFound() | commands.RangeError():
            return str(error)
        case commands.CommandOnCooldown():
            return f"That command is on cooldown. Try again in {error.retry_after:.1f}s."
        case (
            commands.BadArgument()
            | commands.BadUnionArgument()
            | commands.BadLiteralArgument()
            | commands.UserInputError()
        ):
            return str(error) or "I couldn't understand one of those arguments."
        case commands.CheckFailure():
            return "You can't use that command here."
        case commands.CommandInvokeError() | app_commands.CommandInvokeError():
            return _from_api_error(error.original)
        case _:
            return _from_api_error(error)


class Flyxbot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True  # on_member_join, member lookups
        intents.message_content = True  # prefix commands + edit/delete logging
        super().__init__(
            command_prefix=commands.when_mentioned_or(settings.command_prefix),
            intents=intents,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
        )

    async def setup_hook(self) -> None:
        """Runs once, before the gateway connects. Cogs load here, not in on_ready."""
        for path in sorted(COGS_DIR.glob("*.py")):
            if path.stem.startswith("_"):
                continue
            module = f"{COGS_DIR.name}.{path.stem}"
            try:
                await self.load_extension(module)
            except commands.ExtensionError:
                log.exception("Failed to load extension %s", module)
            else:
                log.info("Loaded extension %s", module)

        self.tree.on_error = self.on_tree_error

    async def on_ready(self) -> None:
        log.info("Connected as %s (id=%s)", self.user, getattr(self.user, "id", "?"))

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """One handler for every command; individual commands don't need their own."""
        if isinstance(error, SILENT_ERRORS):
            return
        if ctx.command is not None and ctx.command.has_error_handler():
            return
        if ctx.cog is not None and ctx.cog.has_error_handler():
            return

        message = friendly_error(error)
        if message is None:
            log.error("Unhandled error in command %s", ctx.command, exc_info=error)
            message = "Something went wrong running that command."

        with contextlib.suppress(discord.HTTPException):
            await ctx.send(message, ephemeral=True)

    async def on_tree_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Catches app-command errors that never pass through a Context."""
        message = friendly_error(error)
        if message is None:
            log.error("Unhandled app command error", exc_info=error)
            message = "Something went wrong running that command."

        send = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        with contextlib.suppress(discord.HTTPException):
            await send(message, ephemeral=True)


async def main() -> None:
    discord.utils.setup_logging(level=logging.INFO)

    if not settings.token:
        sys.exit(
            "No bot token found. Set DISCORD_TOKEN in the environment or in a .env file "
            "(see .env.example)."
        )

    try:
        async with Flyxbot() as bot:
            await bot.start(settings.token)
    except discord.LoginFailure:
        sys.exit("Discord rejected the token. Check DISCORD_TOKEN.")
    except discord.PrivilegedIntentsRequired:
        sys.exit(
            "This bot needs the Server Members and Message Content intents. Enable them "
            "under Bot -> Privileged Gateway Intents in the Discord Developer Portal."
        )


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
