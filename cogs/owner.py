"""Owner-only maintenance commands.

These are prefix-only on purpose: `sync` is what registers the slash commands in
the first place, so it can't rely on them existing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Flyxbot


class Owner(commands.Cog):
    def __init__(self, bot: Flyxbot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    @commands.guild_only()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Literal["~", "*", "^", "!"] | None = None,
    ) -> None:
        """Sync the app command tree.

        No arguments syncs globally (slow to propagate). `~` syncs to this guild,
        `*` copies the global commands to this guild and syncs, `^` clears this
        guild's commands, `!` clears the global commands. Any guild IDs given are
        synced individually.

        Duplicate slash commands in a guild usually mean commands got registered
        both globally and to that guild (e.g. after a `*` sync). `>sync ^` then
        `>sync` fixes it: a global sync already overwrites the whole global set.
        """
        if not guilds:
            tree = ctx.bot.tree
            target = None if spec in (None, "!") else ctx.guild
            # The global tree is where the cogs registered their commands, so
            # clearing it would leave the next `>sync` with nothing to push.
            kept = tree.get_commands() if spec == "!" else []
            match spec:
                case "*":
                    tree.copy_global_to(guild=target)
                case "^" | "!":
                    tree.clear_commands(guild=target)
            try:
                synced = await tree.sync(guild=target)
            finally:
                for command in kept:
                    tree.add_command(command)

            where = "globally" if target is None else "to the current guild"
            await ctx.send(f"Synced {len(synced)} commands {where}.")
            return

        synced_guilds = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                synced_guilds += 1

        await ctx.send(f"Synced the tree to {synced_guilds}/{len(guilds)} guilds.")

    @commands.command()
    async def reload(self, ctx: commands.Context, extension: str) -> None:
        """Hot-reload a cog, e.g. `reload cogs.fun`."""
        try:
            await self.bot.reload_extension(extension)
        except commands.ExtensionError as exc:
            await ctx.send(f"Failed to reload `{extension}`: {exc}")
            return
        await ctx.send(f"Reloaded `{extension}`.")


async def setup(bot: Flyxbot) -> None:
    await bot.add_cog(Owner(bot))
