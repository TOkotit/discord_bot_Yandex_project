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

DICT_FOR_DB = {
    'True': True,
    'False': False
}
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{guild.id}'(
        id INT PRIMARY KEY NOT NULL,
        warning_count INT,
        mute_count INT)""")
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS permissions(
id INT PRIMARY KEY NOT NULL UNIQUE,
moderation TEXT,
inspection TEXT,
surveillance TEXT,
CAN_USE TEXT)""")

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
                cursor.execute(
                    f"""INSERT OR IGNORE INTO permissions VALUES({guild.id}, 'True', 'True', 'Ture', 'False')""")
                db.commit()
    data_base_keys = sqlite3.connect('../server_files/database/keywords.db')
    curs_keys = data_base_keys.cursor()
    for guild in bot.guilds:
        if guild.id in [i[0] for i in curs_keys.execute(f"""SELECT id FROM keys""").fetchall()]:
            is_registr = curs_keys.execute(f"""SELECT IS_REGISTRATED FROM keys
    WHERE id = {guild.id}""").fetchone()[0]
            cursor.execute(f"""UPDATE permissions
    SET CAN_USE = '{is_registr}'
    WHERE id = {guild.id}""")
            db.commit()
        else:
            cursor.execute(f"""UPDATE permissions
SET CAN_USE = 'False'
WHERE id = {guild.id}""")
            db.commit()
    data_base_keys.close()
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
                    await i.send(
                        'Бот запущен, это основной канал для его использования.\nТак же, вы можете использовать его и в других каналах')
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
            cursor.execute(
                f"""INSERT OR IGNORE INTO permissions VALUES({guild.id}, 'True', 'True', 'Ture', 'False')""")
            db.commit()

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    data_base_keys = sqlite3.connect('../server_files/database/keywords.db')
    curs_keys = data_base_keys.cursor()
    for guild in bot.guilds:
        if guild.id in [i[0] for i in curs_keys.execute(f"""SELECT id FROM keys""").fetchall()]:
            is_registr = curs_keys.execute(f"""SELECT IS_REGISTRATED FROM keys
    WHERE id = {guild.id}""").fetchone()[0]
            cursor.execute(f"""UPDATE permissions
    SET CAN_USE = '{is_registr}'
    WHERE id = {guild.id}""")
            db.commit()
    data_base_keys.close()
    for i in guild.channels:
        if i.name == '1984' and i.overwrites == overwrites:
            await i.send(f'Бот запущен')
            break
    else:
        await guild.create_text_channel('1984', overwrites=overwrites)
        for i in guild.channels:
            if i.name == '1984' and i.overwrites == overwrites:
                await i.send(
                    'Бот запущен, это основной канал для его использования.\nТак же, вы можете использовать его и в других каналах')
                break


@bot.event
async def on_error(event, *args, **kwargs):
    error_message = traceback.format_exc()
    print(f"ошибка {event}: {error_message}")


@bot.listen()
async def on_message(ctx):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
WHERE id = {ctx.guild.id}""").fetchone()[0]]:
        if not DICT_FOR_DB[cursor.execute(f"""SELECT moderation FROM permissions
WHERE id = {ctx.guild.id}""").fetchone()[0]]:
            if ctx.author == bot.user:
                return
            guild_id = ctx.guild.id
            with open('BAN_WORDS', encoding='utf-8') as file:
                BAN_WORDS = [i.strip() for i in file.readlines()]
            for i in BAN_WORDS:
                if morph.parse(i)[0].normal_form in ctx.content.lower():
                    if ctx.author.guild_permissions.administrator:
                        await ctx.channel.send('Склоняю колено перед админом и прощаю ему все грехи', reference=ctx)
                    else:
                        warg_count = cursor.execute(f"""SELECT warning_count FROM '{guild_id}'
                            WHERE id = {ctx.author.id}""").fetchone()[0]
                        if warg_count == 3:
                            cursor.execute(f"""UPDATE '{guild_id}'
                            SET warning_count = 0
                            WHERE id = {ctx.author.id}""")
                            cursor.execute(f"""UPDATE '{guild_id}'
                            SET mute_count = mute_count + 1
                            WHERE id = {ctx.author.id}""")
                            db.commit()
                            await timeout_member(guild_id, ctx.channel, ctx.author)
                        else:
                            dict_warnings = {
                                0: 'осталось 2 предупреждения',
                                1: 'осталось 1 предупреждение',
                                2: 'последнее предупреждение'
                            }
                            cursor.execute(f"""UPDATE '{guild_id}'
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
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('У тебя здесь нет власти')
            return
        await interaction.response.send_message('Судьба, власть, коварство... и 3 банановые республики')
        cursor.execute(f"""UPDATE permissions
        SET moderation = 'False', inspection = 'False', surveillance = 'False'
        WHERE id = {interaction.guild.id}""")
        db.commit()

    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='светлое_будущее', description='разрешает пользователям использовать бота')
async def dictatorship_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('У тебя здесь нет власти')
            return
        await interaction.response.send_message('У народа теперь есть власть')
        cursor.execute(f"""UPDATE permissions
SET moderation = 'True', inspection = 'True', surveillance = 'True'
WHERE id = {interaction.guild.id}""")
        db.commit()

    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='send_status', description='send status of member')
async def status(interaction: discord.Interaction, role: discord.Role):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if not interaction.user.guild_permissions.administrator:
            if not DICT_FOR_DB[cursor.execute(f"""SELECT surveillance FROM permissions
WHERE id = {interaction.guild.id}""").fetchone()[0]]:
                await interaction.response.send_message('У тебя здесь нет власти')
                return
        embed_message = discord.Embed(description=f'статус людей с ролью {str(role)[1:]}', color=role.color)
        for member in interaction.guild.members:
            if role in member.roles:
                embed_message.add_field(name=member.name, value=member.status)
        await interaction.response.send_message('Всё готово, вот:')
        await interaction.channel.send(embed=embed_message)
    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='check', description='send information of member')
async def check_member(interaction: discord.Interaction, member: discord.Member):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if not interaction.user.guild_permissions.administrator:
            if not DICT_FOR_DB[cursor.execute(f"""SELECT inspection FROM permissions
WHERE id = {interaction.guild.id}""").fetchone()[0]]:
                await interaction.response.send_message('У тебя здесь нет власти')
                return
        for mem in interaction.guild.members:
            if mem.id == member.id:
                member = mem
                break
        if member.activities:
            if member.activities[0].name != 'Hang Status':
                activity = member.activities[0]
            else:
                activity = None
        else:
            activity = None
        sins = cursor.execute(f"""SELECT mute_count FROM '{interaction.guild.id}'
    WHERE id = {member.id}""").fetchone()[0]
        roles = '\t\t'.join([str(i) for i in member.roles if i.name != '@everyone'])
        if len(roles) == 0:
            roles = None
        embed_message = discord.Embed(description=f'Данные о пользователе {member.name}', color=discord.Color.yellow())
        embed_message.add_field(name='status', value=str(member.status), inline=False)
        embed_message.add_field(name='color', value=str(member.color), inline=False)
        embed_message.add_field(name='CustomActivity name', value=str(activity), inline=False)
        embed_message.add_field(name='id', value=str(member.id), inline=False)
        embed_message.add_field(name='roles', value=str(roles), inline=False)
        embed_message.add_field(name='count of mutes', value=str(sins), inline=False)
        await interaction.response.send_message('Всё готово, вот:')
        await interaction.channel.send(embed=embed_message)
    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='begin_the_usurpation', description='используйте эту команду для авторизации и запуска бота')
async def begin_bot(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        try:
            data_base = sqlite3.connect('../server_files/database/keywords.db')
            curs_key = data_base.cursor()
            registrated = curs_key.execute(f"""SELECT IS_REGISTRATED FROM keys
            WHERE id = '{interaction.guild.id}'""").fetchone()[0]
            await  interaction.response.send_message('Бот уже авторизован')
            data_base.close()
        except Exception:
            sigin_window = SignIn(db, cursor)
            await interaction.response.send_modal(sigin_window)
    else:
        await interaction.response.send_message('У тебя здесь нет власти')


@bot.tree.command(name='turn_on_moderation', description='включает модерацию')
async def moder_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
SET moderation = 'False'
WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('Модерация чата включена')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_moderation', description='выключает модерацию')
async def moder_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
SET moderation = 'True'
WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('Модерация чата выключена')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_on_check', description='разрешает пользователям использовать /check')
async def check_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET inspection = 'True'
            WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('/check доступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_check', description='запрещает пользователям использовать /check')
async def check_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET inspection = 'False'
            WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('/check недоступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_on_send_status', description='разрешает пользователям использовать /send_status')
async def send_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET surveillance = 'True'
            WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('/send_status доступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_send_status', description='запрещает пользователям использовать /send_status')
async def send_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET surveillance = 'False'
            WHERE id = {interaction.guild.id}""")
            db.commit()
            await interaction.response.send_message('/send_status недоступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='change_mute_counts', description='Изменяет пользователю счётчик мутов на ваше количество')
async def add_mute_count(interaction: discord.Interaction, member: discord.Member, count: int):
    sins = cursor.execute(f"""SELECT mute_count FROM '{interaction.guild.id}'
WHERE id = {member.id}""").fetchone()[0]
    if sins > 0:
        if sins + count > 50:
            cursor.execute(f"""UPDATE '{interaction.guild.id}'
    SET mute_count = 50
    WHERE id = {member.id}""")
            db.commit()
        elif sins + count <= 50:
            cursor.execute(f"""UPDATE '{interaction.guild.id}'
            SET mute_count = {sins + count}
    WHERE id = {member.id}""")
            db.commit()
    else:
        if sins + count < 0:
            cursor.execute(f"""UPDATE '{interaction.guild.id}'
            SET mute_count = 0
    WHERE id = {member.id}""")
            db.commit()
        elif sins + count >= 0:
            cursor.execute(f"""UPDATE '{interaction.guild.id}'
            SET mute_count = {sins + count}
    WHERE id = {member.id}""")
            db.commit()
    end_sin = cursor.execute(f"""SELECT mute_count FROM '{interaction.guild.id}'
WHERE id = {member.id}""").fetchone()[0]
    await interaction.response.send_message(f'Теперь у пользователя {member.name} mute_count = {end_sin}')


async def timeout_member(guild_id, channel, member: discord.User, reason='Так надо, объективно'):
    mute_count = cursor.execute(f"""SELECT mute_count FROM '{guild_id}'
WHERE id = {member.id}""").fetchone()[0]
    if mute_count > 50:
        mute_count = 50
        cursor.execute(f"""UPDATE '{guild_id}'
SET mute_count = 50
WHERE id = {member.id}""")
        db.commit()
    await member.timeout(timedelta(minutes=2 * (mute_count // 0.9)), reason=reason)
    await channel.send(f'Участник {member.mention} был замучен.\nПричина: {reason}')


bot.run(TOKEN)
