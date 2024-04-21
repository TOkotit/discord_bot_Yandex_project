import os
import discord
import asyncio
import logging
import sqlite3
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
intents.presences = True
intents.members = True
intents.message_content = True

db = sqlite3.connect("../assets/database/ban_members.db")
cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS warnings(
id INT PRIMARY KEY NOT NULL,
warning_count INT)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS mutes (
id INT PRIMARY KEY NOT NULL,
is_muted TEXT,
FOREIGN KEY (id) REFERENCES warnings(id))""")

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
    print('get in')
    if ctx.author == bot.user:
        return
    for i in COMMANDS:
        if i in ctx.content.lower().split()[0]:
            break
    else:
        print('check bans')
        for i in BAN_WORDS:
            if i in ctx.content.lower():
                warg_count = cursor.execute(f"""SELECT warning_count FROM warnings
                WHERE id = {ctx.author.id}""").fetchone()[0]
                if warg_count == 3:
                    cursor.execute(f"""UPDATE warnings
                SET warning_count = 0
                WHERE id = {ctx.author.id}""")
                    cursor.execute(f"""UPDATE mutes
                SET is_muted = 'True'
                WHERE id = {ctx.author.id}""")
                    db.commit()
                    await timeout_member(ctx.channel, ctx.author)
                else:
                    print('warning')
                    cursor.execute(f"""UPDATE warnings
SET warning_count = {warg_count + 1}
WHERE id = {ctx.author.id}""")
                    db.commit()
                    await ctx.channel.send(f'Так больше не пиши, отсалось {3 - warg_count - 1} предупреждений', reference=ctx)
                await ctx.delete()


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключились к чату:\n'
            f'{guild.name}(id: {guild.id})')
    id_members = cursor.execute("""SELECT id FROM warnings""").fetchall()
    for guild in bot.guilds:
        for member in guild.members:
            if member.id not in id_members:
                cursor.execute("INSERT OR IGNORE INTO warnings VALUES(?, ?)", (int(member.id), 0))
                db.commit()
                cursor.execute("INSERT OR IGNORE INTO mutes VALUES(?, ?)", (int(member.id), 'False'))
                db.commit()



async def timeout_member(channel, member: discord.User, reason='Так надо, объективно'):
    # проверяем на существование записи с id пользователя
    await member.timeout(timedelta(minutes=2), reason=reason)
    await channel.send(f'Участник {member.mention} был замучен.\nПричина: {reason}')


async def main():
    await bot.add_cog(ModerBot(bot))
    await bot.start(TOKEN)


asyncio.run(main())
