"""Light-hearted commands available to everyone."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Flyxbot

#: A roulette round loses on exactly one of these faces.
ROULETTE_SIDES = 6

YES_EMOJI = "\N{WHITE HEAVY CHECK MARK}"
NO_EMOJI = "\N{NEGATIVE SQUARED CROSS MARK}"


def lost_roulette() -> bool:
    """True once every :data:`ROULETTE_SIDES` calls, on average."""
    return random.randint(1, ROULETTE_SIDES) == ROULETTE_SIDES


class Fun(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    async def poop(self, ctx: commands.Context) -> None:
        """Sends a funny message"""
        await ctx.send("*sharts*")

    @commands.hybrid_command()
    @app_commands.describe(num1="Lower bound.", num2="Upper bound.")
    async def number(self, ctx: commands.Context, num1: int, num2: int) -> None:
        """Gives you a random number between 2 given numbers"""
        if num1 >= num2:
            await ctx.send("The first number must be smaller than the second number.")
            return
        await ctx.send(f"Random number between {num1} and {num2} is {random.randint(num1, num2)}")

    @commands.hybrid_group(invoke_without_command=True)
    @commands.guild_only()
    async def roulette(self, ctx: commands.Context) -> None:
        """Games of chance with consequences"""
        await ctx.send("Roulette. Try `roulette kick` or `roulette ban`.")

    @roulette.command(description="Play a game of kick roulette.")
    @commands.guild_only()
    async def kick(self, ctx: commands.Context) -> None:
        if not lost_roulette():
            await ctx.send(f"*click* - {ctx.author.mention} lives to see another day.")
            return
        await ctx.send(f"{ctx.author.mention} lost kick roulette and was kicked.")
        await ctx.guild.kick(ctx.author, reason="Lost kick roulette.")

    @roulette.command(description="Play a game of ban roulette.")
    @commands.guild_only()
    async def ban(self, ctx: commands.Context) -> None:
        if not lost_roulette():
            await ctx.send(f"*click* - {ctx.author.mention} lives to see another day.")
            return
        await ctx.send(f"{ctx.author.mention} lost ban roulette and was banned.")
        await ctx.guild.ban(ctx.author, reason="Lost ban roulette.", delete_message_seconds=0)

    @commands.hybrid_command()
    async def coinflip(self, ctx: commands.Context) -> None:
        """Flips a coin"""
        await ctx.send(f"It's **{random.choice(('heads', 'tails'))}!**")

    @commands.hybrid_command()
    async def dice(self, ctx: commands.Context) -> None:
        """Rolls a 6-sided die"""
        await ctx.send(f"You rolled a **{random.randint(1, 6)}**")

    @commands.hybrid_command()
    @app_commands.describe(question="What you want people to vote on.")
    async def quickpoll(self, ctx: commands.Context, *, question: str) -> None:
        """Creates a poll with simple yes/no answers"""
        embed = discord.Embed(title=question[:256])
        embed.add_field(name="Yes", value=YES_EMOJI, inline=True)
        embed.add_field(name="No", value=NO_EMOJI, inline=True)
        embed.set_footer(text=f"Poll by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        message = await ctx.send(embed=embed)
        for emoji in (YES_EMOJI, NO_EMOJI):
            await message.add_reaction(emoji)

    @commands.hybrid_command()
    @app_commands.describe(member="Whose avatar to show. Defaults to you.")
    async def av(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        """Sends the avatar of a given user"""
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar for {member}")
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.describe(member="Who to look up. Defaults to you.")
    async def whois(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        """Shows some info about a given user"""
        member = member or ctx.author

        embed = discord.Embed(
            title=member.display_name,
            description=f"**User info for {member.mention}**",
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(
            name="Account created:",
            value=discord.utils.format_dt(member.created_at, "D"),
            inline=False,
        )
        embed.add_field(
            name="Date joined:",
            value=(
                discord.utils.format_dt(member.joined_at, "D") if member.joined_at else "Unknown"
            ),
            inline=False,
        )
        embed.add_field(name="Current nickname:", value=member.display_name, inline=False)
        embed.add_field(name="Real username:", value=str(member), inline=False)

        roles = [role.mention for role in reversed(member.roles) if not role.is_default()]
        embed.add_field(
            name=f"User roles ({len(roles)}):",
            value=" ".join(roles)[:1024] or "None",
            inline=False,
        )
        embed.set_footer(text=f"User ID: {member.id}")

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context) -> None:
        """Shows the current bot latency"""
        await ctx.send(f":ping_pong: Pong! Bot latency: **{self.bot.latency * 1000:.0f}ms**")


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Fun(bot))
