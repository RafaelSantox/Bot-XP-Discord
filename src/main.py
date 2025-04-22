import discord
from discord import Client, Intents
from discord.member import Member
from discord.message import Message
#Imports para controle de requisições
from discord.ext import commands
from collections import deque
from datetime import datetime, timedelta
from dotenv import load_dotenv
#import para a LLM do Gemini
import google.generativeai as genai
import os
import json

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
botName = 'Athena'
XP_DATA_FILE = "xp_data.json"
CHALLENGES_FILE = "challenges.json"

# Dicionário para armazenar o XP dos usuários
user_xp_data = {}
#Dicionário para armazenar desafios de programação
challenge_data = {}

# Controle de requisições
request_times = deque(maxlen=15) # Mantém as últimas 15 requisições
DAILY_REQUESTS_FILE = "daily_requests.json"
daily_requests = {"count": 0, "date": str(datetime.now().date())}

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


def load_daily_requests():
    global daily_requests
    try:
        with open(DAILY_REQUESTS_FILE, "r") as file:
            data = json.load(file)
            if data["date"] == str(datetime.now().date()):
                daily_requests = data
    except FileNotFoundError:
        daily_requests = {"count": 0, "date": str(datetime.now().date())}

def save_daily_requests():
    with open(DAILY_REQUESTS_FILE, "w") as file:
        json.dump(daily_requests, file)

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
    Analisa código usando Gemini 2.0 flash
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Modelo mais recente
        
        prompt = f"""Analise este código Python para um desafio de programação. Responda STRITAMENTE no formato:

                ANÁLISE:
                - ✅ CORRETO (se perfeito)
                - OU
                - ❌ [Linha X] ERRO: descrição (tipo)

                REGRAS:
                1. Ignore erros de estilo/pep8
                2. Foque em sintaxe e lógica
                3. Seja conciso (máx 3 erros)

                CÓDIGO:
                ```python
                {code[:4000]}```"""
        
        response = await model.generate_content_async(prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ Erro na análise: {str(e)}"


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
            # Divide a mensagem em linhas e remove linhas vazias
            lines = [line.strip() for line in message.content.split('\n') if line.strip()]
        
            # Verifica o número mínimo de linhas (comando + título + descrição + XP)
            if len(lines) < 4:
                await message.channel.send("❌ Formato inválido. Você precisa fornecer todas as informações necessárias.")
                return

            # Extrai e valida cada componente
            titulo = None
            descricao = None
            xp = None
        
            for line in lines[1:]:  # Ignora a primeira linha (comando)
                if line.lower().startswith('título:'):
                    titulo = line[7:].strip().lower()  # Remove "Título:" e espaços
                elif line.lower().startswith('descrição:'):
                    descricao = line[10:].strip()  # Remove "Descrição:" e espaços
                elif line.lower().startswith('xp:'):
                    try:
                        xp = int(line[3:].strip())  # Converte XP para inteiro
                    except ValueError:
                        await message.channel.send("❌ O valor de XP deve ser um número inteiro.")
                        return

            # Verifica se todos os campos foram preenchidos
            if not titulo:
                await message.channel.send("❌ Você precisa especificar um título para o desafio.")
                return
            if not descricao:
                await message.channel.send("❌ Você precisa fornecer uma descrição para o desafio.")
                return
            if xp is None:
                await message.channel.send("❌ Você precisa especificar a recompensa de XP.")
                return

            # Verifica se o título já existe
            if titulo in challenge_data:
                await message.channel.send(f"❌ Já existe um desafio com o título '{titulo}'.")
                return

        # Armazena o desafio
            challenge_data[titulo] = {
                "descrição": descricao,
                "xp": xp
            }

            # Salva no arquivo
            with open(CHALLENGES_FILE, 'w', encoding='utf-8') as file:
                json.dump(challenge_data, file, indent=4, ensure_ascii=False)

            await message.channel.send(
                f"✅ Desafio **{titulo}** registrado com sucesso!\n"
                f"**Recompensa:** {xp} XP\n"
                f"**Descrição:** {descricao}"
            )
        
        except Exception as e:
            print(f"Erro ao registrar desafio: {e}")
            await message.channel.send(
                "❌ Ocorreu um erro ao processar seu desafio. Use o formato:\n"
                "```\n"
                "ty: registrar desafio\n"
                "Título: [nome do desafio]\n"
                "Descrição: [descrição detalhada]\n"
                "XP: [valor numérico]\n"
                "```"
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
        # verificação de uso diario (1500 RPD)
        if daily_requests["date"] != str(datetime.now().date()):
            daily_requests["count"] = 0
            daily_requests["date"] = str(datetime.now().date())
        
        if daily_requests["count"] >= 1500:
            await message.channel.send("⏳ Limite diário de 1500 análises atingido! Tente novamente amanhã.")
            return

        # Verifica limite de requests por minuto (15 RPM)
        now = datetime.now()
        if len(request_times) == 15 and (now - request_times[0]).seconds < 60:
            await message.channel.send("⏳ Limite de 15 análises/minuto atingido!")
            return
        
        request_times.append(now)
        daily_requests["count"] += 1
        save_daily_requests()

        if not message.content.lower().startswith("ty: desafio"):
            return
        
        try:
            # Extrai as partes da mensagem
            _, titulo_desafio, code = message.content.split("\n", 2)
            desafio = titulo_desafio.replace("Desafio: ", "").strip().lower()

            if desafio not in challenge_data:
                await message.channel.send("❌ Desafio não encontrado. Verifique o nome do desafio.")
                return

            recompensa = challenge_data[desafio]["xp"]
            await message.channel.send("Analisando o código, um momento... 🧐")

            analise = (await code_analysis(code)).strip().lower()
        
            # Exibe a análise completa
            await message.channel.send(f"📝 Análise do código para **{titulo_desafio}**:\n```{analise}```")
        
            # Verificação por palavras-chave
            CORRETO_KEYWORDS = [
                "✅",
                "correto",
                "sem erros",
                "não possui erros",
                "está correto",
                "funciona corretamente",
                "código válido"
            ]
        
            INCORRETO_KEYWORDS = [
                "❌",
                "erro",
                "incorreto",
                "ajustes necessários",
                "problema",
                "linha"
            ]        
            
            # Verifica primeiro se há palavras de erro
            if any(palavra in analise for palavra in INCORRETO_KEYWORDS):
                await message.channel.send("O código ainda precisa de ajustes. Continue tentando! 💪")
            # Depois verifica se está correto
            elif any(palavra in analise for palavra in CORRETO_KEYWORDS):
                add_xp(message.author.id, recompensa)
                await message.channel.send(f"{message.author.mention}, seu código está correto! Você ganhou **{recompensa} XP** 🎉")
            else:
                # Caso ambíguo
                await message.channel.send("Não consegui determinar se o código está correto. Verifique a análise acima.")
            
        except ValueError:
            await message.channel.send("❌ Formato inválido. Use:\n`ty: desafio`\n`Desafio: <nome>`\n```python\n<código>\n```")

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
        load_daily_requests()  # Carrega as requisições diárias        
    
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