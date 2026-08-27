"""Passive gateway listeners: DM alerts when a message mentioning the owner changes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from config import settings

if TYPE_CHECKING:
    from bot import Flyxbot

log = logging.getLogger(__name__)

#: Discord rejects embed field values longer than this.
MAX_FIELD_LENGTH = 1024


def field_value(content: str) -> str:
    """Embed fields can't be empty, and can't exceed the length limit."""
    if not content:
        return "*(no text content)*"
    if len(content) <= MAX_FIELD_LENGTH:
        return content
    return content[: MAX_FIELD_LENGTH - 1] + "\N{HORIZONTAL ELLIPSIS}"


class Listeners(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    def mentions_owner(self, message: discord.Message) -> bool:
        return any(user.id == settings.owner_user_id for user in message.mentions)

    async def alert_owner(self, embed: discord.Embed) -> None:
        """DM the configured owner, tolerating closed DMs."""
        owner = self.bot.get_user(settings.owner_user_id)
        if owner is None:
            try:
                owner = await self.bot.fetch_user(settings.owner_user_id)
            except discord.HTTPException:
                log.warning("Could not resolve owner %s", settings.owner_user_id)
                return

        try:
            await owner.send(embed=embed)
        except discord.Forbidden:
            log.warning("Owner %s has DMs closed", owner)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot or not self.mentions_owner(message):
            return

        embed = discord.Embed(title=f"Message mentioning you deleted in {message.guild.name}")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Sent by:", value=str(message.author), inline=True)
        embed.add_field(name="In channel:", value=message.channel.mention, inline=True)
        embed.add_field(name="Message content:", value=field_value(message.content), inline=False)
        embed.set_footer(text=f"Sender ID: {message.author.id}")
        await self.alert_owner(embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        # Edit events also fire for embed/attachment updates, where nothing was typed.
        if before.content == after.content:
            return
        if before.guild is None or before.author.bot or not self.mentions_owner(before):
            return

        embed = discord.Embed(title=f"Message mentioning you edited in {before.guild.name}")
        embed.set_thumbnail(url=before.author.display_avatar.url)
        embed.add_field(name="Sent by:", value=str(before.author), inline=True)
        embed.add_field(name="In channel:", value=before.channel.mention, inline=True)
        embed.add_field(name="Original message:", value=field_value(before.content), inline=False)
        embed.add_field(name="Edited message:", value=field_value(after.content), inline=False)
        embed.set_footer(text=f"Sender ID: {before.author.id}")
        await self.alert_owner(embed)


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Listeners(bot))
