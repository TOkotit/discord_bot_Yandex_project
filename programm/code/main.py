import os
import discord
import asyncio
import logging
from discord.ext import commands
from components import TOKEN, command_prefix

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
print('\n\n\n\ncommand\n\n\n\n\n')


class CommandBot(commands.Cog):
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
            await ctx.send(f'Не указано имя пользователя')
        else:
            for guild in bot.guilds:
                for member in guild.members:
                    if member.name.lower() == name.lower():
                        break
            sting_n, string_t = '\n', '\t'
            if member.activities:
                activity = member.activities[0]
            else:
                activity = None
            await ctx.send(f"""Guild member {name}
status: {member.status}\ncolor:{member.color}
CustomActivity name: {activity}
id: {member.id}
roles:\n {sting_n.join([f'    {i}' for i in member.roles])}
is on time outed: {member.timed_out_until}""")


intents = discord.Intents.all()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=command_prefix, intents=intents)


async def bots_run():
    await bot.add_cog(CommandBot(bot))
    await bot.start(TOKEN)


asyncio.run(bots_run())
