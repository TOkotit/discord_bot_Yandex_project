import discord
import logging
import sqlite3
from samples import TOKEN

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


 #Модерация спокойно запускается вместе с командами, и они не конфликтуют
 #Бот модер не реагирует на команды, всё хорошо
 #Но при программном запуске в одном фале будет работать только один из них
 #Я смог не запустить их кодом по очереди, только ручками через Run file, и они будут спокойно работать
 #Но если попытаться их запустить одновременно(потоками, ассинхронно, я всё пробовал), то в лучшем случае один
 #из них просто не будет работать. Но каким-то образом я своим величием добился того, что вместо нормальной ошибки
 #мне выводится вот это:
 # "run_moder.py" �� ���� ����७��� ��� ���譥�
 # ��������, �ᯮ��塞�� �ணࠬ��� ��� ������ 䠩���. это полный код ошибки, буквально
 # Иероглифы в переводе означают код/информация заполнять/переполнять моча/мочиться/облегчаться
 # Дорогой дневник, мне не описать ту боль и унижение, которе я испытал...


intents = discord.Intents.all()
intents.presences = True #
intents.members = True #
intents.message_content = True #

db = sqlite3.connect("../assets/database/ban_members.db")
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS mutes (name TEXT,id INT)""")




class ModerBot(discord.Client):
    def __init__(self, intents):
        with open('commands.txt', encoding='utf-8') as file:
            self.commands = [i.strip() for i in file.readlines()]
        with open('BAN_WORDS', encoding='utf-8') as file:
            self.BAN_WORDS = [i.strip() for i in file.readlines()]
        super().__init__(intents=intents)

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        for guild in self.guilds:
            logger.info(
                f'{self.user} подключились к чату:\n'
                f'{guild.name}(id: {guild.id})')

    async def on_message(self, message):
        if message.author == self.user:
            return
        for i in self.commands:
            if i in message.content.split()[0]:
                break
        else:
            for i in self.BAN_WORDS:
                if i in message.content.lower():
                    message.author.edit(mute=True)
            else:
                await message.channel.send('123')

    async def mute_member(self, ctx, user: discord.User):
        # проверяем на существование записи с id пользователя
        if cursor.execute(f"SELECT name FROM mutes WHERE id = {ctx.author.id}").fetchone()[0] is not None:
            await ctx.send("Этот игрок уже замучен")
        else:
            cursor.execute("INSERT INTO mutes VALUES (?, ?)", (ctx.author.name, ctx.author.id))
            await ctx.send("Успешно!")


client = ModerBot(intents=intents)
client.run(TOKEN)
