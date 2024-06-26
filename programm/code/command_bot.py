import discord
import traceback
import logging
import sqlite3
import pymorphy3
from sign_in import SignIn
from discord.ext import commands  # импорты
from datetime import timedelta
from samples import TOKEN  # так надо, можно юыло по другому, но я не захотел

logger = logging.getLogger('discord')  # логи
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

morph = pymorphy3.MorphAnalyzer()  # морф вроде работает, но он не знает весь русский мат

intents = discord.Intents.all()  # бот может всё, так проще
intents.presences = True
intents.members = True
intents.message_content = True

db = sqlite3.connect("../server_files/database/1984_bot_database.db")  # база данных, которая не закрывается
cursor = db.cursor()  # её просто нет смысла открывать каждый раз

DICT_FOR_DB = {
    'True': True,
    'False': False  # вроде в sql есть нативный bool, вроде нет, вроде он работает как 1 и 0, хз, так проще
}
bot = commands.Bot(command_prefix='/', intents=intents)  # самый лучший бот на свете


@bot.event
async def on_ready():  # обработчик при запуске
    for guild in bot.guilds:
        # если нет таблиц, создаёт
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{guild.id}'( 
        id INT PRIMARY KEY NOT NULL, 
        warning_count INT,
        mute_count INT)""")  # таблицы с серверов
        # на каждом сервере хранит данные о пользователе
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS permissions(
id INT PRIMARY KEY NOT NULL UNIQUE,
moderation TEXT,
inspection TEXT,
surveillance TEXT,
CAN_USE TEXT)""")  # таблица с разрешениями, у каждого сервера свои

    logger.info(f'{bot.user} has connected to Discord!')  # логи
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключились к чату:\n'
            f'{guild.name}(id: {guild.id})')

    for guild in bot.guilds:  # заполнение таблиц
        id_members = cursor.execute(f"""SELECT id FROM '{guild.id}'""").fetchall()
        for member in guild.members:
            if member.id not in id_members:
                # заполнение информации о новых пользователях
                cursor.execute(f"INSERT OR IGNORE INTO '{guild.id}' VALUES(?, ?, ?)", (int(member.id), 0, 0))
                db.commit()
                # заполнение информации о разрешениях
                cursor.execute(
                    f"""INSERT OR IGNORE INTO permissions VALUES({guild.id}, 'True', 'True', 'Ture', 'False')""")
                db.commit()
    data_base_keys = sqlite3.connect('../server_files/database/keywords.db')
    curs_keys = data_base_keys.cursor()  # база данных с ключами доступа
    for guild in bot.guilds:
        if guild.id in [i[0] for i in curs_keys.execute(f"""SELECT id FROM keys""").fetchall()]:
            is_registr = curs_keys.execute(f"""SELECT IS_REGISTRATED FROM keys
    WHERE id = {guild.id}""").fetchone()[0]  # проверка того, зарегистрирован ли сервер
            cursor.execute(f"""UPDATE permissions
    SET CAN_USE = '{is_registr}'
    WHERE id = {guild.id}""")  # заполнение разрешений сервера
            db.commit()
        else:
            cursor.execute(f"""UPDATE permissions
SET CAN_USE = 'False'
WHERE id = {guild.id}""")  # заполнение разрешений сервера
            db.commit()
    data_base_keys.close()
    for guild in bot.guilds:  # создание чата для команд(чисто для эстетики, можно где угодно писать)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }  # права доступа
        for i in guild.channels:
            if i.name == '1984' and i.overwrites == overwrites:
                await i.send(f'Бот запущен')  # если есть такой чат, пишет о запуске
                break
        else:
            await guild.create_text_channel('1984', overwrites=overwrites)
            for i in guild.channels:
                if i.name == '1984' and i.overwrites == overwrites:  # при создании уведомляет админа
                    await i.send(
                        'Бот запущен, это основной канал для его использования.\n'
                        'Так же, вы можете использовать его и в других каналах')
                    break
    await bot.tree.sync()
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")  # какой-то лог, количество активных команд


@bot.event
async def on_guild_join(guild):  # если присоединился на новый сервер
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{guild.id}'(
       id INT PRIMARY KEY NOT NULL,
       warning_count INT,
       mute_count INT)""")  # делает всё то же, что и при запуске - создаёт таблицы для новых серверов, заполняет их
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
                    'Бот запущен, это основной канал для его использования.\n'
                    'Так же, вы можете использовать его и в других каналах')
                break  # тоже, что и на on_ready()


@bot.event
async def on_error(event, *args, **kwargs):
    error_message = traceback.format_exc()
    print(f"ошибка {event}: {error_message}")  # для технических шоколадок


@bot.listen()
async def on_message(ctx):  # если в чате кто-то пишет
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
WHERE id = {ctx.guild.id}""").fetchone()[0]]:  # проверки на регистрацию
        if not DICT_FOR_DB[cursor.execute(f"""SELECT moderation FROM permissions
WHERE id = {ctx.guild.id}""").fetchone()[0]]:  # проверки на разрешение
            if ctx.author == bot.user:
                return
            guild_id = ctx.guild.id  # чтоб кучу раз не писать ctx.guild.id
            with open('BAN_WORDS', encoding='utf-8') as file:
                BAN_WORDS = [i.strip() for i in file.readlines()]  # бан ворды
            for i in BAN_WORDS:
                if morph.parse(i)[0].normal_form in ctx.content.lower():  # если это запрещённое слово
                    if ctx.author.guild_permissions.administrator:  # админа банить нельзя
                        await ctx.channel.send('Склоняю колено перед админом и прощаю ему все грехи', reference=ctx)
                    else:
                        warg_count = cursor.execute(f"""SELECT warning_count FROM '{guild_id}' 
                            WHERE id = {ctx.author.id}""").fetchone()[0]  # изменение базы данных с предупреждениями
                        if warg_count == 3:  # если уже много раз предупредили
                            cursor.execute(f"""UPDATE '{guild_id}'
                            SET warning_count = 0
                            WHERE id = {ctx.author.id}""")
                            cursor.execute(f"""UPDATE '{guild_id}'
                            SET mute_count = mute_count + 1
                            WHERE id = {ctx.author.id}""")
                            db.commit()
                            await timeout_member(guild_id, ctx.channel, ctx.author)  # БАН!!!
                        else:  # если ещё мало нарушил
                            dict_warnings = {
                                0: 'осталось 2 предупреждения',
                                1: 'осталось 1 предупреждение',
                                2: 'последнее предупреждение'
                            }
                            cursor.execute(f"""UPDATE '{guild_id}'
            SET warning_count = warning_count + 1
            WHERE id = {ctx.author.id}""")  # меняем значения в базе данных
                            db.commit()
                            await ctx.channel.send(
                                f'{ctx.author.mention}, так больше не пиши, {dict_warnings[warg_count]}',
                                reference=ctx)  # просим убедительно так больше не писать, иначе его семью ...
                    await ctx.delete()  # удаляем плохое сообщение
            return


@bot.tree.command(name='дискорднй_двор',
                  description='запрещает пользователям использовать бота')  # команда для запрета всего
async def dictatorship_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # проверка авторизации
        if not interaction.user.guild_permissions.administrator:  # это может делать только админ
            await interaction.response.send_message('У тебя здесь нет власти')
            return
        await interaction.response.send_message(
            'Судьба, власть, коварство... и 3 банановые республики')  # хехехех, запретил писать слово линукс
        cursor.execute(f"""UPDATE permissions
        SET moderation = 'False', inspection = 'False', surveillance = 'False'
        WHERE id = {interaction.guild.id}""")  # меняем базу данных
        db.commit()

    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='светлое_будущее', description='разрешает пользователям использовать бота')  # разрешение всего
async def dictatorship_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # проверка разрешений
        if not interaction.user.guild_permissions.administrator:  # можно только админу
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


@bot.tree.command(name='send_status',
                  description='send status of member')  # отправить статус всех людей с указанной ролью
async def status(interaction: discord.Interaction, role: discord.Role):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # проверка разрешений
        if not interaction.user.guild_permissions.administrator:
            if not DICT_FOR_DB[cursor.execute(f"""SELECT surveillance FROM permissions
WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # если нет разрешения на использование не админам
                await interaction.response.send_message('У тебя здесь нет власти')
                return
        embed_message = discord.Embed(description=f'статус людей с ролью {str(role)[1:]}', color=role.color)
        for member in interaction.guild.members:
            if role in member.roles:
                embed_message.add_field(name=member.name, value=member.status)  # заполнение объекта, который отправим
        await interaction.response.send_message('Всё готово, вот:')
        await interaction.channel.send(embed=embed_message)
    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


@bot.tree.command(name='check', description='send information of member')  # запрос на различные данные о пользователе
async def check_member(interaction: discord.Interaction, member: discord.Member):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions 
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # проверка разрешений
        if not interaction.user.guild_permissions.administrator:
            if not DICT_FOR_DB[cursor.execute(f"""SELECT inspection FROM permissions
WHERE id = {interaction.guild.id}""").fetchone()[0]]:  # проверка разрешений для не админа
                await interaction.response.send_message('У тебя здесь нет власти')
                return
        for mem in interaction.guild.members:  # лютый костыль, почему-то при попытке просто взять объект,
            # он ставит у пользователя все данные дефолтные
            if mem.id == member.id:
                member = mem
                break
        if member.activities:
            if member.activities[0].name != 'Hang Status':  # тоже костыль, странный объект, не то список, не то словарь
                activity = member.activities[0]
            else:
                activity = None
        else:
            activity = None
        sins = cursor.execute(f"""SELECT mute_count FROM '{interaction.guild.id}'
    WHERE id = {member.id}""").fetchone()[0]  # берём мьюты указанного пользователя
        roles = '\t\t'.join([str(i) for i in member.roles if i.name != '@everyone'])
        if len(roles) == 0:  # если нет ролей
            roles = None
        embed_message = discord.Embed(description=f'Данные о пользователе {member.name}', color=discord.Color.yellow())
        embed_message.add_field(name='status', value=str(member.status), inline=False)
        embed_message.add_field(name='color', value=str(member.color), inline=False)
        embed_message.add_field(name='CustomActivity name', value=str(activity), inline=False)
        embed_message.add_field(name='id', value=str(member.id), inline=False)
        embed_message.add_field(name='roles', value=str(roles),
                                inline=False)  # объект для красивого сообщения с рамочкой
        embed_message.add_field(name='count of mutes', value=str(sins), inline=False)
        await interaction.response.send_message('Всё готово, вот:')
        await interaction.channel.send(embed=embed_message)
    else:
        await interaction.response.send_message(
            'Бот не авторизован на это сервере\nОбратитесь к администратору для его авторизации')


# фунция старта и регистрации бота на сервере
@bot.tree.command(name='begin_the_usurpation', description='используйте эту команду для авторизации и запуска бота')
async def begin_bot(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:  # только админ может активировать
        try:  # лютый, лютый костыль, иначе оно не хотело работать
            data_base = sqlite3.connect('../server_files/database/keywords.db')
            curs_key = data_base.cursor()
            registrated = curs_key.execute(f"""SELECT IS_REGISTRATED FROM keys
            WHERE id = '{interaction.guild.id}'""").fetchone()[0]
            await  interaction.response.send_message('Бот уже авторизован')
            data_base.close()
        except Exception:
            sigin_window = SignIn(db, cursor)  # если бот не авторизован, отправляем форму для авторизации
            await interaction.response.send_modal(sigin_window)
    else:
        await interaction.response.send_message('У тебя здесь нет власти')


@bot.tree.command(name='turn_on_moderation', description='включает модерацию')  # включает модерацию
async def moder_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
SET moderation = 'False'
WHERE id = {interaction.guild.id}""")  # просто изменение базы данных с кучей проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('Модерация чата включена')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_moderation', description='выключает модерацию')
async def moder_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
SET moderation = 'True'
WHERE id = {interaction.guild.id}""")  # просто изменение базы данных с кучей проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('Модерация чата выключена')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_on_check', description='разрешает пользователям использовать /check')
async def check_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET inspection = 'True'
            WHERE id = {interaction.guild.id}""")  # просто изменение базы данных
            # с кучей проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('/check доступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_check', description='запрещает пользователям использовать /check')
async def check_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET inspection = 'False'
            WHERE id = {interaction.guild.id}""")  # просто изменение базы данных с кучей
            # проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('/check недоступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_on_send_status', description='разрешает пользователям использовать /send_status')
async def send_on(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET surveillance = 'True'
            WHERE id = {interaction.guild.id}""")  # просто изменение базы данных с кучей
            # проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('/send_status доступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name='turn_off_send_status', description='запрещает пользователям использовать /send_status')
async def send_off(interaction: discord.Interaction):
    if DICT_FOR_DB[cursor.execute(f"""SELECT CAN_USE FROM permissions
    WHERE id = {interaction.guild.id}""").fetchone()[0]]:
        if interaction.user.guild_permissions.administrator:
            cursor.execute(f"""UPDATE permissions
            SET surveillance = 'False'
            WHERE id = {interaction.guild.id}""")  # просто изменение базы данных
            # с кучей проверок, чтоб мог только админ
            db.commit()
            await interaction.response.send_message('/send_status недоступна для всех')
        else:
            await interaction.response.send_message('У тебя здесь нет власти')
    else:
        embed = discord.Embed(title='',
                              description='Бот не авторизован на это сервере\n'
                                          'Обратитесь к администратору для его авторизации')
        await interaction.response.send_message(embed=embed)


# меняет значение в базе данных на count
@bot.tree.command(name='change_mute_counts', description='Изменяет пользователю счётчик мутов на ваше количество')
async def add_mute_count(interaction: discord.Interaction, member: discord.Member, count: int):
    sins = cursor.execute(f"""SELECT mute_count FROM '{interaction.guild.id}'
WHERE id = {member.id}""").fetchone()[0]
    if sins > 0:  # очень глупая проверка на то, чтоб у пользователя в бд значение всегда было от 0 до 50
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


# функция которая бросате пользователя в timeout (строена в дискорд)
async def timeout_member(guild_id, channel, member: discord.User, reason='Так надо, объективно'):
    mute_count = cursor.execute(f"""SELECT mute_count FROM '{guild_id}'
WHERE id = {member.id}""").fetchone()[0]  # бросает пользователя member в таймаут на время, зависящее от значения в бд
    if mute_count > 50:
        mute_count = 50
        cursor.execute(f"""UPDATE '{guild_id}'
SET mute_count = 50
WHERE id = {member.id}""")
        db.commit()
    await member.timeout(timedelta(minutes=2 * (mute_count // 0.9)), reason=reason)
    await channel.send(f'Участник {member.mention} был замучен.\nПричина: {reason}')


bot.run(TOKEN)  # запуск бота
