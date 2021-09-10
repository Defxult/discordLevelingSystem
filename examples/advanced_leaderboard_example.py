import discord
from discordLevelingSystem import DiscordLevelingSystem, MemberData
from discord.ext import commands 

TOKEN = "" #your bot's token here

bot = commands.Bot(command_prefix="!")
lvl = DiscordLevelingSystem(rate=1, per=60.0)
lvl.connect_to_database_file(r'C:\Users\Infinix\Documents\DiscordLevelingSystem.db')

@bot.command(aliases=["lb", "top"])
async def leaderboard(ctx):
  data = await lvl.each_member_data(ctx.guild, sort_by='rank')
  
  embed = discord.Embed(title=f"Leaderboard for {ctx.guild.id}", color=discord.Color.green())
  embed.set_thumbnail(ctx.guild.icon_url)
  
  num = 1
  for names in data:
    if num > 10:
      break
    embed.add_field(name=f"#{num}・{names.name}",value=f"LEVEL: **{names.level}**・XP: **{names.total_xp}**", inline=False)
    num += 1
  
  return await ctx.reply(embed=embed)


bot.run(TOKEN)
