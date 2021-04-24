A library to implement a leveling system into a discord bot. One of the most popular discord bots out there is MEE6 and it's leveling system. This library provides ways to easily implement one for yourself. It uses SQLite (aiosqlite) to locally query things such as their XP, rank, and level. Various amounts of other methods and classes are also provided so you can access or remove contents from the database file.

Install the Github version of this library by doing:
```
pip install git+https://github.com/Defxult/discordLevelingSystem.git
```
You must have [Git](https://git-scm.com/) installed in order to do this

---
## Showcase
![showcase](https://cdn.discordapp.com/attachments/655186216060321816/835010159092039680/leveling_showcase.gif)

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
## `DiscordLevelingSystem`
`class DiscordLevelingSystem(rate=1, per=60.0, awards=None, **kwargs)`

The main class used for the leveling system. Setting the cooldown rate and roles are done here.
* `rate` (`int`)
  * The amount of messages each member can send before the cooldown triggers.
  * defaults to 1

* `per`( `float`)
  * The amount of seconds each member has to wait before gaining more XP, aka the cooldown.
  * defaults to 60.0

* `awards` (`List[RoleAward]`)
  * The role given to a member when they reach a `RoleAward` level requirement.
  * defaults to `None`

### `DiscordLevelingSystem` kwargs
* `no_xp_roles` (`List[int]`)
  * A list of role ID's. Any member with any of those roles will not gain XP when sending messages.
  * defaults to `None`

* `no_xp_channels` (`List[int]`)
  * A list of text channel ID's. Any member sending messages in any of those text channels will not gain XP.
  * defaults to `None`

* `announce_level_up` (`bool`)
  * If `True`, level up messages will be sent when a member levels up.
  * defaults to `True`

* `stack_awards` (`bool`)
  * If this is `True`, when the member levels up the assigned role award will be applied. If `False`, the previous role award will be removed and the level up assigned role will also be applied.
  * defaults to `True`

* `level_up_announcement` (`LevelUpAnnouncement`)
  * The message that is sent when someone levels up.
  * defaults to `LevelUpAnnouncement()`

### Attributes
* `awards`
* `no_xp_roles`
* `no_xp_channels`
* `announce_level_up`
* `stack_awards`
* `level_up_announcement`

> NOTE: All attributes can be set during initialization
---
## The Basics
* Associated method
  * `DiscordLevelingSystem.connect_to_database_file(path: str)`

Since the database file has already been created, all you need to do is connect to it. 
> NOTE: When connecting to the database file, the event loop must not be running
```py
from discord.ext import commands
from discordLevelingSystem import DiscordLevelingSystem

bot = commands.Bot(...)
lvl = DiscordLevelingSystem(rate=1, per=60.0)
lvl.connect_to_database_file(r'C:\Users\Defxult\Documents\DiscordLevelingSystem.db')

bot.run(...)
```
---

## `RoleAward` 
`class RoleAward(role_id: int, level_requirement: int)`

You can assign roles to the system so when someone levels up to a certain level, they are given that role. `RoleAward` is how that is accomplished.
* `role_id` (`int`)
  * ID of the role that is to be awarded.

* `level_requirement` (`int`)
  * What level is required for a member to be awarded the role.

When creating role awards, all role ID's and level requirements must be unique. Level requirements must also be in ascending order.
```py
from discordLevelingSystem import DiscordLevelingSystem, RoleAward

rookie = RoleAward(role_id=307260748776865793, level_requirement=10)
associate = RoleAward(role_id=704956494927626320, level_requirement=20)
legend = RoleAward(role_id=834845004480381000, level_requirement=30)

lvl = DiscordLevelingSystem(..., awards=[rookie, associate, legend])
```
---

## `LevelUpAnnouncement`
`class LevelUpAnnouncement(message=default_message, level_up_channel_id=None, allowed_mentions=default_mentions, tts=False, delete_after=None)`

Level up announcements are for when you want to implement your own level up messages. Level up messages supports the values of who just leveled up, their XP/total XP, level, and rank. It also uses some of discord py's kwargs from it's `Messageable.send` such as `allowed_mentions`, `tts`, and `delete_after` to give you more control over the sent message.

* `message` (`str`)
  * The message that is sent when someone levels up.
  * defaults to `"<mention>, you are now **level <level>!**"`

* `level_up_channel_id` (`int`)
  * The text channel ID where all level up messages will be sent. If `None`, the level up message will be sent in the channel where they sent the message.
  * defaults to `None`

* `allowed_mentions` (`discord.AllowedMentions`)
  * Used to determine who can be pinged in the level up message.
  * defaults to `discord.AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)`

* `tts` (`bool`)
  * When the level up message is sent, have discord read the level up message aloud.
  * defaults to `False`

* `delete_after` (`float`)
  * Delete the level up message after an x amount of seconds.
  *  defaults to `None`

### Class Attributes
* `LevelUpAnnouncement.AUTHOR_MENTION` The member that leveled up
* `LevelUpAnnouncement.XP` The members current XP amount
* `LevelUpAnnouncement.TOTAL_XP` The members current total XP amount
* `LevelUpAnnouncement.LEVEL` The members current level
* `LevelUpAnnouncement.RANK` The members current rank

Example:
```py
from discordLevelingSystem import DiscordLevelingSystem, LevelUpAnnouncement

announcement = LevelUpAnnouncement(f'{LevelUpAnnouncement.AUTHOR_MENTION} just leveled up to level {LevelUpAnnouncement.LEVEL} 😎')

lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)
```
---
## Giving XP
Method `award_xp` is how members gain XP. This method is placed inside the `on_message` event of your bot. Members will gain XP if they send a message and if they're *not* on cooldown. Spamming messages will not give them XP.
> NOTE: Members cannot gain XP in DM's
* Associated method
  * `await DiscordLevelingSystem.award_xp(*, amount=[15,25], message: Message, refresh_name=True)`


### Parameters for `award_xp`
* `amount` (`Union[int, List[int]]`)
  * The amount of XP to award to the member per message. Must be from 1-100. Can be a list with a minimum and maximum length of two. If `amount` is a list of two integers, it will randomly pick a number in between those numbers including the numbers provided.

* `message` (`discord.Message`)
  * A discord message object

* `refresh_name` (`bool`)
  * Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is suggested to leave this as `True` so the database can always have the most up-to-date record.
  * defaults to `True`

---
## `MemberData`
Accessing the raw information inside the database file can look a bit messy if you don't know exactly what you're looking at. To make things easier, this library comes with the `MemberData` class. A class which returns information about a specifc member in the database.

* Associated methods
  * `await DiscordLevelingSystem.get_data_for(member: Member) -> MemberData`
  * `await DiscordLevelingSystem.each_member_data(guild: Guild, sort_by=None) -> List[MemberData]`

### Attributes
* `id_number` (`int`)
  The members ID

* `name` (`str`)
  The members name

* `level` (`int`)
  The members level

* `xp` (`int`)
  The members xp

* `total_xp` (`int`)
  The members total xp

* `rank` (`int`)
  The members rank

* `mention` (`str`)
  The discord member mention string


---
## Full Example
With all classes and core methods introduced, here is a basic implementation of this library.
```py
from discord.ext import commands
from discordLevelingSystem import DiscordLevelingSystem, RoleAward, LevelUpAnnouncement

bot = commands.Bot(...)

rookie = RoleAward(role_id=307260748776865793, level_requirement=10)
associate = RoleAward(role_id=704956494927626320, level_requirement=20)
legend = RoleAward(role_id=834845004480381000, level_requirement=30)

announcement = LevelUpAnnouncement(f'{LevelUpAnnouncement.AUTHOR_MENTION} just leveled up to level {LevelUpAnnouncement.LEVEL} 😎')

# DiscordLevelingSystem.create_database_file(r'C:\Users\Defxult\Documents') database file already created
lvl = DiscordLevelingSystem(rate=1, per=60.0, awards=[rookie, associate, legend], level_up_announcement=announcement)
lvl.connect_to_database_file(r'C:\Users\Defxult\Documents\DiscordLevelingSystem.db')

@bot.event
async def on_message(message):
    await lvl.award_xp(amount=15, message=message)

bot.run(...)
```
---
## All Methods
* `DiscordLevelingSystem.create_database_file(path: str)`
  * *static method* Create the database file and implement the SQL data for the database
---
* `DiscordLevelingSystem.backup_database_file(path: str, with_timestamp=False)`
  * Create a copy of the database file to the specified path. If a copy of the backup file is already in the specified path it will be overwritten
---
* `DiscordLevelingSystem.connect_to_database_file(path: str)`
  * Connect to the existing database file in the specified path
---
* `await DiscordLevelingSystem.change_cooldown(rate: int, per: float)`
  * Update the cooldown rate
---
* `await DiscordLevelingSystem.refresh_names(guild: Guild) -> Optional[int]`
  * Update names inside the database. This does not add anything new. It simply verifies if the name in the database matches their current name, and if they don't match, update the database name
---
* `await DiscordLevelingSystem.wipe_database(*, intentional=False)`
  * Delete EVERYTHING from the database
---
* `await DiscordLevelingSystem.clean_database(all_members: List[Member]) -> Optional[int]`
  * Removes the data for members that are no longer in the guild, thus reducing the database file size. It is recommended to have this method in a background loop in order to keep the database file free of records that are no longer in use
---
* `await DiscordLevelingSystem.reset_member(member: Member)`
  * Sets the members XP, total XP, and level to zero
---
* `await DiscordLevelingSystem.reset_everyone(*, intentional=False)`
  * Sets EVERYONES XP, total XP, and level to zero in the database
---
* `await DiscordLevelingSystem.export_as_json(path: str)`
  * Export a json file that represents the database to the path specified
---
* `await DiscordLevelingSystem.raw_database_contents() -> List[tuple]`
  * Returns everything in the database
---
* `await DiscordLevelingSystem.remove_from_database(member: Union[Member, int]) -> Optional[bool]`
  * Remove a member from the database
---
* `await DiscordLevelingSystem.is_in_database(member: Union[Member, int]) -> bool`
  * A quick check to see if a member is in the database
---
* `await DiscordLevelingSystem.get_record_count() -> int`
  * Get the amount of members that are registered in the database
---
* `await DiscordLevelingSystem.next_level_up(member: Member) -> int`
  * Get the amount of XP needed for the specified member to level up
---
* `await DiscordLevelingSystem.get_xp_for(member: Member) -> int`
  * Get the XP for the specified member
---
* `await DiscordLevelingSystem.get_total_xp_for(member: Member) -> int`
  * Get the total XP for the specified member
---
* `await DiscordLevelingSystem.get_level_for(member: Member) -> int`
  * Get the level for the specified member
---
* `await DiscordLevelingSystem.get_data_for(member: Member) -> MemberData`
  * Get the `MemberData` object that represents the specified member
---
* `await DiscordLevelingSystem.each_member_data(guild: Guild, sort_by=None) -> List[MemberData]`
  * Return each member in the database as a `MemberData` object for easy access to their XP, level, etc.
---
* `await DiscordLevelingSystem.get_rank_for(member: Member) -> int`
  * Get the rank for the specified member
---
* `await DiscordLevelingSystem.sql_query_get(sql: str, parameters: Tuple[Union[str, int]]=None, fetch: Union[str, int]='ALL') -> Union[List[tuple], tuple]`
  * Query and return something from the database using SQL
---
* `await DiscordLevelingSystem.award_xp(*, amount: Union[int, List[int]]=[15, 25], message: Message, refresh_name: bool=True)`
  * Give XP to the member that sent a message