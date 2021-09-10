import discord
from discordLevelingSystem import DiscordLevelingSystem, MemberData
from discord.ext import commands
import aiosqlite #I use aiosqlite db


TOKEN = "" #your bot's token here

bot = commands.Bot(command_prefix="!")
lvl = DiscordLevelingSystem(rate=1, per=60.0, bot=bot) # your bot instance variable is needed
lvl.connect_to_database_file(r'C:\Users\Infinix\Documents\DiscordLevelingSystem.db')


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


async def createtable():
  conn = await aiosqlite.connect("C:\Users\Infinix\Documents\configs.db")
  cur = conn.cursor()
  await cur.execute("CREATE TABLE IF NOT EXISTS config(guild_id INT, announcement_toggle BOOLEAN, level_up_channel_id INT)")
  await conn.commit()
  await cur.close()
  await conn.close()
  
  return


async def insert():
  #do rest of the stuffs here
  pass


async def fetch_details(guild):
  await createtable()
  conn = await aiosqlite.connect("C:\Users\Infinix\Documents\configs.db")
  conn.row_factory = dict_factory #dict values
  cur = conn.cursor()
  cur = await cur.execute("SELECT * FROM config WHERE guild_id = ?", (guild.id,))
  data = await cur.fetchone()
  await cur.close()
  await conn.close()
  
  return data
  
  
@bot.event
async def on_dls_level_up(member: discord.Member, message: discord.Message, data: MemberData):
  details = await fetch_details(member.guild)
  if not fetch_details:
    return
  toggle = details["announcement_toggle"]
  channel_id = details["level_up_channel_id"]
  
  if toggle:
    ch = await bot.fetch_channel(channel_id)
    
    embed = discord.Embed(title=f"Congratulations {member.name}!", description=f"You have levelled up to **level {data.level}**!", color=discord.Color.gold())
    embed.set_thumbnail(member.avatar_url) 
    embed.set_footer(text=f"Rank in the server: {data.rank}")
    return await message.channel.send(embed=embed)

bot.run(TOKEN)
