import discord
from discordLevelingSystem import DiscordLevelingSystem, RoleAward, LevelUpAnnouncement
from discord.ext import commands 

TOKEN = "" #your bot's token here

bot = commands.Bot(command_prefix="!")

main_guild_id = 850809412011950121

my_awards = {
    main_guild_id : [
        RoleAward(role_id=831672678586777601, level_requirement=1, role_name='Rookie'),
        RoleAward(role_id=831672730583171073, level_requirement=2, role_name='Associate'),
        RoleAward(role_id=831672814419050526, level_requirement=3, role_name='Legend')
    ]
}

announcement = LevelUpAnnouncement(f'{LevelUpAnnouncement.Member.mention} just leveled up to level {LevelUpAnnouncement.LEVEL} 😎')

# DiscordLevelingSystem.create_database_file(r'C:\Users\Infinix\Documents') database file already created

lvl = DiscordLevelingSystem(rate=1, per=60.0, awards=my_awards, level_up_announcement=announcement)
lvl.connect_to_database_file(r'C:\Users\Infinix\Documents\DiscordLevelingSystem.db')

@bot.event
async def on_message(message):
    await lvl.award_xp(amount=15, message=message)

bot.run(TOKEN)
