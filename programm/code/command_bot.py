import os
import discord
import asyncio
import logging
from discord.ext import commands
from datetime import timedelta
from samples import TOKEN

GUILD = os.getenv('GC_TEST_GUILD')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.all()
intents.presences = True  #
intents.members = True  #
intents.message_content = True  #

with open('commands.txt', encoding='utf-8') as file:
    COMMANDS = [i.strip() for i in file.readlines()]
with open('BAN_WORDS', encoding='utf-8') as file:
    BAN_WORDS = [i.strip() for i in file.readlines()]


client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/', intents=intents)


class ModerBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




    @commands.command(aliases=['send_status'])
    async def status(self, ctx):
        for guild in bot.guilds:
            members = '\n - '.join([f"{member.name} ({member.status})" for member in guild.members])
            await ctx.send(f'Guild Members:\n - {members}')

    @commands.command(aliases=['check'])
    async def check_member(self, ctx, member: discord.Member):
        if member.activities:
            activity = member.activities[0]
        else:
            activity = None
        sting_n, string_t = '\n', '\t'
        await ctx.send(f"""Guild member {member.name}
status: {member.status}\ncolor:{member.color}
CustomActivity name: {activity}
id: {member.id}
roles:\n {sting_n.join([f'    {i}' for i in member.roles])}
is on time outed: {member.timed_out_until}""")


@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return
    for i in COMMANDS:
        if i in ctx.content.lower().split()[0]:
            break
    else:
        for i in BAN_WORDS:
            if i in ctx.content.lower():
                await timeout_member(ctx.channel, ctx.author)
                break
        else:
            await ctx.reply('я твой рот и жизнь ибал ежи')

async def timeout_member(channel, member: discord.User, reason='Иди ты нахуй, выблядок'):
    # проверяем на существование записи с id пользователя
    await member.timeout(timedelta(minutes=2), reason=reason)
    await channel.send(f'Участник {member.mention} был замучен.\nПричина: {reason}')


async def main():
    await bot.add_cog(ModerBot(bot))
    await bot.start(TOKEN)


asyncio.run(main())
