import discord
from discord.ext import commands
from discord.ext.commands import Greedy, Context
from typing import Optional, Literal
import os

bot = commands.Bot(command_prefix=">", intents=discord.Intents.all())
#TOKEN = '(insert token here)'

@bot.event
async def on_ready():
    for root, _, files in os.walk("cogs"):
        for file in files:
            if file.endswith(".py"):
                await bot.load_extension(root.replace("\\", ".") + "." + file[:-3])

    await bot.tree.sync()

    print(f'Bot connected as {bot.user}')

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

bot.run(TOKEN)