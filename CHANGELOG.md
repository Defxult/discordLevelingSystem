## v0.0.2 » Jun. 21, 2021
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
* Fixed an issue where if a `level_up_channel_id` was set for a server and level up occured in a different server, an error would occur (important: see Breaking Change for `level_up_channel_id`)
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

## v0.0.1 » Apr. 24, 2021
* Initial release
