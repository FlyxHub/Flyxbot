import discord
from discord.ext import commands

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        blacklist = [787885272594513950, 514143503471738910]

        if member.id in blacklist:
            await member.add_roles(discord.utils.get(member.guild.roles, id=1041203946817081365))
            return
        else:
            return
    

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        flyx = discord.utils.get(message.guild.members, id=307688449811415041)
        if flyx in message.mentions:
            embed = discord.Embed(title=f'Message mentioning you deleted in {message.guild.name}').set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name='Sent by:', value=message.author, inline=True)
            embed.add_field(name='In channel:', value=message.channel.mention, inline=True)
            embed.add_field(name='Message content:', value=message.content, inline=False)
            embed.set_footer(text=f"Sender ID: {message.author.id}")
            await flyx.send(embed=embed)
            return
        else:
            return
    
        
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        flyx = discord.utils.get(before.guild.members, id=307688449811415041)
        if flyx in before.mentions:
            embed = discord.Embed(title=f'Message mentioning you edited in {before.guild.name}').set_thumbnail(url=before.author.display_avatar.url)
            embed.add_field(name='Sent by:', value=before.author, inline=True)
            embed.add_field(name='In channel:', value=before.channel.mention, inline=True)
            embed.add_field(name='Original message:', value=before.content, inline=False)
            embed.add_field(name='Edited message:', value=after.content, inline=False)
            embed.set_footer(text=f"Sender ID: {before.author.id}")
            await flyx.send(embed=embed)
            return
        else:
            return


async def setup(bot):
    await bot.add_cog(Listeners(bot))
