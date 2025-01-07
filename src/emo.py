import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)
user_xp = {} # Armazenamento do XP de todos os usuários

def get_user_xp(user_id):
    # Função para retornar o XP do usuário. (Provisório)
    return 100  # Exemplo

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Captura XP para o cálculo
    user_xp = get_user_xp(message.author.id)
    if user_xp >= 400:
        role = discord.utils.get(message.guild.roles, name="🛠️ Escudeiro")
        if role not in message.author.roles:
            await message.author.add_roles(role)
            await message.channel.send(f"Parabéns, {message.author.mention}! Você ganhou o Emo de 🛠️ Escudeiro!")

    if user_xp >= 900:
        role = discord.utils.get(message.guild.roles, name="✝️ Monge Guerreiro")
        if role not in message.author.roles:
            await message.author.add_roles(role)
            await message.channel.send(f"Parabéns, {message.author.mention}! Você ganhou o Emo de ✝️ Monge Guerreiro! Agora você faz parte de uma ordem militar religiosa.")



bot.run(TOKEN)
