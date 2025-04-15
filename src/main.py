# https://discord.com/developers/applications/1324484768695451679/bot

import discord
from discord import Client, Intents
from discord.member import Member
from discord.message import Message
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
botName = 'Athena'
linksChatDiscord = {
    'comunicados': '',
    'comunicadosFrelancers': '',
    'boas-vindas': '',
    'playground': {
        'chatGeral': '',
        'desafios': '',
        'source': '',
    }
}

# Dicionário para armazenar o XP dos usuários
user_xp_data = {}

def get_user_xp(user_id: int) -> int:
    # Retorna o XP atual do usuário, ou 0 se ele não existir no dicionário
    return user_xp_data.get(user_id, 0)

def add_xp(user_id: int, xp: int):
    # Adiciona XP ao usuário
    if user_id in user_xp_data:
        user_xp_data[user_id] += xp
    else:
        user_xp_data[user_id] = xp


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
        if message.content.lower() == "ty: xp":
            await message.channel.send(f"XP do usuário {message.author.mention}: {user_xp}")
            return
        if message.content.lower() == "ty: guardião":
            await message.channel.send(f"Olá, {message.author.mention}! Eu sou {botName}, a coruja sábia que se tornou a mascote orgulhosa desta incrível comunidade.\n\nEu sou a representação viva do compromisso da TYTO.code com a excelência em administração, suporte aos desenvolvedores e organização de projetos. Assim como minha homônima mitológica, estou aqui para guiar e inspirar.\n\nSe você tiver ideias para aprimorar a minha atuação ou sugestões para a TYTO.code, ficarei encantada em ouvir. Contribuições que promovam eficiência, inovação e uma atmosfera de desenvolvimento positiva são sempre apreciadas.")
            return
        
        # Verifica se a mensagem começa com "/xp"
        # Caso sim:
        # - Verifica se na mensagem, a menção feita é válida
        #   ex: pode ser feita uma menção de um usuário que não existe
        #   Caso sim:
        #       - Envia a mensagem com XP do usuário mencionado
        #   Caso não:
        #       - Envia uma mensagem avisando que o usuário mencionado não existe
        if message.content.lower().startswith("ty: xp"):
            if message.mentions:
                mentioned_user = message.mentions[0]
                mentioned_xp = get_user_xp(mentioned_user.id)
                await message.channel.send(f"XP de {mentioned_user.mention}: {mentioned_xp}")
            else:
                await message.channel.send(f"Usuário não catalogado!")
            return
        if message.content.startswith("ty: addxp"):
            await add_xp_command(message)
        

    async def add_xp_command(message):
        if message.author.bot:
            return

        # Verifica se o autor tem permissão para adicionar XP
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Você não tem permissão para usar este comando.")
            return

        # Verifica se o comando foi usado corretamente
        try:
            # Extraindo os parâmetros: menção ao usuário e quantidade de XP
            _, mentioned_user, xp_to_add = message.content.split()
            mentioned_user_id = int(mentioned_user[3:-1])  # Extrai o ID da menção, removendo <@ e >
            xp_to_add = int(xp_to_add)

            # Adiciona XP ao usuário no banco de dados
            add_xp(mentioned_user_id, message.guild.id, xp_to_add)
            await message.channel.send(f"{xp_to_add} XP foram adicionados para o usuário {mentioned_user}!")
        except (IndexError, ValueError):
            await message.channel.send("Use o comando assim: `/addxp @usuario [quantidade]`.")



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
        if message.content.lower() == "ty: ranking":
            ranking = sorted(user_xp_data.items(), key=lambda x: x[1], reverse=True)
            ranking_message = "**Ranking de XP**:\n"
            for i, (user_id, xp) in enumerate(ranking[:10], start=1):
                user = await self.client.fetch_user(user_id)
                ranking_message += f"{i}. {user.name}: {xp} XP\n"
            await message.channel.send(f"Meu caro {message.author.mention}! Ainda não consigo listar o **Ranking**")

    async def ranking_hierarchy(self, message: Message):
        # Certifique-se de que está acessando os atributos corretamente.
        if isinstance(message, discord.Message):
            if message.author.bot:
                return
        else:
            print("Mensagem não é do tipo esperado:", type(message))
        
        
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
        
        for role_name, required_xp in xp_roles:
            if user_xp >= required_xp:
                # Busca o cargo pelo nome
                role = discord.utils.get(message.guild.roles, name=role_name)
                
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
