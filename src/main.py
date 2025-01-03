# This example requires the 'members' privileged intent to function.

import os
import asyncio
import discord
from discord.message import Message
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = f'Welcome {member.mention} to {guild.name}!'
            await guild.system_channel.send(to_send)
    
    async def on_message(self, message: Message):
        print(type(message))
        if message.content.startswith('!editme'):
            msg = await message.channel.send("10") 
            await asyncio.sleep(3)
            await msg.edit(content="40")


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = MyClient(intents=intents)
client.run(TOKEN)