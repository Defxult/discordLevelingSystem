import discord
from discordLevelingSystem import DiscordLevelingSystem, MemberData
from discord.ext import commands 

bot = commands.Bot(command_prefix="!")
lvl = DiscordLevelingSystem(rate=1, per=60.0, bot=bot) # your bot instance variable is needed
lvl.connect_to_database_file(r'C:\Users\Infinix\Documents\DiscordLevelingSystem.db')

@bot.event
async def on_dls_level_up(member: discord.Member, message: discord.Message, data: MemberData):
  await message.channel.send(f"Congratulations {member.mention}! You have levelled up!")
