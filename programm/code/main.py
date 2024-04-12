import os
import discord
import asyncio
import logging
from discord.ext import commands
from TOKEN import TOKEN

GUILD = os.getenv('GC_TEST_GUILD')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class ModerBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['send_status'])
    async def status(self, ctx):
        for guild in bot.guilds:
            members = '\n - '.join([f"{member.name} ({member.status})" for member in guild.members])
            await ctx.send(f'Guild Members:\n - {members}')
    @commands.command(aliases=['check'])
    async def check_member(self, ctx, name=None):
        if name is None:
            await ctx.send(f'Не указано имя пользователя, чекни мать')
        else:
            for guild in bot.guilds:
                for member in guild.members:
                    if member.name.lower() == name.lower():
                        break
            sting_n, string_t = '\n', '\t'
            await ctx.send(f"""Guild member {name}
status: {member.status}\ncolor:{member.color}
CustomActivity name: {member.activities[0]}
id: {member.id}
roles:\n {sting_n.join([f'    {i}' for i in member.roles])}
is on time outed: {member.timed_out_until}""")

intents = discord.Intents.all()
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)


async def main():
    await bot.add_cog(ModerBot(bot))
    await bot.start(TOKEN)


asyncio.run(main())
