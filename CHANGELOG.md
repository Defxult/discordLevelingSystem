## v1.2.0 » Future Release
<!-- <details>
  <summary>Click to display changelog</summary> -->

#### Library Change
* The developer of discord.py has decided to revive the project. Since this library was originally dependent on discord.py, as of this version it no longer dependent on pycord, and will be using discord.py 2.0 and higher for the duration of this library.

#### New Features
* Added a shortcut method to function `version_info()`
  * `DiscordLevelingSystem.version_info()`

<!-- </details> -->

## v1.1.0 » Jan. 29, 2022
<details>
  <summary>Click to display changelog</summary>

#### Library Change
* With the discontinuation of discord.py, this library is now dependent on [pycord](https://github.com/Pycord-Development/pycord)
#### New Features
* Added `LevelUpAnnouncement.Member.display_avatar_url`. Used to access member avatars that are guild specific
* Added `LevelUpAnnouncement.Member.banner_url`. Used to access member banners
* Added the ability to get the total amount of XP needed for a level
  * `DiscordLevelingSystem.get_xp_for_level(level: int)`
* Added the ability to limit the amount of records returned from a member data query
  * `DiscordLevelingSystem.each_member_data(..., limit: Optional[int] = None)`
* Added the ability to get the next level for a member
  * `DiscordLevelingSystem.next_level(member: discord.Member)`
* Added the ability to get the `dict` that represents the leveling systems level/XP requirement process
  * `DiscordLevelingSystem.levels_and_xp()`
#### Miscellaneous
* Added `__repr__` to the `DiscordLevelingSystem.Bonus` class
* Added `__all__` for the library itself (`from discordLevelingSystem import *`)
* Added more `typing.Optional` for parameters. Implemented the use of `typing.ClassVar` and `collections.abc.Sequence`. A handful of parameters that specified a `List[x]` never really *needed* to be a list. All parameters that specified a `List[x]` has been changed to `Sequence[x]`, but parameters that still require a list are still type hinted as `List[x]`
</details>

## v1.0.2 » Sept. 4, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the event `on_dls_level_up`. This offers more capabilities compared to `LevelUpAnnouncement` ([docs](https://github.com/Defxult/discordLevelingSystem#events))
* Added the ability to connect to a different database file while the leveling system is active
  * `DiscordLevelingSystem.switch_connection(path: str)`
* Added property `DiscordLevelingSystem.database_file_path`. Returns the current path of the active database file
* Added the `MemberData` class to `__init__` for easier access to the class. Should only be used for type hinting
#### Bug Fixes
* Fixed an issue where properties `DiscordLevelingSystem.rate` & `DiscordLevelingSystem.per` wouldn't return their updated values if `DiscordLevelingSystem.change_cooldown()` was used
</details>


## v1.0.1 » Aug. 24, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the ability to insert your own leveling system data into the library. Typically used if you're currently using a json leveling system, but can be converted from any system as long as the necessary values are given (beta) ([docs](https://github.com/Defxult/discordLevelingSystem#inserting-your-own-leveling-system-information))
  * `DiscordLevelingSystem.insert(bot: Union[Bot, AutoShardedBot], guild_id: int, users: Dict[int, int], using: str, overwrite: bool=False, show_results: bool=True)`
* Added the ability manually add a record to the database
  * `DiscordLevelingSystem.add_record(guild_id: int, member_id: int, member_name: str, level: int)`
* Added method `MemberData.to_dict()`
* Added function `discordLevelingSystem.version_info()` . This will be the standard way for getting the information about what version of the library you are using

</details>

## v1.0.0 » Aug. 9, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added parameter `guild` for the below methods
  * This allows a more targeted check or removal for the specified member 
    * `DiscordLevelingSystem.is_in_database(member: Union[Member, int], guild: Guild=None)`
    * `DiscordLevelingSystem.remove_from_database(member: Union[Member, int], guild: Guild=None)`
  * Before, your only option was to delete the entire database file. You can now delete the guild records of your choice
    * `DiscordLevelingSystem.wipe_database(guild: Guild=None, *, intentional: bool=False)`
* Added the ability to get the awards that were set in the constructor as a whole or filtered by a specified guild
  * `DiscordLevelingSystem.get_awards(guild: Union[Guild, int]=None)`
* Added a few new attributes
  * `DiscordLevelingSystem.active` - Enable/disable the leveling system ([docs](https://github.com/Defxult/discordLevelingSystem#attributes))
  * `RoleAward.mention` - The discord role mention string

</details>



## v0.0.2 » Jun. 21, 2021
<details>
  <summary>Click to display changelog</summary>

#### New Features
* Added the ability for `LevelUpAnnouncement` messages to be embeds ([docs](https://github.com/Defxult/discordLevelingSystem#levelupannouncement))
* Added the ability to have multiple `LevelUpAnnouncement` messages ([docs](https://github.com/Defxult/discordLevelingSystem#levelupannouncement))
* Added the ability for multiple servers to have their own level up awards ([docs](https://github.com/Defxult/discordLevelingSystem#roleaward))
* Added the ability to set roles that give bonus XP ([docs](https://github.com/Defxult/discordLevelingSystem#handling-xp))
* Added the ability to set the name for a `RoleAward` ([docs](https://github.com/Defxult/discordLevelingSystem#roleaward))
* Added the ability to access `rate` and `per` (the values set in the `DiscordLevelingSystem` constructor) ([docs](https://github.com/Defxult/discordLevelingSystem#discordlevelingsystem))
  * `DiscordLevelingSystem.rate` (property)
  * `DiscordLevelingSystem.per` (property)
* Added the ability to manually set a members XP and level ([docs](https://github.com/Defxult/discordLevelingSystem#all-methods-for-discordlevelingsystem))
  * `DiscordLevelingSystem.add_xp(member: Member, amount: int)`
  * `DiscordLevelingSystem.remove_xp(member: Member, amount: int)`
  * `DiscordLevelingSystem.set_level(member: Member, level: int)`
* Added the ability to access more of the members information when a level up message is sent ([docs](https://github.com/Defxult/discordLevelingSystem#class-attributes))
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
* Added the ability to transfer your `v0.0.1` database file records to a `v0.0.2+` database file (see Bug Fixes)
  * `DiscordLevelingSystem.transfer(old: str, new: str, guild_id: int)`
* Improved `export_as_json` method. Format is now easier to read

#### Bug Fixes
* Fixed an issue where if your bot was in multiple servers and members were in 2 or more of those servers, the leaderboard would be updated regardless of being in the same server or a different one. A member could level up to "1" in a server and their next level would be "2" in another. The member's level and XP would remain the same in all the servers. With this update, member XP and level are now specific to each server and are no longer the same in all servers.
  * **IMPORTANT:** [Migrating from v0.0.1 to v0.0.2+](https://github.com/Defxult/discordLevelingSystem#migrating-from-v001-to-v002)
* Fixed an issue where if an `award_xp` amount value was a list and the first value was larger than the second, an error would occur that was not informative. An informative error is now raised.
* Fixed an issue where discord system messages would give XP to the member
* Fixed an issue where if a `level_up_channel_id` was set for a server and level up occurred in a different server, an error would occur (important: see Breaking Change for `level_up_channel_id`)
#### Breaking Change
* *removed* `LevelUpAnnouncement.AUTHOR_MENTION`
  * This has been replaced with `LevelUpAnnouncement.Member.mention`
* *removed* `LevelUpAnnouncement.XP`
  * This was removed because in a level up message the members XP was always reset to zero because of the level up, and accessing that attribute would always give a value of zero
* *removed* Exception `AwardedRoleNotFound` has been removed because it is no longer needed
* *removed* Exception `LevelUpChannelNotFound` has been removed because it is no longer needed
* *removed* `DiscordLevelingSystem.awards` attribute
  * The ability to set this attribute from an instance of `DiscordLevelingSystem` was removed because there is a necessary check that needs to take place to ensure the role award system can operate smoothly. You can still set the `awards` value via the `DiscordLevelingSystem` constructor
* *changed* `LevelUpAnnouncement` parameter `level_up_channel_id`. This was renamed and the type has been changed to support multiple servers having their own level up channel
  * Before: `level_up_channel_id` (`int`)
  * After: `level_up_channel_ids` (`List[int]`)
* *changed* Maximum value allowed in `award_xp`
  * Previously, the maximum value for the `amount` parameter in `award_xp` was 100. This has been reduced to a maximum of 25. Why? The goal of this library is to try and mimic the operations of the MEE6 leveling system, and awarding XP less than or equal to 25 has proved to be more of a stable way to earn XP, especially when it comes to bonus XP roles
* *changed* `DiscordLevelingSystem` parameter `awards` type
  * Before: `Union[List[RoleAward], None]`
  * After: `Union[Dict[int, List[RoleAward]], None]`
* *changed* Parameters for method `clean_database`
  * Before: `DiscordLevelingSystem.clean_database(all_members: List[Member])`
  * After: `DiscordLevelingSystem.clean_database(guild: Guild)`
* *changed* Parameters for method `reset_everyone`
  * Before: `DiscordLevelingSystem.reset_everyone(*, intentional: bool=False)`
  * After: `DiscordLevelingSystem.reset_everyone(guild: Union[Guild, None], *, intentional: bool=False)`
* *changed* Parameters for method `export_as_json`
  * Before: `DiscordLevelingSystem.export_as_json(path: str)`
  * After: `DiscordLevelingSystem.export_as_json(path: str, guild: Union[Guild, None])`
* *changed* Parameters for method `raw_database_contents`
  * Before: `DiscordLevelingSystem.raw_database_contents()`
  * After: `DiscordLevelingSystem.raw_database_contents(guild: Guild=None)`
* *changed* Parameters for method `get_record_count`
  * Before: `DiscordLevelingSystem.get_record_count()`
  * After: `DiscordLevelingSystem.get_record_count(guild: Guild=None)`

</details>



## v0.0.1 » Apr. 24, 2021
<details>
  <summary>Click to display changelog</summary>

* Initial release

</details>