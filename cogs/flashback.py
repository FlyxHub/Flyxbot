"""Channel Flashback: every morning, repost a message from this day in each earlier year."""

from __future__ import annotations

import datetime as dt
import logging
import random
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from config import settings

if TYPE_CHECKING:
    from bot import Flyxbot

log = logging.getLogger(__name__)

TZ = ZoneInfo(settings.flashback_timezone)


def past_days(today: dt.date, first_year: int) -> list[tuple[int, dt.datetime, dt.datetime]]:
    """``(years ago, start, end)`` for today's date in each earlier year, newest first."""
    days = []
    for year in range(today.year - 1, first_year - 1, -1):
        try:
            start = dt.datetime.combine(today.replace(year=year), dt.time(), TZ)
        except ValueError:  # Feb 29 in a non-leap year
            continue
        days.append((today.year - year, start, start + dt.timedelta(days=1)))
    return days


def flashback_embed(message: discord.Message, years: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"{years} year{'s' if years != 1 else ''} ago today",
        description=message.content[:4096] or None,
        url=message.jump_url,
        timestamp=message.created_at,
    )
    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    for attachment in message.attachments:
        if (attachment.content_type or "").startswith("image/"):
            embed.set_image(url=attachment.url)
            break
    return embed


class Flashback(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.post.start()

    async def cog_unload(self) -> None:
        self.post.cancel()

    @tasks.loop(time=dt.time(9, tzinfo=TZ))
    async def post(self) -> int:
        """Post today's flashbacks and return how many went out."""
        source = self.bot.get_channel(settings.flashback_channel_id)
        target = self.bot.get_channel(settings.flashback_target_channel_id)
        if not all(isinstance(c, discord.abc.Messageable) for c in (source, target)):
            log.warning("Flashback channels not found; check the FLASHBACK_* IDs in .env")
            return 0

        posted = 0
        today = dt.datetime.now(TZ).date()
        # An uncaught error would stop the loop for good, not just skip today.
        try:
            days = past_days(today, source.created_at.astimezone(TZ).year)
            if not days:
                log.info("Flashback: #%s was created this year, so there's no past to show", source)
            for years, start, end in days:
                # ponytail: reads the whole day to pick one; fine until a day holds thousands.
                fetched = [m async for m in source.history(after=start, before=end, limit=None)]
                messages = [m for m in fetched if not m.author.bot]
                if not messages:
                    log.info(
                        "Flashback: no messages from people in #%s on %s (%d from bots)",
                        source,
                        start.date(),
                        len(fetched),
                    )
                    continue
                await target.send(embed=flashback_embed(random.choice(messages), years))
                posted += 1
        except discord.HTTPException:
            log.exception("Flashback failed")
        return posted

    @commands.command(name="flashback")
    @commands.is_owner()
    async def flashback_now(self, ctx: commands.Context) -> None:
        """Run today's Channel Flashback now instead of waiting for 9AM."""
        posted = await self.post()
        await ctx.send(f"Posted {posted} flashback(s). Check the log if you expected more.")

    @post.before_loop
    async def before_post(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: Flyxbot) -> None:
    if settings.flashback_channel_id and settings.flashback_target_channel_id:
        await bot.add_cog(Flashback(bot))


if __name__ == "__main__":
    # Leap day only lands in leap years; everything else once per earlier year.
    assert [y for y, _, _ in past_days(dt.date(2028, 2, 29), 2023)] == [4]
    days = past_days(dt.date(2026, 9, 28), 2024)
    assert [y for y, _, _ in days] == [1, 2]
    assert days[0][1] == dt.datetime(2025, 9, 28, tzinfo=TZ)
    assert days[0][2] - days[0][1] == dt.timedelta(days=1)
    print("ok")
