# Importações do discord
import discord
from discord import Client
from discord.member import Member
from discord.message import Message
from discord.guild import Guild
from discord.ext import commands

# Importações gerais
import os
import asyncio
from dotenv import load_dotenv

# Carregando as variáveis de ambiente
load_dotenv()

# Armazenando token do bot
TOKEN = os.getenv("DISCORD_TOKEN")

# Classe de gerenciamento dos comandos de XP
class ExperienceManager:
    """
    Objeto que irá gerenciar o xp dos usuários
    """
    def __init__(self, client: Client):
        self.client: Client = client

    async def xp_command(self, message: Message):
        """
        Conjunto de comandos relacionados ao XP dos usuários
        """

        # Verificar se a mensagem enviada não foi enviada pelo próprio bot
        if message.author == self.client.user:
            return
        
        # Verifica se a mensagem é apenas "/xp"
        # Caso sim:
        # - Envia a mensagem com o XP do usuário autor no chat
        if message.content.lower() == "/xp":
            await message.channel.send(f"XP do usuário {message.author.mention}: Mais de 8 mil")
            return # Precisa do Return para não ler os outros comandos
        
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
                await message.channel.send(f"XP do usuário {mentioned_user.mention}: Mais de 8 mil")
                return # Precisa do return para não ler os outros comandos
            else:
                await message.channel.send(f"Usuário não catalogado!")
                return # Precisa do return para não ler os outros comandos
    
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



class MyClient(Client):
    """
    Classe responsável pela conexão com a API de aplicações do Discord
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializa o a classe de gerenciamento de XP dos usuários
        self.experience = ExperienceManager(self)

    async def on_ready(self):
        """
        Evento: Quando o bot for ativado
        """
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_member_join(self, member:Member):
        """
        Evento: Quando um novo usuário entra no servidor
        """

        # Armazena as informações do servidor
        guild = member.guild

        # Verifica se no servidor há um canal de mensagens do sistema
        # Caso sim:
        # - Envia uma mensagem de welcome no canal de mensagens do sistema
        if guild.system_channel is not None:
            to_send = f'Welcome {member.mention} to {guild.name}!'
            await guild.system_channel.send(to_send)
    
    
    async def on_message(self, message: Message):
        """
        Evento: Quando uma nova mensagem é enviada
        """

        # Envia o conteúdo da mensagem para o Gerenciador de XP -> Comandos de XP
        await self.experience.xp_command(message)
        
        # Envia o conteúdo da mensagem para o Gerenciador de XP -> Comandos de Ranking
        await self.experience.ranking_command(message)
        

# Configurações internas de Intents do app Bot
intents = discord.Intents.default()
intents.members = True # Acesso aos membros
intents.message_content = True # Acesso as mensagens

# Instanciando o bot
client = MyClient(intents=intents)
client.run(TOKEN) # Executando o loop de eventos do bot