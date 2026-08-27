"""Moderation commands.

Permission gating is deliberately mixed: the Discord-native actions (kick, ban,
unban, lockdown) check Discord permissions, while the guild-specific ones check
for the moderator role from :mod:`config`.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import settings

if TYPE_CHECKING:
    from bot import Flyxbot

#: Discord's own ceiling for per-channel slowmode.
MAX_SLOWMODE_SECONDS = 21600

MODERATOR_ONLY = commands.has_role(settings.moderator_role_id)


class Moderation(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    def restriction_role(self, guild: discord.Guild) -> discord.Role | None:
        """The 'no images' role. Holding it *removes* the ability to post images."""
        return guild.get_role(settings.no_images_role_id)

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
    @MODERATOR_ONLY
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.describe(member="Who loses image perms.")
    async def takeimg(self, ctx: commands.Context, member: discord.Member) -> None:
        """Removes image perms from a user"""
        role = self.restriction_role(ctx.guild)
        if role is None:
            await ctx.send("The image restriction role is missing. Check NO_IMAGES_ROLE_ID.")
            return
        if role in member.roles:
            await ctx.send("That user does not have image perms to remove.")
            return

        await member.add_roles(role, reason=f"takeimg by {ctx.author}")
        await ctx.send(f"Successfully removed image perms from {member.mention}.")

    @commands.hybrid_command()
    @commands.guild_only()
    @MODERATOR_ONLY
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.describe(member="Who gets image perms back.")
    async def giveimg(self, ctx: commands.Context, member: discord.Member) -> None:
        """Grants image perms to a user"""
        role = self.restriction_role(ctx.guild)
        if role is None:
            await ctx.send("The image restriction role is missing. Check NO_IMAGES_ROLE_ID.")
            return
        if role not in member.roles:
            await ctx.send("That user already has image perms.")
            return

        await member.remove_roles(role, reason=f"giveimg by {ctx.author}")
        await ctx.send(f"Successfully granted image perms to {member.mention}.")

    @commands.hybrid_command()
    @commands.guild_only()
    @MODERATOR_ONLY
    @app_commands.describe(member="Who to gamble with.", action="What happens if they lose.")
    async def modroulette(
        self,
        ctx: commands.Context,
        member: discord.Member,
        action: Literal["kick", "ban"] = "kick",
    ) -> None:
        """1 in 6 chance of getting a user kicked/banned"""
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
    @MODERATOR_ONLY
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode interval in seconds.")
    async def set(
        self, ctx: commands.Context, seconds: commands.Range[int, 0, MAX_SLOWMODE_SECONDS]
    ) -> None:
        await ctx.channel.edit(slowmode_delay=seconds, reason=f"Slowmode by {ctx.author}")
        await ctx.send(f"Channel slowmode set to {seconds} seconds.")

    @sm.command(description="Disable slowmode in the current channel.")
    @commands.guild_only()
    @MODERATOR_ONLY
    @commands.bot_has_permissions(manage_channels=True)
    async def off(self, ctx: commands.Context) -> None:
        await ctx.channel.edit(slowmode_delay=0, reason=f"Slowmode off by {ctx.author}")
        await ctx.send("Channel slowmode disabled.")

    @commands.hybrid_group(invoke_without_command=True)
    @commands.guild_only()
    async def ld(self, ctx: commands.Context) -> None:
        """Channel lockdown"""
        await ctx.send("Lockdown. Try `ld enable` or `ld disable`.")

    async def _set_lockdown(self, ctx: commands.Context, *, locked: bool) -> None:
        role = ctx.guild.get_role(settings.lockdown_role_id)
        if role is None:
            await ctx.send("The lockdown role is missing. Check LOCKDOWN_ROLE_ID.")
            return

        state = "enabled" if locked else "lifted"
        await ctx.channel.set_permissions(
            role,
            view_channel=True,
            send_messages=not locked,
            reason=f"Lockdown {state} by {ctx.author}",
        )
        await ctx.send("Channel is now locked down." if locked else "Channel lockdown lifted.")

    @ld.command(description="Locks down a channel.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def enable(self, ctx: commands.Context) -> None:
        await self._set_lockdown(ctx, locked=True)

    @ld.command(description="Unlocks a channel from lockdown.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def disable(self, ctx: commands.Context) -> None:
        await self._set_lockdown(ctx, locked=False)


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Moderation(bot))
