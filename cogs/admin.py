"""Server-owner commands for administering the bot itself.

Gated on being the owning guild's owner rather than a Discord permission: changing
the bot's presence isn't a permission Discord models (there's no "Manage Bot
Status"), and it affects the whole bot process, not just this server, so it stays
narrower than an Administrator check.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Flyxbot

ACTIVITY_TYPES: dict[str, discord.ActivityType] = {
    "playing": discord.ActivityType.playing,
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "competing": discord.ActivityType.competing,
}

STATUSES: dict[str, discord.Status] = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}


def is_guild_owner():
    async def predicate(ctx: commands.Context) -> bool:
        return ctx.guild is not None and ctx.author.id == ctx.guild.owner_id

    return commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    @commands.guild_only()
    @is_guild_owner()
    @app_commands.describe(
        presence="The online status to show.",
        activity_type="What kind of activity to show. Ignored if text is omitted.",
        text="The activity text, e.g. 'with fire'. Omit to clear the activity.",
    )
    async def status(
        self,
        ctx: commands.Context,
        presence: Literal["online", "idle", "dnd", "invisible"] = "online",
        activity_type: Literal["playing", "watching", "listening", "competing"] = "playing",
        *,
        text: str | None = None,
    ) -> None:
        """Sets the bot's online status and activity"""
        activity = discord.Activity(type=ACTIVITY_TYPES[activity_type], name=text) if text else None
        await self.bot.change_presence(status=STATUSES[presence], activity=activity)

        if activity is not None:
            await ctx.send(f"Status set to {presence}, {activity_type} **{text}**.")
        else:
            await ctx.send(f"Status set to {presence} with no activity.")


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Admin(bot))
