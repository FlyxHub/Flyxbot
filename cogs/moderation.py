import discord
from discord import app_commands
from discord.ext import commands
import random
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member):
        """Kicks a member"""
        await member.kick()
        await ctx.send('Member was kicked')
        return
    @kick.error
    async def kickError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Missing required argument. Try pinging or pasting the ID of a member to kick.')
            return
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("I can't kick that user.")
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the role required for that command.")
            return
    
    class banFlags(commands.FlagConverter):
        member:discord.Member
        reason:str='No reason given'
    @commands.hybrid_command(description='Used to ban a member.')
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member='The user you want to ban.',
        reason="The reason you're banning them.",
    )
    async def ban(self, ctx, flags: banFlags):
        await flags.member.ban(reason=flags.reason)
        await ctx.send(f'{flags.member.mention} has been banned. Reason: `{flags.reason}`')
        return
    @ban.error
    async def banError(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("That user is either already banned, or doesn't exist. Make sure you have the right ID.")
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send("You must use the ID of the user you want to unban.")
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the role required for that command.")
            return

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, id: int):
        """Unbans a member from the server"""
        user = await self.bot.fetch_user(id)
        await ctx.guild.unban(user)
        await ctx.send('Member was unbanned')
        return
    @unban.error
    async def unbanError(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("That user is either not banned, or doesn't exist. Make sure you have the right ID.")
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send("You must use the ID of the user you want to unban.")
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the role required for that command.")
            return


    @commands.hybrid_command()
    @commands.has_role(1042085580034539580)
    async def takeimg(self, ctx, member: discord.Member):
        """Removes image perms from a user"""
        if discord.utils.get(ctx.guild.roles, id=1041203946817081365) not in member.roles:
            await member.add_roles(discord.utils.get(ctx.guild.roles, id=1041203946817081365))
            await ctx.send(f"Successfully removed image perms from {member.mention}.")
            return
        else:
            await ctx.send('That user does not have image perms to remove.')
            return
    @takeimg.error
    async def takeimgError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Missing required argument. You need to give a member to remove image perms from.')
            return
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I can't find that user. Are you sure you have the right person?")
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the role required for that command.")
            return
            

    @commands.hybrid_command()
    @commands.has_role(1042085580034539580)
    async def giveimg(self, ctx, member: discord.Member):
        """Grants image perms to a user"""
        if discord.utils.get(ctx.guild.roles, id=1041203946817081365) in member.roles:
            await member.remove_roles(discord.utils.get(ctx.guild.roles, id=1041203946817081365))
            await ctx.send(f"Successfully granted image perms to {member.mention}.")
            return
        else:
            await ctx.send('That user already has image perms')
            return
    @giveimg.error
    async def giveimgError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Missing required argument. You need to give a member to grant image perms to.')
            return
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I can't find that user. Are you sure you have the right person?")
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the role required for that command.")
            return


    @commands.hybrid_command()
    @commands.has_role(1042085580034539580)
    async def modroulette(self, ctx, member: discord.Member, action='kick'):
        """1 in 6 chance of getting a user kicked/banned"""
        outcome = random.randint(1, 7)
        if outcome == 6:
            if action.lower() == 'kick':
                await member.kick(reason='Lost kick roulette.')
                await ctx.send(f"{member.mention} lost kick roulette and was kicked.")
                return
            elif action.lower() == 'ban':
                await member.ban(reason='Lost kick roulette.')
                await ctx.send(f"{member.mention} lost ban roulette and was banned.")
                return
        else:
            await ctx.send(f'*click* - {member.mention} lives to see another day.')
            return
    @modroulette.error
    async def rouletteError(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send("Error, missing permissions. I can't kick or ban that user")
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Error, missing required argument.')
            return
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send('Error, member not found.')
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Error, bad argument.')
            return
        elif isinstance(error, commands.MissingRole):
            await ctx.send("Error, you don't have the required role to do that.")
            return


    @commands.hybrid_group()
    async def sm(self, ctx):
        await ctx.send('Slowmode')
        return
    class smFlags(commands.FlagConverter):
        seconds:int
    @sm.command(description='Set the slowmode in the current channel.')
    @commands.has_role(1042085580034539580)
    @app_commands.describe(
        seconds="Slowmode interval in seconds.",
    )
    async def set(self, ctx, flags:smFlags):
        await ctx.channel.edit(slowmode_delay=flags.seconds)
        await ctx.send(f'Channel slowmode set to {flags.seconds} seconds.')
        return
    @sm.command(description='Disable slowmode in the current channel.')
    @commands.has_role(1042085580034539580)
    async def off(self, ctx):
        await ctx.channel.edit(slowmode_delay=0)
        await ctx.send(f'Channel slowmode disabled.')
        return
    
    @commands.hybrid_group()
    async def ld(self, ctx):
        await ctx.send('Lockdown')
        return
    @ld.command(description='Locks down a channel.')
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.get_role(1036799478608429116), view_channel=True, send_messages=False)
        await ctx.send('Channel is now locked down.')
        return
    @ld.command(description='Unlocks a channel from lockdown.')
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.get_role(1036799478608429116), view_channel=True, send_messages=True)
        await ctx.send('Channel lockdown lifted.')
        return

    @commands.hybrid_group()
    async def mute(self, ctx):
        await ctx.send('Mute')
        return
    
async def setup(bot):
    await bot.add_cog(Moderation(bot))