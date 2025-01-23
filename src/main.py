# https://discord.com/developers/applications/1324484768695451679/bot

import discord
from discord import Client, Intents
from discord.member import Member
from discord.message import Message
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

def get_user_xp(user_id: int) -> int:
    # Simulação de XP
    return 450

# Classe de gerenciamento dos comandos de XP
class ExperienceManager:
    def __init__(self, client: Client):
        self.client = client

    async def xp_command(self, message: Message):
        # Verificar se a mensagem enviada não foi enviada pelo próprio bot
        if message.author == self.client.user:
            return

        user_xp = get_user_xp(message.author.id)

        # Verifica se a mensagem é apenas "/xp"
        # Caso sim:
        # - Envia a mensagem com o XP do usuário autor no chat
        if message.content.lower() == "/xp":
            await message.channel.send(f"XP do usuário {message.author.mention}: {user_xp}")
            return
        
        # Verifica se a mensagem começa com "/xp"
        # Caso sim:
        # - Verifica se na mensagem, a menção feita é válida
        #   ex: pode ser feita uma menção de um usuário que não existe
        #   Caso sim:
        #       - Envia a mensagem com XP do usuário mencionado
        #   Caso não:
        #       - Envia uma mensagem avisando que o usuário mencionado não existe
        if message.content.lower().startswith("/xp"):
            if message.mentions:
                mentioned_user = message.mentions[0]
                mentioned_xp = get_user_xp(mentioned_user.id)
                await message.channel.send(f"XP do usuário {mentioned_user.mention}: {mentioned_xp}")
            else:
                await message.channel.send(f"Usuário não catalogado!")
            return

    async def ranking_command(self, message: Message):
        """
        Comando responsável pelo ranking de XP dos usuários
        """

        # Verificar se a mensagem enviada não foi enviada pelo próprio bot
        if message.author == self.client.user:
            return
        
        # Verifica se a mensagem é apenas "/ranking"
        # Caso sim:
        # - Envia a mensagem com o ranking de XP dos usuário catalogados com XP
        if message.content.lower() == "/ranking":
            await message.channel.send(f"Usuário {message.author.mention} deseja o **Ranking**")

    async def ranking_hierarchy(self, message: Message):
        if message.author.bot:
            return
        user_xp = get_user_xp(message.author.id)

        xp_roles = [
            ("👑 Lorde", 6809600),
            ("⚜️ Nobre", 1702400),
            ("🛡️ Cavalaria", 425600),
            ("⚔️ Oficiais", 106400),
            ("💰 Soldado de aluguel", 25600),
            ("✝️ Monge", 6400),
            ("🛠️ Armeiro", 1600),
            ("🧑‍🎓 Escudeiro", 400),
        ]
        
        for xp_criteria in xp_roles:
            if user_xp >= xp_criteria["xp"]:
                # Busca o cargo pelo nome
                role = discord.utils.get(message.guild.roles, name=xp_criteria["role_name"])
                
                # Verifica se o cargo existe e se o usuário já não possui
                if role and role not in message.author.roles:
                    await message.author.add_roles(role)
                    await message.channel.send(
                        f"Parabéns, {message.author.mention}! Você ganhou o cargo de {role.name}!"
                    )



class Minerva(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.experience = ExperienceManager(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_member_join(self, member: Member):
        guild = member.guild
        if guild.system_channel:
            to_send = f'Welcome {member.mention} to {guild.name}!'
            await guild.system_channel.send(to_send)

    async def on_message(self, message: Message):
        await self.experience.xp_command(message)
        await self.experience.ranking_command(message)
        await self.experience.ranking_hierarchy(message)

intents = Intents.default()
intents.members = True
intents.message_content = True

client = Minerva(intents=intents)
client.run(TOKEN)
