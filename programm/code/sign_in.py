import discord
import sqlite3
from discord import ui


class SignIn(ui.Modal, title='Авторизация'):
    def __init__(self, data, curs):
        self.curs = curs
        self.data = data
        super().__init__()

    member_login = ui.TextInput(
        style=discord.TextStyle.short,
        label='Login',
        required=False,
        placeholder='имя, по которому вас запишут в интересную БД'
    )
    password = ui.TextInput(
        style=discord.TextStyle.short,
        label='Password',
        required=False,
        placeholder='Хороший пароль, это ваша ответственность'
    )
    key_word = ui.TextInput(
        style=discord.TextStyle.long,
        label='Key-word',
        required=False,
        max_length=500,
        placeholder='ключ для активации бота'
    )

    async def on_submit(self, interaction: discord.Interaction):
        data_base = sqlite3.connect('../server_files/database/keywords.db')
        cursor = data_base.cursor()

        try:
            key = cursor.execute(f"""SELECT * FROM keys
WHERE key = '{self.key_word.value.strip()}'""").fetchone()
        except Exception:
            await interaction.response.send_message('Неправильный ключ')
            return
        if key is None:
            await interaction.response.send_message('Неправильный ключ')
            return
        elif key[1] is None or key[2] is None or key[3] is None:
            cursor.execute(f"""UPDATE keys
SET id = {interaction.guild.id}, login = '{self.member_login.value}', password = '{self.password.value}', IS_REGISTRATED = 'True'
WHERE key = '{self.key_word.value}'""")
            data_base.commit()
            data_base.close()
            self.curs.execute(f"""UPDATE permissions
SET CAN_USE = 'True'
WHERE id = {interaction.guild.id}""")
            self.data.commit()
        elif key[1] is not None or key[2] is not None or key[3] is not None:
            await interaction.response.send_message('Неправильный логин или пароль для этого сервера')
            return
        else:
            await interaction.response.send_message('Неправильный ключ')
            return
        embed = discord.Embed(title='Бот готов\nСпасибо за его использование',
                              description='Насладитесь же властью над своим сервером')
        await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message('Что-то пошло не так :(\nПовторите поптыку позже')
