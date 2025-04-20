import discord
from discord import Client, Intents
from discord.member import Member
from discord.message import Message
from dotenv import load_dotenv
#cliente e inferência da hugging Face
from huggingface_hub import InferenceClient
import os
import json

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
# Inicialização do cliente da Hugging Face com o modelo e token especificado no .env
hf_client = InferenceClient(model="bigcode/starcoder", token=HF_TOKEN)
botName = 'Athena'
XP_DATA_FILE = "xp_data.json"
CHALLENGES_FILE = "challenges.json"

# Dicionário para armazenar o XP dos usuários
user_xp_data = {}
#Dicionário para armazenar desafios de programação
challenge_data = {}

def load_xp_data():
    """Carrega os dados de XP do arquivo JSON para o dicionário."""
    global user_xp_data
    try:
        with open(XP_DATA_FILE, "r") as file:
            data = json.load(file)
            # Converter as chaves para int, pois o JSON armazena como string
            user_xp_data = {int(user_id): xp for user_id, xp in data.items()}
    except FileNotFoundError:
        user_xp_data = {}

def load_challenges():
    #Carrega os dados de desafops do arquivo JSON para o dicionário
    #Os desafios devem estar no formato:
    #{
    #   "titulo": {
    #       "descrição: "
    #       "xp: "
    # }
    #
    #
    #}
    global challenge_data
    try:
        with open(CHALLENGES_FILE, "r", encoding="utf-8") as file:
            challenge_data = json.load(file)
    except FileNotFoundError:
        print("Arquivo de desafios não encontrado.")
        challenge_data = {}

def save_xp_data():
    """Salva os dados de XP no arquivo JSON."""
    with open(XP_DATA_FILE, "w") as file:
        json.dump(user_xp_data, file)

def get_user_xp(user_id: int) -> int:
    # Retorna o XP atual do usuário, ou 0 se ele não existir no dicionário
    return user_xp_data.get(user_id, 0)

def add_xp(user_id: int, xp: int):
    """Adiciona XP ao usuário e atualiza o arquivo JSON."""
    if user_id in user_xp_data:
        user_xp_data[user_id] += xp
    else:
        user_xp_data[user_id] = xp
    save_xp_data()

async def code_analysis(code: str):
    """
    Envia o código fornecido pelo usuário para análise de erros utilizando o modelo StarCoder (Hugging Face).
        code: O código Python enviado pelo usuário.

    Retorna:
        str: A resposta gerada pelo modelo com a análise do código.
    """
    prompt = f""" Análise de código Python:
Código:
{code}

### O código possui erros? Se sim diga quais. Se não, diga que está correto.
resposta: """
    
    # Envia o prompt pro modelo StarCoder e retorna a resposta
    resposta = hf_client.text_generation(prompt, max_new_tokens = 100)
    return resposta

# Classe de gerenciamento dos comandos de XP
class ExperienceManager:
    def __init__(self, client: Client):
        self.client = client

    async def xp_command(self, message: Message):
        # Ignora mensagens enviadas pelo próprio bot
        if message.author == self.client.user:
            return

        user_xp = get_user_xp(message.author.id)

        # Comando: ty: xp
        if message.content.lower() == "ty: xp":
            await message.channel.send(f"XP do usuário {message.author.mention}: {user_xp} XP")
            return

        # Comando: ty: guardião
        if message.content.lower() == "ty: guardião":
            await message.channel.send(
                f"Olá, {message.author.mention}! Eu sou {botName}, a coruja sábia que se tornou a mascote orgulhosa desta incrível comunidade.\n\n"
                "Eu represento o compromisso da TYTO.code com a excelência em administração, suporte aos desenvolvedores e organização de projetos. "
                "Se você tiver ideias para aprimorar a minha atuação ou sugestões para a TYTO.code, ficarei encantada em ouvir."
            )
            return
        
        # Comando: ty: xp <menção>
        if message.content.lower().startswith("ty: xp"):
            if message.mentions:
                mentioned_user = message.mentions[0]
                mentioned_xp = get_user_xp(mentioned_user.id)
                await message.channel.send(f"XP de {mentioned_user.mention}: {mentioned_xp}")
            else:
                await message.channel.send("Usuário não catalogado!")
            return

        # Comando: ty: addxp <menção> <quantidade>
        if message.content.lower().startswith("ty: addxp"):
            await self.add_xp_command(message)

    async def add_xp_command(self, message: Message):
        if message.author.bot:
            return

        # Apenas administradores podem adicionar XP
        if not message.author.guild_permissions.administrator:
            await message.channel.send("Você não tem permissão para usar este comando.")
            return

        try:
            # Exemplo de comando: ty: addxp @usuario 100
            # Usar message.mentions para extrair o usuário mencionado
            mentioned_user = message.mentions[0]
            # A quantidade de XP é o último argumento
            xp_to_add = int(message.content.split()[-1])
            add_xp(mentioned_user.id, xp_to_add)
            await message.channel.send(f"{xp_to_add}xp foram adicionados para o usuário {mentioned_user.mention}!")
        except (IndexError, ValueError):
            await message.channel.send("Use o comando assim: `ty: addxp @usuario [quantidade]`.")    
    
    async def registrar_desafio_command(self, message: Message):
        if not message.content.lower().startswith("ty: registrar desafio"):
            return
        try:
        # Tenta dividir a mensagem em quatro partes: comando, título, descrição e linha de XP.
        # O split usa '\n' como separador e espera exatamente quatro linhas.
            _, titulo, descricao, xp_line = message.content.split("\n", 3)
            # limpa, formata e converte o título, descrição e o xp do desafio
            titulo = titulo.replace("Título:", "").strip().lower()
            descricao = descricao.replace("Descrição:", "").strip()
            xp = int(xp_line.replace("XP:", "").strip())
            
            # Verifica se já existe um desafio com o mesmo título no dicionário
            if titulo in challenge_data:
                await message.channel.send("Já existe um desafio com esse título.")
                return

            challenge_data[titulo] = {
                "descrição": descricao,
                "xp": xp
            }

            with open(CHALLENGES_FILE, "w", encoding="utf-8") as file:
                json.dump(challenge_data, file, indent=4, ensure_ascii=False)

            await message.channel.send(f"Desafio **{titulo}** registrado com sucesso com recompensa de **{xp} XP**! ✅")
        
        except Exception as e:
             # Em caso de erro (formato incorreto, erro ao converter XP etc.), envia instruções ao usuário
            print("Erro ao registrar desafio:", e)
            await message.channel.send(
                "Formato inválido. Use assim:\n"
                "`ty: registrardesafio`\n"
                "`Título: <nome>`\n"
                "`Descrição: <texto>`\n"
                "`XP: <valor numérico>`"
            )

    async def desafio_command(self, message: Message):
        
        #Permite o envio de códigos para validação 
        #ty: desafio
        #Desafio: <título>
        #```python
        #<código>
        #```
        #
        #O título é usado para buscar a recompensa no json
        #O código é enviado para o LLM, se estiver certo, o xp é concedido
        #
        if not message.content.lower().startswith("ty: desafio"):
            return
        
        try:
            # Quebra a mensagem em 3 partes: comando, título e código
            _, titulo_desafio, code = message.content.split("\n", 2)
            # Remove prefixo "Desafio: "
            desafio = titulo_desafio.replace("Desafio: ", "").strip().lower()

            if desafio not in challenge_data:
                await message.channel.send("Desafio não encontrado. Verifique o nome do desafio.")
                return

            recompensa = challenge_data[desafio]["xp"]
            await message.channel.send("Analisando o código, um momento... 🧐")

            analise = await code_analysis(code)

            await message.channel.send(f"Análise do código para **{titulo_desafio}**:\n```{analise.strip()}```")
            
            # Verifica se o modelo retornou uma resposta positiva com base em palavras-chave
            if any(palavra in analise.lower() for palavra in ["está correto", "sem erros", "funciona", "não possui erros"]):
                add_xp(message.author.id, recompensa)
                await message.channel.send(f"{message.author.mention}, seu código está correto! Você ganhou **{recompensa} XP** 🎉")

            else:
                await message.channel.send("O código ainda precisa de ajustes. Continue tentando! 💪")
        except ValueError:
            await message.channel.send("Formato inválido. Use o seguinte formato:\n"
                                       "`ty: desafio`\n"
                                       "`Desafio: <nome do desafio>`\n"
                                       "```python\n<seu código>\n```")

    async def ranking_command(self, message: Message):
        # Ignora mensagens do bot
        if message.author == self.client.user:
            return

        if message.content.lower() == "ty: ranking":
            ranking = sorted(user_xp_data.items(), key=lambda x: x[1], reverse=True)
            ranking_message = "**Ranking de XP**:\n"
            for i, (user_id, xp) in enumerate(ranking[:10], start=1):
                try:
                    user = await self.client.fetch_user(user_id)
                    ranking_message += f"{i}. {user.name}: {xp} XP\n"
                except Exception:
                    ranking_message += f"{i}. ID {user_id}: {xp} XP\n"
            await message.channel.send(ranking_message)

    async def ranking_hierarchy(self, message: Message):
        # Verifica se a mensagem é do tipo esperado e ignora bots
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
                # Procura o cargo pelo nome
                role = discord.utils.get(message.guild.roles, name=role_name)
                # Se o cargo existir e o usuário ainda não o tiver, adiciona-o
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
        load_xp_data()  # Carrega os dados de XP ao iniciar o bot
        load_challenges() #Carrega os desafios ao iniciar o bot
    async def on_member_join(self, member: Member):
        guild = member.guild
        if guild.system_channel:
            await guild.system_channel.send(f'Welcome {member.mention} to {guild.name}!')

    async def on_message(self, message: Message):
        await self.experience.xp_command(message)
        await self.experience.ranking_command(message)
        await self.experience.ranking_hierarchy(message)
        await self.experience.registrar_desafio_command(message)
        await self.experience.desafio_command(message)

intents = Intents.default()
intents.members = True
intents.message_content = True

client = Minerva(intents=intents)
client.run(TOKEN)