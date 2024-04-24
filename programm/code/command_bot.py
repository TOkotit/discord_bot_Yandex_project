import os
import discord
import asyncio
import traceback
import logging
import sqlite3
import pymorphy3
from sign_in import SignIn
from discord.ext import commands
from datetime import timedelta
from samples import TOKEN

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

morph = pymorphy3.MorphAnalyzer()

intents = discord.Intents.all()
intents.presences = True
intents.members = True
intents.message_content = True

db = sqlite3.connect("../server_files/database/1984_bot_database.db")
cursor = db.cursor()

with open('commands.txt', encoding='utf-8') as file:
    COMMANDS = [i.strip() for i in file.readlines()]

PERMISSIONS_FOR_MEMBERS = {
    'freedom of speech': True,
    'inspection': True,
    'surveillance': True
}
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{guild.id}'(
        id INT PRIMARY KEY NOT NULL,
        warning_count INT,
        mute_count INT)""")

    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключились к чату:\n'
            f'{guild.name}(id: {guild.id})')

    for guild in bot.guilds:
        id_members = cursor.execute(f"""SELECT id FROM '{guild.id}'""").fetchall()
        for member in guild.members:
            if member.id not in id_members:
                cursor.execute(f"INSERT OR IGNORE INTO '{guild.id}' VALUES(?, ?, ?)", (int(member.id), 0, 0))
                db.commit()

    for guild in bot.guilds:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        for i in guild.channels:
            if i.name == '1984' and i.overwrites == overwrites:
                await i.send(f'Бот запущен')
                break
        else:
            await guild.create_text_channel('1984', overwrites=overwrites)
            for i in guild.channels:
                if i.name == '1984' and i.overwrites == overwrites:
                    await i.send('Бот запущен, это основной канал для его использования')
                    break
    await bot.tree.sync()
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")


@bot.event
async def on_guild_join(guild):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{guild.id}'(
       id INT PRIMARY KEY NOT NULL,
       warning_count INT,
       mute_count INT)""")
    id_members = cursor.execute(f"""SELECT id FROM '{guild.id}'""").fetchall()
    for member in guild.members:
        if member.id not in id_members:
            cursor.execute(f"INSERT OR IGNORE INTO '{guild.id}' VALUES(?, ?, ?)", (int(member.id), 0, 0))
            db.commit()

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    for i in guild.channels:
        if i.name == '1984' and i.overwrites == overwrites:
            await i.send(f'Бот запущен')
            break
    else:
        await guild.create_text_channel('1984', overwrites=overwrites)
        for i in guild.channels:
            if i.name == '1984' and i.overwrites == overwrites:
                await i.send('Бот запущен, это основной канал для его использования')
                break


@bot.event
async def on_error(event, *args, **kwargs):
    error_message = traceback.format_exc()
    print(f"ошибка {event}: {error_message}")


@bot.listen()
async def on_message(ctx):
    if ctx.author == bot.user:
        return
    with open('BAN_WORDS', encoding='utf-8') as file:
        BAN_WORDS = [i.strip() for i in file.readlines()]
    for i in BAN_WORDS:
        if morph.parse(i)[0].normal_form in ctx.content.lower():
            if ctx.author.guild_permissions.administrator:
                await ctx.channel.send('Склоняю колено перед админом и прощаю ему все грехи', reference=ctx)
            else:
                for guild in bot.guilds:
                    warg_count = cursor.execute(f"""SELECT warning_count FROM '{guild.id}'
                    WHERE id = {ctx.author.id}""").fetchone()[0]
                    if warg_count == 3:
                        cursor.execute(f"""UPDATE '{guild.id}'
                    SET warning_count = 0
                    WHERE id = {ctx.author.id}""")
                        cursor.execute(f"""UPDATE '{guild.id}'
                    SET mute_count = mute_count + 1
                    WHERE id = {ctx.author.id}""")
                        db.commit()
                        await timeout_member(guild.id, ctx.channel, ctx.author)
                    else:
                        dict_warnings = {
                            0: 'осталось 2 предупреждения',
                            1: 'осталось 1 предупреждение',
                            2: 'последнее предупреждение'
                        }
                        cursor.execute(f"""UPDATE '{guild.id}'
    SET warning_count = warning_count + 1
    WHERE id = {ctx.author.id}""")
                        db.commit()
                        await ctx.channel.send(
                            f'{ctx.author.mention}, так больше не пиши, {dict_warnings[warg_count]}',
                            reference=ctx)
                await ctx.delete()
            return


@bot.tree.command(name='дискорднй_двор', description='запрещает пользователям использовать бота')
async def dictatorship_on(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('Судьба, власть, коварство... и 3 банановые республики')
        for i in PERMISSIONS_FOR_MEMBERS:
            PERMISSIONS_FOR_MEMBERS[i] = False


@bot.tree.command(name='светлое_будущее', description='разрешает пользователям использовать бота')
async def dictatorship_off(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('у народа теперь есть власть')
        for i in PERMISSIONS_FOR_MEMBERS:
            PERMISSIONS_FOR_MEMBERS[i] = True


@bot.tree.command(name='send_status', description='send status of member')
async def status(interaction: discord.Interaction, role: discord.Role):
    if not PERMISSIONS_FOR_MEMBERS['surveillance']:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('У тебя здесь нет власти')
            return
    for guild in bot.guilds:
        if role:

            members = '\n - '.join(
                [f"{member.name} ({member.status})" for member in guild.members if role in member.roles])
        else:
            members = '\n - '.join(
                [f"{member.name} ({member.status})" for member in guild.members if role in member.roles])
        await interaction.response.send_message('Всё готово, вот:')
        await interaction.channel.send(f'Guild Member:\n - {members}')


@bot.tree.command(name='check', description='send information of member')
async def check_member(interaction: discord.Interaction, member: discord.Member):
    if not PERMISSIONS_FOR_MEMBERS['inspection']:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('У тебя здесь нет власти')
            return
    if member.activities:
        activity = member.activities[0]
    else:
        activity = None
    sting_n, string_t = '\n', '\t'
    await interaction.response.send_message('Всё готово, вот:')
    await interaction.channel.send(f"""Guild member {member.name}
status: {member.status}\ncolor:{member.color}
CustomActivity name: {activity}
id: {member.id}
roles:\n {sting_n.join([f'    {i}' for i in member.roles])}
is on time outed: {member.timed_out_until}""")


@bot.tree.command(name='begin_the_usurpation', description='используйте эту команду для авторизации и запуска бота')
async def begin_bot(interaction: discord.Interaction):
    sign_window = SignIn()
    await interaction.response.send_modal(sign_window)


async def timeout_member(guild_id, channel, member: discord.User, reason='Так надо, объективно'):
    mute_count = cursor.execute(f"""SELECT mute_count FROM '{guild_id}'
WHERE id = {member.id}""").fetchone()[0]
    if mute_count > 50:
        mute_count = 50
    await member.timeout(timedelta(minutes=2 * (mute_count // 1.5)), reason=reason)
    await channel.send(f'Участник {member.mention} был замучен.\nПричина: {reason}')


bot.run(TOKEN)
