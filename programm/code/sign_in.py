import discord
from discord import ui


class SignIn(ui.Modal, title='Авторизация'):
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
        ...


    async def on_error(self, interaction: discord.Interaction, error):
        ...

