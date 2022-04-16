A library to implement a leveling system into a discord bot. One of the most popular discord bots out there is MEE6 and it's leveling system. This library provides ways to easily implement one for yourself. It uses SQLite (aiosqlite) to locally query things such as their XP, rank, and level. Various amounts of other methods and classes are also provided so you can access or remove contents from the database file.

## GitHub Updates vs PyPI Updates
The GitHub version of this library will always have the latest changes, fixes, and additions before the [PyPI](https://pypi.org/project/discordLevelingSystem/) version. You can install the GitHub version by doing:
  ```
  $ pip install git+https://github.com/Defxult/discordLevelingSystem
  ```
  You must have [Git](https://git-scm.com/) installed in order to do this. With that said the current README.md documentation represents the GitHub version of this library. If you are using the PyPI version of this library, it is suggested to read the README.md that matches your PyPI version [here](https://github.com/Defxult/discordLevelingSystem/releases) because documentation may have changed.

* `GitHub: v1.2.0`
* `PyPI: v1.1.0`

---
## How to install
```
$ pip install discordLevelingSystem
```

---

## Showcase
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/835010159092039680/leveling_showcase.gif)

---
## How to import
```py
from discordLevelingSystem import DiscordLevelingSystem, LevelUpAnnouncement, RoleAward
```

---
## Intents
[Intents](https://docs.pycord.dev/en/master/intents.html) are required for proper functionality
```py
bot = commands.Bot(..., intents=discord.Intents(messages=True, guilds=True, members=True))
```
---


## DiscordLevelingSystem
```class DiscordLevelingSystem(rate=1, per=60.0, awards=None, **kwargs)```

---
### Parameters of the DiscordLevelingSystem constructor
* `rate` (`int`) The amount of messages each member can send before the cooldown triggers
* `per` (`float`) The amount of seconds each member has to wait before gaining more XP, aka the cooldown
* `awards` (`Optional[Dict[int, List[RoleAward]]]`) The role given to a member when they reach a `RoleAward` level requirement
---
### Kwargs of the DiscordLevelingSystem constructor
| Name | Type | Default Value | Info
|------|------|---------------|-----
| `no_xp_roles` | `Sequence[int]` | `None` | A sequence of role ID's. Any member with any of those roles will not gain XP when sending messages
| `no_xp_channels` | `Sequence[int]` | `None` | A sequence of text channel ID's. Any member sending messages in any of those text channels will not gain XP
| `announce_level_up` | `bool` | `True` | If `True`, level up messages will be sent when a member levels up
| `stack_awards` | `bool` | `True` | If this is `True`, when the member levels up the assigned role award will be applied. If `False`, the previous role award will be removed and the level up assigned role will also be applied
| `level_up_announcement` | `Union[LevelUpAnnouncement, Sequence[LevelUpAnnouncement]]` | `LevelUpAnnouncement()` | The message that is sent when someone levels up. If this is a sequence of `LevelUpAnnouncement`, one is selected at random
|`bot` | ` Union[AutoShardedBot, Bot]` | `None` | Your bot instance variable. Used only if you'd like to use the `on_dls_level_up` event

---
### Attributes
* `no_xp_roles`
* `no_xp_channels`
* `announce_level_up`
* `stack_awards`
* `level_up_announcement`
* `bot`
* `rate` (`int`) Read only property from the constructor
* `per` (`float`) Read only property from the constructor
* `database_file_path` (`str`) Read only property
* `active` (`bool`) Enable/disable the leveling system. If `False`, nobody can gain XP when sending messages unless this is set back to `True`

> NOTE: All attributes can be set during initialization
---
## Initial Setup
When setting up the leveling system, a database file needs to be created in order for the library to function. 
* Associated static method
  * `DiscordLevelingSystem.create_database_file(path: str)`

The above *static* method is used to create the database file for you in the path you specify. This method only needs to be called once. Example:
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
* `role_name` (`Optional[str]`) A name you can set for the award. Nothing is done with this value, it is used for visual identification purposes only.
---
### Attributes
* `role_id`
* `level_requirement`
* `role_name`
* `mention` (`str`) The discord role mention string

When creating role awards, all role IDs and level requirements must be unique. Level requirements must also be in ascending order. It is also possible to assign different role awards for different guilds. If you don't want any role awards, set the `awards` parameter to `None`. When setting `awards`, it accepts a `dict` where the keys are guild IDs and the values are a `list` of `RoleAward`
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

Level up announcements are for when you want to implement your own level up messages. It provides access to who leveled up, their rank, level and much more. It also uses some of pycord's kwargs from it's `Messageable.send` such as `allowed_mentions`, `tts`, and `delete_after` to give you more control over the sent message.

---
### Parameters of the LevelUpAnnouncement constructor

* `message` (`Union[str, discord.Embed]`) The message that is sent when someone levels up. Defaults to `"<mention>, you are now **level <level>!**"`

* `level_up_channel_ids` (`Optional[Sequence[int]]`) The text channel IDs where all level up messages will be sent for each server. If `None`, the level up message will be sent in the channel where they sent the message (example below).

* `allowed_mentions` (`discord.AllowedMentions`) Used to determine who can be pinged in the level up message. Defaults to `discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)`

* `tts` (`bool`) When the level up message is sent, have discord read the level up message aloud.

* `delete_after` (`Optional[float]`) Delete the level up message after an x amount of seconds.

### Class Attributes
The `LevelUpAnnouncement` class provides a set of markdown attributes for you to use so you can access certain information in a level up message.

* `LevelUpAnnouncement.TOTAL_XP` The members current total XP amount
* `LevelUpAnnouncement.LEVEL` The members current level
* `LevelUpAnnouncement.RANK` The members current rank

The below markdown attributes takes the information from a `discord.Member` object so you can access member information in the level up message.

* `LevelUpAnnouncement.Member.avatar_url`
* `LevelUpAnnouncement.Member.banner_url`
* `LevelUpAnnouncement.Member.created_at`
* `LevelUpAnnouncement.Member.default_avatar_url`
* `LevelUpAnnouncement.Member.discriminator`
* `LevelUpAnnouncement.Member.display_avatar_url`
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

embed = discord.Embed()
embed.set_author(name=LevelUpAnnouncement.Member.name, icon_url=LevelUpAnnouncement.Member.avatar_url)
embed.description = f'Congrats {LevelUpAnnouncement.Member.mention}! You are now level {LevelUpAnnouncement.LEVEL} 😎'

announcement = LevelUpAnnouncement(embed)

lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)

# NOTE: You can have multiple level up announcements by setting the parameter to a sequence of LevelUpAnnouncement
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
* `amount` (`Union[int, Sequence[int]]`) The amount of XP to award to the member per message. Must be from 1-25. Can be a sequence with a minimum and maximum length of two. If `amount` is a sequence of two integers, it will randomly pick a number in between those numbers including the numbers provided.
* `message` (`discord.Message`) A discord message object
* `refresh_name` (`bool`) Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is suggested to leave this as `True` so the database can always have the most up-to-date record.

### Kwargs for award_xp
* `bonus` (`DiscordLevelingSystem.Bonus`) Used to set the roles that will be awarded bonus XP.
  * `class Bonus(role_ids: Sequence[int], bonus_amount: int, multiply: bool)`
  * **Parameters of the DiscordLevelingSystem.Bonus constructor**
    * `role_ids` (`Sequence[int]`) The role(s) a member must have to be able to get bonus XP. They only need to have one of these roles to get the bonus
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
  * `await DiscordLevelingSystem.each_member_data(guild: Guild, sort_by=None, limit=None) -> List[MemberData]`

### Attributes
* `id_number` (`int`) The members ID
* `name` (`str`) The members name
* `level` (`int`) The members level
* `xp` (`int`) The members xp
* `total_xp` (`int`) The members total xp
* `rank` (`Optional[int]`) The members rank
* `mention` (`str`) The discord member mention string

### Methods
* `MemberData.to_dict() -> dict`

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
## Events
You can set an event to be called when a member levels up. Using the event is considered as an enhanced `LevelUpAnnouncement` because it provides more capabilities rather than simply sending a message with only text/an embed. The `on_dls_level_up` event takes three parameters:
* `member` (`discord.Member`) The member that leveled up
* `message` (`discord.Message`) The message that triggered the level up
* `data` (`MemberData`) The database information for that member

```py
bot = commands.Bot(...)
lvl = DiscordLevelingSystem(..., bot=bot) # your bot instance variable is needed

@bot.event
async def on_dls_level_up(member: discord.Member, message: discord.Message, data: MemberData):
    # You can do a lot more here compared to LevelUpAnnouncement
    # - create a level up image and send it with discord.File
    # - call additional functions that you may need
    # - access to all attributes/methods that are available within discord.Member and discord.Message
```
> NOTE: `LevelUpAnnouncement` and `on_dls_level_up` are not the same. Level up messages are sent by default by the library. If you'd like to only use `on_dls_level_up`, you need to disable level up announcements (`lvl.announce_level_up = False`)

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

* *await* **add_record**(`guild_id, member_id, member_name, level`) - Manually add a record to the database. If the record already exists (the `guild_id` and `member_id` was found), only the level will be updated. If there were no records that matched those values, all provided information will be added
  * **Parameters**
    * **guild_id** (`int`) The guild ID to register
    * **member_id** (`int`) The member ID to register
    * **member_name** (`str`) The member name to register
    * **level** (`int`) The member level to register. Must be from 0-100
  * **Raises**
    * `DiscordLevelingSystemError` - The value given from a parameter was not of the correct type or "level" was not 0-100


* *await* **add_xp**(`member, amount`) - Give XP to a member. This also changes their level so it matches the associated XP
  * **Parameters**
    * **member** (`discord.Member`) The member to give XP to
    * **amount** (`int`) Amount of XP to give to the member
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - Parameter "amount" was less than or equal to zero. The minimum value is 1 


* *await* **award_xp**(`*, amount = [15, 25], message, refresh_name = True, **kwargs`) - Give XP to the member that sent a message
  * **Parameters**
    * **amount** (`Union[int, Sequence[int]]`)
    * **message** (`discord.Message`) A message object
    * **refresh_name** (`bool`) Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is suggested to leave this as `True` so the database can always have the most up-to-date record
  * **Kwargs**
    * **bonus** (`DiscordLevelingSystem.Bonus`) Set the bonus values. Read the `DiscordLevelingSystem.Bonus` doc string for more details (defaults to `None`)
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* **backup_database_file**(`path, with_timestamp = False`) - Create a copy of the database file to the specified path. If a copy of the backup file is already in the specified path it will be overwritten
  * **Parameters**
    * **path** (`str`) The path to copy the database file to
    * **with_timestamp** (`bool`) Creates a unique file name that has the date and time of when the backup file was created. This is useful when you want multiple backup files
  * **Raises**
    * `DiscordLevelingSystemError` - Path doesn't exist or points to another file
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **change_cooldown**(`rate, per`) - Update the cooldown rate
  * **Parameters**
    * **rate** (`int`) The amount of messages each member can send before the cooldown triggers
    * **per** (`float`) The amount of seconds each member has to wait before gaining more XP, aka the cooldown
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - The rate or per value was not greater than zero


* *await* **clean_database**(`guild`) - Removes the data for members that are no longer in the guild, thus reducing the database file size. It is recommended to have this method in a background loop in order to keep the database file free of records that are no longer in use
  * **Parameters**
    * **guild** (`discord.Guild`) The guild records to clean
  * **Returns**
    * (`Optional[int]`) The amount of records that were removed from the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* **connect_to_database_file**(`path`) - Connect to the existing database file in the specified path
  * **Parameters**
    * **path** (`str`) The location of the database file
  * **Raises**
    * `ConnectionFailure` - Attempted to connect to the database file when the event loop is already running
    * `DatabaseFileNotFound` - The database file was not found


* *static method* **create_database_file**(`path`) - Create the database file and implement the SQL data for the database
  * **Parameters**
    * **path** (`str`) The location to create the database file
  * **Raises**
    * `ConnectionFailure` - Attempted to create the database file when the event loop is already running
    * `DiscordLevelingSystemError` - The path does not exist or the path points to a file instead of a directory


* *await* **each_member_data**(`guild, sort_by = None, limit = None`) - Return each member in the database as a `MemberData` object for easy access to their XP, level, etc. You can sort the data with `sort_by` with the below values
  * **Parameters**
    * **guild** (`discord.Guild`) A guild object
    * **sort_by** (`Optional[str]`) Return each member sorted by: "name", "level", "xp", "rank". If `None`, it will return in the order they were added to the database
    * **limit** (`Optional[int]`) Restrict the amount of records returned to the specified amount
  * **Returns**
    * `List[MemberData]`
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - The value of `sort_by` was not recognized or `guild` was not of type `discord.Guild`


* *await* **export_as_json**(`path, guild`) - Export a json file that represents the database to the path specified
  * **Parameters**
    * **path** (`str`) Path to copy the json file to
    * **guild** (`discord.Guild`) The guild for which the data should be extracted from. If `None`, all guild information will be extracted from the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - The path does not exist or does not point to a directory


* **get_awards**(`guild = None`) - Get all `RoleAward`'s or only the `RoleAward`'s assigned to the specified guild
  * **Parameters**
    * **guild** (`Optional[Union[discord.Guild, int]]`) A guild object or a guild ID
  * **Returns**
    * (`Union[Dict[int, List[RoleAward]], List[RoleAward]]`) If `guild` is `None`, this return the awards `dict` that was set in constructor. If `guild` is specified, it returns a List[`RoleAward`] that matches the specified guild ID. Can also return `None` if awards were never set or if the awards for the specified guild was not found


* *await* **get_data_for**(`member`) - Get the `MemberData` object that represents the specified member
  * **Parameters**
    * **member** (`discord.Member`) The member to get the data for
  * **Returns**
    * (`MemberData`) Can be `None` if the member isn't in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **get_level_for**(`member`) - Get the level for the specified member
  * **Parameters**
    * **member** (`discord.Member`) Member to get the level for
  * **Returns**
    * (`int`) Can be `None` if the member isn't in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **get_rank_for**(`member`) - Get the rank for the specified member
  * **Parameters**
    * **member** (`discord.Member`) Member to get the rank for
  * **Returns**
    * (`int`) Can be `None` if the member isn't ranked yet
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **get_record_count**(`guild = None`) - Get the amount of members that are registered in the database. If `guild` is set to `None`, ALL members in the database will be counted
  * **Parameters**
    * **guild** (`Optional[discord.Guild]`) The guild for which to count the amount of records
  * **Returns**
    * (`int`)
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **get_total_xp_for**(`member`) - Get the total XP for the specified member
  * **Parameters**
    * **member** (`discord.Member`) Member to get the total XP for
  * **Returns**
    * (`int`) Can be `None` if the member isn't in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **get_xp_for**(`member`) - Get the XP for the specified member
  * **Parameters**
    * **member** (`discord.Member`) Member to get the XP for
  * **Returns**
    * (`int`) Can be `None` if the member isn't in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *static method* **get_xp_for_level**(`level`) - Returns the total amount of XP needed for the specified level. Levels go from 0-100
  * **Parameters**
    * **level** (`int`) The level XP information to retrieve
  * **Returns**
    * (`int`)
  * **Raises**
    * `DiscordLevelingSystemError` - The level specified does not exist


* *await* **insert**(`bot, guild_id, users, using, overwrite = False, show_results = True`) - Insert the records from your own leveling system into the library. A lot of leveling system tutorials out there use json files to store information. Although it might work, it is insufficient because json files are not made to act as a database. Using an actual database file has many benefits over a json file
  * **Parameters**
    * **bot** (`Union[discord.ext.commands.Bot, discord.ext.commands.AutoShardedBot]`) Your bot instance variable
    * **guild_id** (`int`) ID of the guild that you used your leveling system with
    * **users** (`Dict[int, int]`) This is the information that will be added to the database. The keys are user ID's, and the values are the users total XP or level. Note: This library only uses levels 0-100 and XP 0-1899250. If any number in this dict are over the levels/XP threshold, it is implicitly set back to this libraries maximum value
    * **using** (`str`) What structure your leveling system used. Options: "xp" or "levels". Some leveling systems give users only XP and they are ranked up based on that XP value. Others use a combination of levels and XP. If all the values in the `users` dict are based on XP, set this to "xp". If they are based on a users level, set this to "levels"
    * **overwrite** (`bool`) If a user you've specified in the `users` dict already has a record in the database, overwrite their current record with the one your inserting
    * **show_results** (`bool`) Print the results for how many of the `users` were successfully added to the database file. If any are unsuccessful, their ID along with the value you provided will also be shown
  * **Raises**
      * `DiscordLevelingSystemError` - The value given from a parameter was not of the correct type. The `users` dict was empty. Or your bot is not in the guild associated with `guild_id`       


* *await* **is_in_database**(`member, guild = None`) - A quick check to see if a member is in the database. This is not guild specific although it can be if `guild` is specified
  * **Parameters**
    * **member** (`Union[discord.Member, int]`) The member to check for. Can be the member object or that members ID
    * **guild** (`Optional[discord.Guild]`) The guild to check if the member is registered in
  * **Returns**
    * (`bool`)
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - Parameter `member` was not of type `discord.Member` or `int`


* *static method* **levels_and_xp**( ) -  Get the raw `dict` representation for the amount of levels/XP in the system. The keys in the `dict` returned is each level, and the values are the amount of XP needed to be awarded that level
  * **Returns**
    * (`Dict[str, int]`)


* *await* **next_level**(`member`) - Get the next level for the specified member
  * **Parameters**
    * **member** (`discord.Member`) Member to get the next level for
  * **Returns**
    * (`int`) If the member is currently max level (100), it will return 100. This can also return `None` if the member is not in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **next_level_up**(`member`) - Get the amount of XP needed for the specified member to level up
  * **Parameters**
    * **member** (`discord.Member`) Member to get the amount of XP needed for a level up
  * **Returns**
    * (`int`) Returns 0 if the member is currently at max level. Can return `None` if the member is not in the database.
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **raw_database_contents**(`guild = None`) - Returns everything in the database. Can specify which guild information will be extracted
  * **Parameters**
    * **guild** (`Optional[discord.Guild]`) The guild to extract the raw database contents from. If `None`, information about all guilds will be extracted
  * **Returns**
    * `List[Tuple[int, int, str, int, int, int]]` The tuples inside the list represents each row of the database:
      * Index 0 is the guild ID
      * Index 1 is their ID
      * Index 2 is their name
      * Index 3 is their level
      * Index 4 is their XP
      * Index 5 is their total xp
      * Can be an empty list if nothing is in the database
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **refresh_names**(`guild`) - Update names inside the database. This does not add anything new. It simply verifies if the name in the database matches their current name, and if they don't match, update the database name
  * **Parameters**
    * **guild** (`discord.Guild`) A guild object
  * **Returns**
    * `(Optional[int])` The amount of records in the database that were updated
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **remove_from_database**(`member, guild = None`) - Remove a member from the database. This is not guild specific although it can be if `guild` is specified
  * **Parameters**
    * **member** (`Union[discord.Member, int]`) The member to remove. Can be the member object or that members ID
    * **guild** (`Optional[discord.Guild]`) If this parameter is given, it will remove the record of the specified member only from the specified guild record. If `None`, it will remove all records no matter the guild
  * **Returns**
    * (`Optional[bool]`) Returns `True` if the member was successfully removed from the database. `False` if the member was not in the database so there was nothing to remove
  * **Raises**
      * `DatabaseFileNotFound` - The database file was not found
      * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
      * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
      * `DiscordLevelingSystemError` - Parameter `member` was not of type `discord.Member` or `int`
      * `NotConnected` - Attempted to use a method that requires a connection to a database file


* *await* **remove_xp**(`member, amount`) - Remove XP from a member. This also changes their level so it matches the associated XP
  * **Parameters**
      * **member** (`discord.Member`) The member to remove XP from
      * **amount** (`int`) Amount of XP to remove from the member
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - Parameter "amount" was less than or equal to zero. The minimum value is 1


* *await* **reset_everyone**(`guild, *, intentional = False`) - Sets EVERYONES XP, total XP, and level to zero in the database. Can specify which guild to reset
  * **Parameters**
      * **guild** (`Union[discord.Guild, None]`) The guild for which everyone will be reset. If this is set to `None`, everyone in the entire database will be reset
      * **intentional** (`bool`) A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `FailSafe` - "intentional" argument for this method was set to `False` in case you called this method by mistake


* *await* **reset_member**(`member`) - Sets the members XP, total XP, and level to zero
  * **Parameters**
    * **member** (`discord.Member`) The member to reset
  * **Raises**
    * `DatabaseFileNotFound` The database file was not found
    * `LeaderboardNotFound` Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` Leaderboard table was altered. Components changed or deleted
    * `NotConnected` Attempted to use a method that requires a connection to a database file


* *await* **set_level**(`member, level`) - Sets the level for the member. This also changes their total XP so it matches the associated level
  * **Parameters**
    * **member** (`discord.Member`) The member who's level will be set
    * **level** (`int`) Level to set. Must be from 0-100     
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - Parameter "level" was not from 0-100


* *await* **sql_query_get**(`sql, parameters = None, fetch = 'ALL'`) - Query and return something from the database using SQL. The following columns are apart of the "leaderboard" table: guild_id, member_id, member_name, member_level, member_xp, member_total_xp
  * **Parameters**
    * **sql** (`str`) SQL string used to query the database
    * **parameters** (`Optional[Tuple[Union[str ,int]]]`) The parameters used for the database query
    * **fetch** (`Union[str, int]`) The amount of rows you would like back from the query. Options: 'ALL', 'ONE', or an integer value that is greater than zero
  * **Returns**
    * (`Union[List[tuple], tuple]`)
      * Using `fetch='ALL'` returns `List[tuple]`
      * Using `fetch='ONE'` returns `tuple`
      * Using `fetch=4` returns `List[tuple]` with only four values
      * Can also return an empty list if the query was valid but got nothing from it
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `DiscordLevelingSystemError` - Argument "fetch" was the wrong type or used an invalid value
    * `aiosqlite.Error` - Base aiosqlite error. Multiple errors can arise from this if the SQL query was invalid


* *await* **switch_connection**(`path`) - Connect to a different leveling system database file
  * **Parameters**
    * **path** (`str`) The location of the database file
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found


* *static method* **transfer**(`old, new, guild_id`) - Transfer the database records from a database file created from v0.0.1 to a blank database file created using v0.0.2+. If you were already using a v0.0.2+ database file, there's no need to use this method
  * **Parameters**
    * **old** (`str`) The path of the v0.0.1 database file
    * **new** (`str`) The path of the v0.0.2+ database file
    * **guild_id** (`int`) ID of the guild that was originally used with this library
  * **Raises**
    - `ConnectionFailure` - The event loop is already running
    - `DatabaseFileNotFound` - "old" or "new" database file was not found
    - `DiscordLevelingSystemError` - One of the databases is missing the "leaderboard" table. A v0.0.2+ database file contains records, or there was an attempt to transfer records from a v0.0.2+ file to another v0.0.2+ file


* *static method* **version_info**() - A shortcut to the function `discordLevelingSystem.version_info()`


* *await* **wipe_database**(`guild = None, *, intentional = False`) - Delete EVERYTHING from the database. If `guild` is specified, only the information related to that guild will be deleted
  * **Parameters**
    * **guild** (`Optional[discord.Guild]`) The guild for which all information that is related to that guild will be deleted. If `None`, everything will be deleted
    * **intentional** (`bool`) A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone
  * **Raises**
    * `DatabaseFileNotFound` - The database file was not found
    * `LeaderboardNotFound` - Table "leaderboard" in the database file is missing
    * `ImproperLeaderboard` - Leaderboard table was altered. Components changed or deleted
    * `NotConnected` - Attempted to use a method that requires a connection to a database file
    * `FailSafe` - "intentional" argument for this method was set to `False` in case you called this method by mistake

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

## Inserting your own leveling system information
<details>
    <summary>Click to show details</summary>

Insert the records from your leveling system into this one. A lot of leveling system tutorials out there use json files to store information. Although it might work, it is insufficient because json files are not made to act as a database. Using a database file has many benefits over a json file. If you previously watched a tutorial for your leveling system and would like to import your records over to use with this library, you can do so with the below method.

* Associated static method
  * `await DiscordLevelingSystem.insert(bot: Union[Bot, AutoShardedBot], guild_id: int, users: Dict[int, int], using: str, overwrite=False, show_results=True)`

### Parameters
- `bot` (`Union[discord.ext.commands.Bot, discord.ext.commands.AutoShardedBot]`) Your bot instance variable

- `guild_id` (`int`) ID of the guild that you used your leveling system with

- `users` (`Dict[int, int]`) This is the information that will be added to the database. The keys are user ID's, and the values are the users total XP or level. Note: This library only uses levels 0-100 and XP 0-1899250. If any number in this dict are over the levels/XP threshold, it is implicitly set back to this libraries maximum value

- `using` (`str`) What structure your leveling system used. Options: "xp" or "levels". Some leveling systems give users only XP and they are ranked up based on that XP value. Others use a combination of levels and XP. If all the values in the `users` dict are based on XP, set this to "xp". If they are based on a users level, set this to "levels"

- `overwrite` (`bool`) If a user you've specified in the `users` dict already has a record in the database, overwrite their current record with the one your inserting

- `show_results` (`bool`) Print the results for how many of the `users` were successfully added to the database file. If any are unsuccessful, their ID along with the value you provided will also be shown

> NOTE: If the users you've provided in the `users` dict is not currently in the guild (`guild_id`), their information will not be inserted. If you'd like, you can manually add those records with method `DiscordLevelingSystem.add_record()`, but that is discouraged because it is better to discard information that is no longer in use (the user is no longer in the guild)

<div align="left"><sub>EXAMPLE</sub></div>

```py
# leveling_system.json
[
  {
      "5748392849348934" : {
          "xp" : 373,
          "level" : 4
      }
  },
  {
      "89283659820948923" : {
          "xp" : 23,
          "level" : 1
      }
  }
]


# bot.py
import json
from discord.ext import commands
from discordLevelingSystem import DiscordLevelingSystem

bot = commands.Bot(...)

lvl = DiscordLevelingSystem(...)
lvl.connect_to_database_file(...)

def json_to_dict() -> dict:
    with open('leveling_system.json') as fp:
        data = json.load(fp)
        formatted: Dict[int, int] = ... # format the data so all keys and values are associated with the user ID and level
        
        """
        In the end, the formatted dict should look like so:
        
        formatted = {
            5748392849348934 : 4,
            89283659820948923 : 1
        }
        """
        return formatted

@bot.command()
async def insert(ctx):
    await lvl.insert(ctx.bot, guild_id=12345678901234, users=json_to_dict(), using='levels')

bot.run(...)
```

</details>
