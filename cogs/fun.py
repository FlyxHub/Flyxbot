import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import math

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    
    @commands.hybrid_command()
    async def poop(self, ctx):
        """Sends a funny message"""
        await ctx.send('*sharts*')
        return
    
    
    @commands.hybrid_command()
    async def number(self, ctx, num1: int, num2: int):
        """Gives you a random number between 2 given numbers"""
        if num1 >= num2:
            await ctx.send('The first number must be smaller than the second number.')
            return
        else:
            await ctx.send(f"Random number between {num1} and {num2} is {random.randint(num1, num2)}")
            return
    @number.error
    async def numberError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Error, missing required arguments. Try adding a number, followed by a bigger number in your command.')
            return

    @commands.hybrid_group()
    async def roulette(self, ctx):  
        await ctx.send('Roulette')
        return
    @roulette.command(description='Play a game of kick roulette.')
    async def kick(self, ctx):
        roll = random.randint(0, 6)
        if roll == 6:
            await ctx.author.kick(reason='Lost kick roulette.')
            await ctx.send(f"{ctx.author.mention} lost kick roulette and was kicked.")
        else:
            await ctx.send(f"*click* - {ctx.author.mention} lives to see another day.")
        return
    @roulette.command(description='Play a game of ban roulette.')
    async def ban(self, ctx):
        roll = random.randint(0, 6)
        if roll == 6:
            await ctx.author.ban(reason='Lost ban roulette.')
            await ctx.send(f"{ctx.author.mention} lost ban roulette and was banned.")
        else:
            await ctx.send(f"*click* - {ctx.author.mention} lives to see another day.")
        return

    @commands.hybrid_command()
    async def coinflip(self, ctx):
        """Flips a coin"""
        if random.randint(1, 2) == 1:
            await ctx.send("It's **heads!**")
            return
        else:
            await ctx.send("It's **tails!**")
            return


    @commands.hybrid_command()
    async def dice(self, ctx):
        """Rolls a 6-sided die"""
        outcome = random.randint(1, 6)
        await ctx.send(f'You rolled a **{outcome}**')
        return
    

    @commands.hybrid_command()
    async def quickpoll(self, ctx, *, question):
        """Creates a poll with simple yes/no answers"""
        emojis = [u"\u2705", u"\u274E"]
        toEmbed = discord.Embed(title=question)
        toEmbed.add_field(name='Yes', value=":white_check_mark:", inline=True)
        toEmbed.add_field(name='No', value=":negative_squared_cross_mark:", inline=True)
        toEmbed.set_footer(text=f'Poll by {ctx.author}', icon_url=ctx.author.display_avatar.url)
        message = await ctx.send(embed=toEmbed)
        for emoji in emojis:
            await message.add_reaction(emoji)
            time.sleep(.2)
        return


    @commands.hybrid_command()
    async def av(self, ctx, member: discord.Member=None):
        """Sends the avatar of a given user"""
        member = member or ctx.author

        toEmbed = discord.Embed(title=f"Avatar for {member}")
        toEmbed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=toEmbed)
        return


    @commands.hybrid_command()
    async def whois(self, ctx, member: discord.Member=None):
        """Shows some info about a given user"""
        member = member or ctx.author

        toSend = discord.Embed(title=f"{member.display_name}", description=f"**User info for {member.mention}**").set_thumbnail(url=member.display_avatar.url).set_author(name=member, icon_url=member.display_avatar.url)
        toSend.add_field(name='Account created:', value=member.created_at.strftime("%b %d, %Y"), inline=False)
        toSend.add_field(name='Date joined:', value=member.joined_at.strftime("%b %d, %Y"), inline=False)
        toSend.add_field(name='Current nickname:', value=member.display_name, inline=False)
        toSend.add_field(name='Real username:', value=member, inline=False)

        roles = []
        for role in member.roles:
            if role.name != '@everyone':
                roles.append(role.mention)
            else:
                pass
        roles.reverse()
        toSend.add_field(name=f"User roles ({len(member.roles)-1}):", value=" ".join(roles), inline=False)  

        toSend.set_footer(text=f'User ID: {member.id}')

        await ctx.send(embed=toSend)
        return
    @whois.error
    async def whoisError(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send('Error, user not found. Try a real user next time?')


    @commands.hybrid_command(name='ping')
    async def ping(self, ctx):
        """Shows the current bot latency"""
        latency = math.trunc(self.bot.latency*1000)
        await ctx.send(f":ping_pong: Pong! Bot latency: **{latency}MS**")
        return

async def setup(bot):
    await bot.add_cog(Fun(bot))