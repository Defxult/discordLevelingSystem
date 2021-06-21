A library to implement a leveling system into a discord bot. One of the most popular discord bots out there is MEE6 and it's leveling system. This library provides ways to easily implement one for yourself. It uses SQLite (aiosqlite) to locally query things such as their XP, rank, and level. Various amounts of other methods and classes are also provided so you can access or remove contents from the database file.

If your discord.py version is 1.5.0+, [intents](https://discordpy.readthedocs.io/en/latest/intents.html) are required

## Github Updates vs PyPI Updates
The Github version of this library will always have the latest changes, fixes, and additions before the [PyPI](https://pypi.org/project/discordLevelingSystem/) version. You can install the Github version by doing:
```
pip install git+https://github.com/Defxult/discordLevelingSystem.git
```
You must have [Git](https://git-scm.com/) installed in order to do this. With that said, the current README.md documentation represents the Github version of this library. If you are using the PyPI version of this library, it is suggested to read the README.md that matches your PyPI version [here](https://github.com/Defxult/discordLevelingSystem/releases/tag/v0.0.1) because documentation may have changed.

* `Github: v0.0.2`
* `PyPI: v0.0.2`

## How to install
```txt
pip install discordLevelingSystem
```

<!-- If you are using `v0.0.2.dev` and discover any bugs, please don't hesitate to put them in [issues](https://github.com/Defxult/discordLevelingSystem/issues) so they can be fixed before release 😀 -->

---
## Showcase
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/835010159092039680/leveling_showcase.gif)

---
## How to import
```py
from discordLevelingSystem import DiscordLevelingSystem, LevelUpAnnouncement, RoleAward
```


## DiscordLevelingSystem
```class DiscordLevelingSystem(rate=1, per=60.0, awards=None, **kwargs)```

---
### Parameters of the DiscordLevelingSystem constructor
* `rate` (`int`) The amount of messages each member can send before the cooldown triggers
* `per` (`float`) The amount of seconds each member has to wait before gaining more XP, aka the cooldown
* `awards` (`Union[Dict[int, List[RoleAward]], None]`) The role given to a member when they reach a `RoleAward` level requirement
---
### Kwargs of the DiscordLevelingSystem constructor
| Name | Type | Default Value | Info
|------|------|---------------|-----
| `no_xp_roles` | `List[int]` | `None` | A list of role ID's. Any member with any of those roles will not gain XP when sending messages
| `no_xp_channels` | `List[int]` | `None` | A list of text channel ID's. Any member sending messages in any of those text channels will not gain XP
| `announce_level_up` | `bool` | `True` | If `True`, level up messages will be sent when a member levels up
| `stack_awards` | `bool` | `True` | If this is `True`, when the member levels up the assigned role award will be applied. If `False`, the previous role award will be removed and the level up assigned role will also be applied
| `level_up_announcement` | `Union[LevelUpAnnouncement, List[LevelUpAnnouncement]]` | `LevelUpAnnouncement()` | The message that is sent when someone levels up. If this is a list of `LevelUpAnnouncement`, one is selected at random

---
### Attributes
* `no_xp_roles`
* `no_xp_channels`
* `announce_level_up`
* `stack_awards`
* `level_up_announcement`
* `rate` (property - read only)
* `per` (property - read only)

> NOTE: All attributes can be set during initialization
---
## Initial Setup
When setting up the leveling system, a database file needs to be created in order for the library to function. 
* Associated static method
  * `DiscordLevelingSystem.create_database_file(path: str)`

The above *static* method is used the create the database file for you in the path you specify. This method only needs to be called once. Example:
```py
DiscordLevelingSystem.create_database_file(r'C:\Users\Defxult\Documents')
```
Once created, there is no need to ever run that method again unless you want to create a new database file from scratch. Now that you have the database file, you can use the leveling system.

---
## Connecting to the Database
* Associated method
  * `DiscordLevelingSystem.connect_to_database_file(path: str)`

Since the database file has already been created, all you need to do is connect to it. 
> NOTE: When connecting to the database file, the event loop must not be running
<div align="left"><sub>EXAMPLE</sub></div>

```py
from discord.ext import commands
from discordLevelingSystem import DiscordLevelingSystem

bot = commands.Bot(...)
lvl = DiscordLevelingSystem(rate=1, per=60.0)
lvl.connect_to_database_file(r'C:\Users\Defxult\Documents\DiscordLevelingSystem.db')

bot.run(...)
```
---

## RoleAward
```class RoleAward(role_id: int, level_requirement: int, role_name=None)```

You can assign roles to the system so when someone levels up to a certain level, they are given that role. `RoleAward` is how that is accomplished.

---
### Parameters of the RoleAward constructor
* `role_id` (`int`) ID of the role that is to be awarded.
* `level_requirement` (`int`) What level is required for a member to be awarded the role.
* `role_name` (`str`) An optional name. Nothing is done with this value, it is used for visual identification purposes.

When creating role awards, all role ID's and level requirements must be unique. Level requirements must also be in ascending order. It is also possible to assign different role awards for different guilds. If you don't want any role awards, set the `awards` parameter to `None`. When setting `awards`, it accepts a `dict` where they keys are guild IDs and the values are a `list` of `RoleAward`
<div align="left"><sub>EXAMPLE</sub></div>

```py
from discordLevelingSystem import DiscordLevelingSystem, RoleAward

johns_server = 587937522043060224
janes_server = 850809412011950121

my_awards = {
    johns_server : [
        RoleAward(role_id=831672678586777601, level_requirement=1, role_name='Rookie'),
        RoleAward(role_id=831672730583171073, level_requirement=2, role_name='Associate'),
        RoleAward(role_id=831672814419050526, level_requirement=3, role_name='Legend')
    ],
    janes_server : [
        RoleAward(role_id=851400453904400385, level_requirement=1, role_name='Silver'),
        RoleAward(role_id=851379776111116329, level_requirement=2, role_name='Gold'),
        RoleAward(role_id=851959077071880202, level_requirement=3, role_name='Diamond')
    ]
}

lvl = DiscordLevelingSystem(..., awards=my_awards)
```
---

## LevelUpAnnouncement
```class LevelUpAnnouncement(message=default_message, level_up_channel_ids=None, allowed_mentions=default_mentions, tts=False, delete_after=None)```

Level up announcements are for when you want to implement your own level up messages. It provides access to who leveled up, their rank, level and much more. It also uses some of discord.py's kwargs from it's `Messageable.send` such as `allowed_mentions`, `tts`, and `delete_after` to give you more control over the sent message.

---
### Parameters of the LevelUpAnnouncement constructor

* `message` (`Union[str, discord.Embed]`) The message that is sent when someone levels up. Defaults to `"<mention>, you are now **level <level>!**"`

* `level_up_channel_ids` (`List[int]`) The text channel IDs where all level up messages will be sent for each server. If `None`, the level up message will be sent in the channel where they sent the message (example below).

* `allowed_mentions` (`discord.AllowedMentions`) Used to determine who can be pinged in the level up message. Defaults to `discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)`

* `tts` (`bool`) When the level up message is sent, have discord read the level up message aloud.

* `delete_after` (`float`) Delete the level up message after an x amount of seconds.

### Class Attributes
The `LevelUpAnnouncement` class provides a set of markdown attributes for you to use so you can access certain information in a level up message.

* `LevelUpAnnouncement.TOTAL_XP` The members current total XP amount
* `LevelUpAnnouncement.LEVEL` The members current level
* `LevelUpAnnouncement.RANK` The members current rank

The below markdown attributes takes the information from a `discord.Member` object so you can access member information in the level up message.

* `LevelUpAnnouncement.Member.avatar_url`
* `LevelUpAnnouncement.Member.created_at`
* `LevelUpAnnouncement.Member.default_avatar_url`
* `LevelUpAnnouncement.Member.discriminator`
* `LevelUpAnnouncement.Member.display_name`
* `LevelUpAnnouncement.Member.id`
* `LevelUpAnnouncement.Member.joined_at`
* `LevelUpAnnouncement.Member.mention`
* `LevelUpAnnouncement.Member.name`
* `LevelUpAnnouncement.Member.nick`
* `LevelUpAnnouncement.Member.Guild.icon_url`
* `LevelUpAnnouncement.Member.Guild.id`
* `LevelUpAnnouncement.Member.Guild.name`

<div align="left"><sub>EXAMPLE</sub></div>

```py
from discordLevelingSystem import DiscordLevelingSystem, LevelUpAnnouncement

embed = discord.Embed(color=discord.Color.blue())
embed.set_author(name=LevelUpAnnouncement.Member.name, icon_url=LevelUpAnnouncement.Member.avatar_url)
embed.description = f'Congrats {LevelUpAnnouncement.Member.mention}! You are now level {LevelUpAnnouncement.LEVEL} 😎'

announcement = LevelUpAnnouncement(embed)

lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)

# NOTE: You can have multiple level up announcements by setting the parameter to a list of LevelUpAnnouncement
lvl = DiscordLevelingSystem(..., level_up_announcement=[announcement_1, announcement_2, ...])
```
When it comes to `level_up_channel_ids`, you can set a designated channel for each server. If you don't set a level up channel ID for a specific server, the level up message will be sent in the channel where the member leveled up. You don't have to specify a level up channel ID for each server unless you'd like to.
```py
johns_bot_commands = 489374746737648734 # text channel ID from server A
janes_levelup_channel = 58498304930493094 # text channel ID from server B

announcement = LevelUpAnnouncement(..., level_up_channel_ids=[johns_bot_commands, janes_levelup_channel])
lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)
```
---
## Handling XP
Method `award_xp` is how members gain XP. This method is placed inside the `on_message` event of your bot. Members will gain XP if they send a message and if they're *not* on cooldown. Spamming messages will not give them XP.
> NOTE: Members cannot gain XP in DM's
* Associated methods
  * `await DiscordLevelingSystem.add_xp(member: Member, amount: int)`
  * `await DiscordLevelingSystem.remove_xp(member: Member, amount: int)`
  * `await DiscordLevelingSystem.set_level(member: Member, level: int)`
  * `await DiscordLevelingSystem.award_xp(*, amount=[15, 25], message: Message, refresh_name=True, **kwargs)`


### Parameters for award_xp
* `amount` (`Union[int, List[int]]`) The amount of XP to award to the member per message. Must be from 1-25. Can be a list with a minimum and maximum length of two. If `amount` is a list of two integers, it will randomly pick a number in between those numbers including the numbers provided.
* `message` (`discord.Message`) A discord message object
* `refresh_name` (`bool`) Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is suggested to leave this as `True` so the database can always have the most up-to-date record.

### Kwargs for award_xp
* `bonus` (`DiscordLevelingSystem.Bonus`) Used to set the roles that will award bonus XP.
  * `class Bonus(role_ids: List[int], bonus_amount: int, multiply: bool)`
  * **Parameters of the DiscordLevelingSystem.Bonus constructor**
    * `role_ids` (`List[int]`) The role(s) a member must have to be able to get bonus XP. They only need to have one of these roles to get the bonus
    * `bonus_amount` (`int`) Amount of extra XP to be awarded
    * `multiply` (`bool`) If set to `True`, this will operate on a x2, x3 basis. Meaning if you have the awarded XP amount set to 10 and you want the bonus XP role to be awarded 20, it must be set to 2, not 10. If `False`, it operates purely on the given value. Meaning if you have the awarded XP set to 10 and you want the bonus XP role to be awarded 20, it must be set to 10.

<div align="left"><sub>EXAMPLE</sub></div>

```py
lvl = DiscordLevelingSystem(...)

nitro_booster = 851379776111116329
associate_role = 851400453904400385

@bot.event
async def on_message(message):
    await lvl.award_xp(amount=[15, 25], message=message, bonus=DiscordLevelingSystem.Bonus([nitro_booster, associate_role], 20, multiply=False))
```
---

## MemberData
Accessing the raw information inside the database file can look a bit messy if you don't know exactly what you're looking at. To make things easier, this library comes with the `MemberData` class. A class which returns information about a specific member in the database.

* Associated methods
  * `await DiscordLevelingSystem.get_data_for(member: Member) -> MemberData`
  * `await DiscordLevelingSystem.each_member_data(guild: Guild, sort_by=None) -> List[MemberData]`

### Attributes
* `id_number` (`int`) The members ID
* `name` (`str`) The members name
* `level` (`int`) The members level
* `xp` (`int`) The members xp
* `total_xp` (`int`) The members total xp
* `rank` (`int`) The members rank
* `mention` (`str`) The discord member mention string

<div align="left"><sub>EXAMPLE</sub></div>

```py
lvl = DiscordLevelingSystem(...)

@bot.command()
async def rank(ctx):
    data = await lvl.get_data_for(ctx.author)
    await ctx.send(f'You are level {data.level} and your rank is {data.rank}')

@bot.command()
async def leaderboard(ctx):
    data = await lvl.each_member_data(ctx.guild, sort_by='rank')
    # show the leaderboard whichever way you'd like
```

---
## Full Example
With all classes and core methods introduced, here is a basic implementation of this library.
```py
from discord.ext import commands
from discordLevelingSystem import DiscordLevelingSystem, RoleAward, LevelUpAnnouncement

bot = commands.Bot(...)

main_guild_id = 850809412011950121

my_awards = {
    main_guild_id : [
        RoleAward(role_id=831672678586777601, level_requirement=1, role_name='Rookie'),
        RoleAward(role_id=831672730583171073, level_requirement=2, role_name='Associate'),
        RoleAward(role_id=831672814419050526, level_requirement=3, role_name='Legend')
    ]
}

announcement = LevelUpAnnouncement(f'{LevelUpAnnouncement.Member.mention} just leveled up to level {LevelUpAnnouncement.LEVEL} 😎')

# DiscordLevelingSystem.create_database_file(r'C:\Users\Defxult\Documents') database file already created
lvl = DiscordLevelingSystem(rate=1, per=60.0, awards=my_awards, level_up_announcement=announcement)
lvl.connect_to_database_file(r'C:\Users\Defxult\Documents\DiscordLevelingSystem.db')

@bot.event
async def on_message(message):
    await lvl.award_xp(amount=15, message=message)

bot.run(...)
```
---

## All methods for DiscordLevelingSystem
<details>
    <summary>Click to show all methods</summary>

* `await DiscordLevelingSystem.add_xp(member: Member, amount: int)`
  * Give XP to a member. This also changes their level so it matches the associated XP
---
* `await DiscordLevelingSystem.award_xp(*, amount=[15,25], message: Message, refresh_name=True, **kwargs)`
  * Give XP to the member that sent a message
---
* `DiscordLevelingSystem.backup_database_file(path: str, with_timestamp=False)`
  * Create a copy of the database file to the specified path. If a copy of the backup file is already in the specified path it will be overwritten
---
* `await DiscordLevelingSystem.change_cooldown(rate: int, per: float)`
  * Update the cooldown rate
---
* `await DiscordLevelingSystem.clean_database(guild: Guild) -> int`
  * Removes the data for members that are no longer in the guild, thus reducing the database file size. It is recommended to have this method in a background loop in order to keep the database file free of records that are no longer in use
---
* `DiscordLevelingSystem.connect_to_database_file(path: str)`
  * Connect to the existing database file in the specified path
---
* `DiscordLevelingSystem.create_database_file(path: str)`
  * *static method* Create the database file and implement the SQL data for the database
---
* `await DiscordLevelingSystem.each_member_data(guild: Guild, sort_by=None) -> List[MemberData]`
  * Return each member in the database as a `MemberData` object for easy access to their XP, level, etc. You can sort the data with `sort_by` with the following values: "name", "level", "xp", "rank"
---
* `await DiscordLevelingSystem.export_as_json(path: str, guild: Union[Guild, None])`
  * Export a json file that represents the database to the path specified
---
* `await DiscordLevelingSystem.get_data_for(member: Member) -> MemberData`
  * Get the `MemberData` object that represents the specified member
---
* `await DiscordLevelingSystem.get_level_for(member: Member) -> int`
  * Get the level for the specified member
---
* `await DiscordLevelingSystem.get_rank_for(member: Member) -> int`
  * Get the rank for the specified member
---
* `await DiscordLevelingSystem.get_record_count(guild=None) -> int`
  * Get the amount of members that are registered in the database. If `guild` is set to `None`, ALL members in the database will be counted
---
* `await DiscordLevelingSystem.get_total_xp_for(member: Member) -> int`
  * Get the total XP for the specified member
---
* `await DiscordLevelingSystem.get_xp_for(member: Member) -> int`
  * Get the XP for the specified member
---
* `await DiscordLevelingSystem.is_in_database(member: Union[Member, int]) -> bool`
  * A quick check to see if a member is in the database. This is not guild specific
---
* `await DiscordLevelingSystem.next_level_up(member: Member) -> int`
  * Get the amount of XP needed for the specified member to level up
---
* `await DiscordLevelingSystem.raw_database_contents(guild=None) -> List[tuple]`
  * Returns everything in the database. Can specify which guild information will be extracted
---
* `await DiscordLevelingSystem.refresh_names(guild: Guild) -> int`
  * Update names inside the database. This does not add anything new. It simply verifies if the name in the database matches their current name, and if they don't match, update the database name
---
* `await DiscordLevelingSystem.remove_from_database(member: Union[Member, int]) -> bool`
  * Remove a member from the database. This is not guild specific
---
* `await DiscordLevelingSystem.remove_xp(member: Member, amount: int)`
  * Remove XP from a member. This also changes their level so it matches the associated XP
---
* `await DiscordLevelingSystem.reset_everyone(guild: Union[Guild, None], *, intentional=False)`
  * Sets EVERYONES XP, total XP, and level to zero in the database. Can specify which guild to reset
---
* `await DiscordLevelingSystem.reset_member(member: Member)`
  * Sets the members XP, total XP, and level to zero
---
* `await DiscordLevelingSystem.set_level(member: Member, level: int)`
  * Sets the level for the member. This also changes their total XP so it matches the associated level
---
* `await DiscordLevelingSystem.sql_query_get(sql: str, parameters=None, fetch='ALL') -> Union[List[tuple], tuple]`
  * Query and return something from the database using SQL. The following columns are apart of the "leaderboard" table: guild_id, member_id, member_name, member_level, member_xp, member_total_xp
---
* `DiscordLevelingSystem.transfer(old: str, new: str, guild_id: int)`
  * *static method* Transfer the database records from a database file created from v0.0.1 to a blank database file created using v0.0.2+. If you were already using a v0.0.2+ database file, there's no need to use this method
---
* `await DiscordLevelingSystem.wipe_database(*, intentional=False)`
  * Delete EVERYTHING from the database

</details>

## Migrating from v0.0.1 to v0.0.2+
<details>
    <summary>Click to show details</summary>

This library was not originally designed with the use of multiple servers in mind, so all the data you might have currently (your database file was created in `v0.0.1`) should be from a single server. With `v0.0.2`, the structure of the database file was changed to accommodate this fix. That means if you are currently using a `v0.0.1` database file and update to `v0.0.2+`, a vast majority of the library will be broken. To avoid this, you need to transfer all your `v0.0.1` database file records to a `v0.0.2+` database file. This can be done using the `transfer` method.

* Associated static method
  * `DiscordLevelingSystem.transfer(old: str, new: str, guild_id: int)`

### Parameters
* `old` (`str`) The path of the `v0.0.1` database file
* `new` (`str`) The path of the `v0.0.2+` database file (a brand new file from using `DiscordLevelingSystem.create_database_file(path: str)`)
* `guild_id` (`int`) ID of the guild that was originally used with this library

<div align="left"><sub>EXAMPLE</sub></div>

```py
from discordLevelingSystem import DiscordLevelingSystem

old = r'C:\Users\Defxult\Documents\DiscordLevelingSystem.db'
new = r'C:\Users\Defxult\Desktop\DiscordLevelingSystem.db'

DiscordLevelingSystem.transfer(old, new, guild_id=850809412011950121)
```

</details>
