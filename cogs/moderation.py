"""Moderation commands.

Everything here gates on Discord's own permissions rather than on a configured role
ID, and resolves its targets from ``ctx``, so the whole cog works in a server it has
never seen before with no setup beyond inviting the bot.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Flyxbot

#: Discord's own ceiling for per-channel slowmode.
MAX_SLOWMODE_SECONDS = 21600


class Moderation(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Who to kick.", reason="Why they're being kicked.")
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason given",
    ) -> None:
        """Kicks a member"""
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} was kicked. Reason: `{reason}`")

    @commands.hybrid_command(description="Used to ban a member.")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        member="The user you want to ban.",
        reason="The reason you're banning them.",
    )
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason given",
    ) -> None:
        await member.ban(reason=reason, delete_message_seconds=0)
        await ctx.send(f"{member.mention} has been banned. Reason: `{reason}`")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="The user (or user ID) to unban.", reason="Why they're unbanned.")
    async def unban(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str = "No reason given",
    ) -> None:
        """Unbans a member from the server"""
        try:
            await ctx.guild.unban(user, reason=reason)
        except discord.NotFound:
            await ctx.send("That user isn't banned. Make sure you have the right ID.")
            return
        await ctx.send(f"{user.mention} was unbanned.")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Who to gamble with.", action="What happens if they lose.")
    async def modroulette(
        self,
        ctx: commands.Context,
        member: discord.Member,
        action: Literal["kick", "ban"] = "kick",
    ) -> None:
        """1 in 6 chance of getting a user kicked/banned"""
        # Kick permission gets you in the door; banning is a separate, bigger stick, so
        # it needs its own permission rather than being reachable through an argument.
        if action == "ban":
            for label, actor in (("You", ctx.author), ("I", ctx.me)):
                if not actor.guild_permissions.ban_members:
                    await ctx.send(f"{label} need the Ban Members permission to play ban roulette.")
                    return

        if random.randint(1, 6) != 6:
            await ctx.send(f"*click* - {member.mention} lives to see another day.")
            return

        await ctx.send(f"{member.mention} lost {action} roulette and was {action}ned.")
        if action == "kick":
            await member.kick(reason="Lost kick roulette.")
        else:
            await member.ban(reason="Lost ban roulette.", delete_message_seconds=0)

    @commands.hybrid_group(invoke_without_command=True)
    @commands.guild_only()
    async def sm(self, ctx: commands.Context) -> None:
        """Channel slowmode"""
        await ctx.send("Slowmode. Try `sm set <seconds>` or `sm off`.")

    @sm.command(description="Set the slowmode in the current channel.")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode interval in seconds.")
    async def set(
        self, ctx: commands.Context, seconds: commands.Range[int, 0, MAX_SLOWMODE_SECONDS]
    ) -> None:
        await ctx.channel.edit(slowmode_delay=seconds, reason=f"Slowmode by {ctx.author}")
        await ctx.send(f"Channel slowmode set to {seconds} seconds.")

    @sm.command(description="Disable slowmode in the current channel.")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def off(self, ctx: commands.Context) -> None:
        await ctx.channel.edit(slowmode_delay=0, reason=f"Slowmode off by {ctx.author}")
        await ctx.send("Channel slowmode disabled.")


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Moderation(bot))
