"""
MIT License

Copyright (c) 2021-present Defxult#8269

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import collections
import json
import os
import random
import shutil
from collections.abc import Sequence
from datetime import datetime
from inspect import cleandoc
from typing import Dict, List, Optional, Tuple, Union

import aiosqlite
from discord import Guild, Member, Message, MessageType, Role
from discord.ext.commands import AutoShardedBot, Bot, BucketType, CooldownMapping

from .announcement import LevelUpAnnouncement
from .decorators import db_file_exists, leaderboard_exists, verify_leaderboard_integrity
from .errors import *
from .levels_xp_needed import *
from .member_data import MemberData
from .role_awards import RoleAward


class DiscordLevelingSystem:
    """A local discord.py leveling system powered by SQLite

    Parameters
    ----------
    rate: :class:`int`
        The amount of messages each member can send before the cooldown triggers

    per: :class:`float`
        The amount of seconds each member has to wait before gaining more XP, aka the cooldown
    
    awards: Optional[Dict[:class:`int`, List[:class:`RoleAward`]]]
        The role given to a member when they reach a :class:`RoleAward` level requirement

    Kwargs
    ------
    no_xp_roles: Sequence[:class:`int`]
        A sequence of role ID's. Any member with any of those roles will not gain XP when sending messages (defaults to :class:`None`)
    
    no_xp_channels: Sequence[:class:`int`]
        A sequence of text channel ID's. Any member sending messages in any of those text channels will not gain XP (defaults to :class:`None`)
    
    announce_level_up: :class:`bool`
        If `True`, level up messages will be sent when a member levels up (defaults to `True`)

    stack_awards: :class:`bool`
        If this is `True`, when the member levels up the assigned role award will be applied. If `False`, the previous role award will be removed
        and the level up assigned role will also be applied (defaults to `True`)

    level_up_announcement: Union[:class:`LevelUpAnnouncement`, Sequence[:class:`LevelUpAnnouncement`]]
        The message that is sent when someone levels up. If this is a list of :class:`LevelUpAnnouncement`, one is selected at random (defaults to :class:`LevelUpAnnouncement()`)
    
    bot: Union[:class:`discord.ext.commands.AutoShardedBot`, :class:`discord.ext.commands.Bot`]
        Your bot instance variable. Used only if you'd like to use the `on_dls_level_up` event (defaults to :class:`None`)
    
    Attributes
    ----------
    - `no_xp_roles`
    - `no_xp_channels`
    - `announce_level_up`
    - `stack_awards`
    - `level_up_announcement`
    - `active`
    - `bot`
    - `rate` (property)
    - `per` (property)
    - `database_file_path` (property)
    """
    
    _QUERY_NEW_MEMBER = """
        INSERT INTO leaderboard
        VALUES (?, ?, ?, ?, ?, ?)
    """

    def __init__(self, rate: int=1, per: float=60.0, awards: Optional[Dict[int, List[RoleAward]]]=None, **kwargs):
        if rate <= 0 or per <= 0:   raise DiscordLevelingSystemError('Invalid rate or per. Values must be greater than zero')
        self.__rate = rate
        self.__per = per

        RoleAward._check(awards)
        self._awards = awards

        self.no_xp_roles: Optional[Sequence[int]] = kwargs.get('no_xp_roles')
        self.no_xp_channels: Optional[Sequence[int]] = kwargs.get('no_xp_channels')
        self.announce_level_up: bool = kwargs.get('announce_level_up', True)
        self.stack_awards: bool = kwargs.get('stack_awards', True)
        self.level_up_announcement: Union[LevelUpAnnouncement, Sequence[LevelUpAnnouncement]] = kwargs.get('level_up_announcement', LevelUpAnnouncement())

        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)
        self._connection: aiosqlite.Connection = None
        self._cursor: aiosqlite.Cursor = None
        self._loop = asyncio.get_event_loop()
        self._database_file_path: str = None

        # v0.0.2
        self._message_author: Member = None

        # v1.0.0
        self.active = True

        # v1.0.2
        self.bot: Union[AutoShardedBot, Bot] = kwargs.get('bot')
    
    @property
    def rate(self) -> int:
        """
        Returns
        -------
        :class:`int`: The amount of messages each member can send before the cooldown triggers

            .. added:: v0.0.2
        """
        return self.__rate
    
    @property
    def per(self) -> float:
        """
        Returns
        -------
        :class:`float`: The amount of seconds each member has to wait before gaining more XP, aka the cooldown
            
            .. added:: v0.0.2
        """
        return self.__per
    
    @property
    def database_file_path(self) -> str:
        """
        Returns
        -------
        :class:`str`: The path of the current database file. Could be :class:`None` if the database connection was never set

            .. added:: v1.0.2
        """
        return self._database_file_path

    class Bonus:
        """Set the roles that gives x amount of extra XP to the member. This is to be used with kwarg "bonus" in the :meth:`award_xp` method

        Note
        ----
        Having :param:`multiply` as `True` and :param:`bonus_amount` be greater than 3 is not allowed. If :param:`multiply` is `True`, :param:`bonus_amount` needs to be less than or equal to 3.
        It should also be noted that if :param:`multiply` is `False`, it doesn't matter what :param:`bonus_amount` you use but if the total amount (awarded XP + the bonus) is greater than 75, the
        value is implicitly changed back to 75. The maximum amount of XP a member can earn through sending messages is 75.

        Parameters
        ----------
        role_ids: Sequence[:class:`int`]
            The roles a member must have to be able to get bonus XP. They only need to have one of these roles to get the bonus

        bonus_amount: :class:`int`
            Amount of extra XP to be awarded

        multiply: :class:`bool`
            If set to `True`, this will operate on a x2, x3 basis. Meaning if you have the awarded XP set to 10 and you want the bonus XP role to be awarded 20, it must be set to 2,
            not 10. If `False`, it operates purely on the given value. Meaning if you have the awarded XP set to 10 and you want the bonus XP role to be awarded 20, it must be set to 10
        
        Attributes
        ----------
        - `role_ids`
        - `bonus_amount`
        - `multiply`

        Example
        -------
        ```
        lvl = DiscordLevelingSystem(...)

        nitro_booster = 851379776111116329
        associate_role = 851400453904400385

        @bot.event
        async def on_message(message):
            await lvl.award_xp(amount=[15, 25], message=message, bonus=DiscordLevelingSystem.Bonus([nitro_booster, associate_role], 20, multiply=False))
        ```

            .. added:: v0.0.2
        """
        __slots__ = ('role_ids', 'bonus_amount', 'multiply')

        def __init__(self, role_ids: Sequence[int], bonus_amount: int, multiply: bool):
            if len(role_ids) >= 1:
                self.role_ids = role_ids
                self.bonus_amount = bonus_amount
                self.multiply = multiply

                if multiply and bonus_amount > 3:
                    raise DiscordLevelingSystemError('Parameter "bonus_amount" cannot be greater than 3 when parameter "multiply" is True')
                
            else:
                raise DiscordLevelingSystemError('When setting the role_ids for bonus XP, the role ID sequence cannot be empty')
        
    @staticmethod
    def create_database_file(path: str):
        """|static method| Create the database file and implement the SQL data for the database
        
        Parameters
        ----------
        path: :class:`str`
            The location to create the database file
        
        Raises
        ------
        - `ConnectionFailure`: Attempted to create the database file when the event loop is already running
        - `DiscordLevelingSystemError`: The path does not exist or the path points to a file instead of a directory
        
            .. changes::
                v0.0.2
                    Added guild_id for database file creation
        """
        if os.path.exists(path) and os.path.isdir(path):
            database_file = os.path.join(path, 'DiscordLevelingSystem.db')
            with open(database_file, mode='w'):
                try:
                    loop = asyncio.get_event_loop()

                    # create a temporary connection and build the leaderboard table
                    connection: aiosqlite.Connection = loop.run_until_complete(aiosqlite.connect(database_file))
                    query = """
                        CREATE TABLE leaderboard (
                            guild_id INT NOT NULL,
                            member_id INT NOT NULL,
                            member_name TEXT NOT NULL,
                            member_level INT NOT NULL,
                            member_xp INT NOT NULL,
                            member_total_xp INT NOT NULL
                        );
                    """
                    loop.run_until_complete(connection.execute(query))
                    loop.run_until_complete(connection.commit())
                except RuntimeError:
                    raise ConnectionFailure
        else:
            raise DiscordLevelingSystemError(f'The path {path!r} does not exist or that path directs to a file when it is suppose to path to a directory')
    
    def backup_database_file(self, path: str, with_timestamp: bool=False):
        """Create a copy of the database file to the specified path. If a copy of the backup file is already in the specified path it will be overwritten
        
        Parameters
        ----------
        path: :class:`str`
            The path to copy the database file to

        with_timestamp: :class:`bool`
            (optional) Creates a unique file name that has the date and time of when the backup file was created. This is useful when you want multiple backup files (defaults to `False`)
        
        Raises
        ------
        - `DiscordLevelingSystemError`: Path doesn't exist or points to another file
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        # the decorator @db_file_exists should be used here because if :attr:`_database_file_path` is :class:`None`, it will raise TypeError, which is exactly what Exception `NotConnected` is made for
        # and is handled inside that decorator. But to repurpose the entire function to support functions that are not coroutines is unnecessary. A simple check is all thats needed for this
        if not self._database_file_path:
            raise NotConnected
            
        if os.path.exists(path) and os.path.isdir(path):
            if not with_timestamp:
                database_file = os.path.join(path, 'DiscordLevelingSystem__backup.db')
                shutil.copyfile(src=self._database_file_path, dst=database_file)
            else:
                dt = datetime.now()
                dt_str = dt.strftime('%Y_%b_%d__%I_%M_%S_%p__%f')
                database_file = os.path.join(path, 'DiscordLevelingSystem__backup(%s).db' % dt_str)
                shutil.copyfile(src=self._database_file_path, dst=database_file)
        else:
            raise DiscordLevelingSystemError(f'When attempting to backup the database file, the path "{path}" does not exist or points to another file')
    
    def connect_to_database_file(self, path: str):
        """Connect to the existing database file in the specified path
        
        Parameters
        ----------
        path: :class:`str`
            The location of the database file
        
        Raises
        ------
        - `ConnectionFailure`: Attempted to connect to the database file when the event loop is already running
        - `DatabaseFileNotFound`: The database file was not found
        """
        if all([os.path.exists(path), os.path.isfile(path), path.endswith('.db')]):
            try:
                self._connection = self._loop.run_until_complete(aiosqlite.connect(path))
                self._cursor = self._loop.run_until_complete(self._connection.cursor())
                self._database_file_path = path
            except RuntimeError:
                raise ConnectionFailure
        else:
            raise DatabaseFileNotFound(f'The database file in path {path!r} was not found')

    async def switch_connection(self, path: str):
        """|coro| Connect to a different leveling system database file

        Parameters
        ----------
        path: :class:`str`
            The location of the database file

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found

            .. added:: v1.0.2
        """
        if all([os.path.exists(path), os.path.isfile(path), path.endswith('.db')]):
            if self._database_file_path == path:
                return
            
            # close the current connection before making a new one
            await self._connection.close()

            self._connection = await aiosqlite.connect(path)
            self._cursor = await self._connection.cursor()
            self._database_file_path = path
        else:
            raise DatabaseFileNotFound(f'The database file in path {path!r} was not found')
    
    def _determine_no_xp(self, message: Message) -> bool:
        """Check if the channel the member is sending messages in is a no XP channel. This also checks if any of the roles they have is a no XP role
        
            .. changes::
                v0.0.2
                    Complete overhaul to support multi-guild leveling 
        """
        has_no_xp_role = False
        in_no_xp_channel = False
        
        if self.no_xp_channels:
            if message.channel.id in self.no_xp_channels:
                in_no_xp_channel = True
        
        # if :var:`in_no_xp_channel` is already `True`, there's no need to execute the no xp role check
        if in_no_xp_channel:
            return True

        if self.no_xp_roles:
            all_member_role_ids = [role.id for role in message.author.roles]
            for no_xp_role_id in self.no_xp_roles:
                if no_xp_role_id in all_member_role_ids:
                    has_no_xp_role = True
                    break

        return any([has_no_xp_role, in_no_xp_channel])        
    
    async def _update_record(self, member: Union[Member, int], level: int, xp: int, total_xp: int, guild_id: int, name: str=None, **kwargs):
        maybe_new_record = kwargs.get('maybe_new_record', False)
        if maybe_new_record and not name:
            raise Exception('kwarg "name" needs to be set when adding a new record')
        
        # :meth:`DiscordLevelingSystem.is_in_database` parameter "guild" expects a :class:`discord.Guild` object. We don't necessarily *need* an actual :class:`discord.Guild`
        # object because that method really only needs the ID to operate on the correct guild. Since this method has no :class:`discord.Guild` object, just make a false guild
        # object so :meth:`DiscordLevelingSystem.is_in_database` will work as intended
        FakeGuild = collections.namedtuple('FakeGuild', 'id')
        if await self.is_in_database(member, guild=FakeGuild(id=guild_id)):
            await self._cursor.execute('UPDATE leaderboard SET member_level = ?, member_xp = ?, member_total_xp = ? WHERE member_id = ? AND guild_id = ?', (level, xp, total_xp, member.id if isinstance(member, Member) else member, guild_id))
        else:
            await self._cursor.execute(DiscordLevelingSystem._QUERY_NEW_MEMBER, (guild_id, member.id if isinstance(member, Member) else member, name, level, xp, total_xp))
        await self._connection.commit()
    
    @staticmethod
    def _get_transfer(path: str, loop: asyncio.AbstractEventLoop):
        """|static method| Connect to the target database file in the specified path and return a named tuple of the connection and cursor
        
            .. added:: v0.0.2
        """
        if all([os.path.exists(path), os.path.isfile(path), path.endswith('.db')]):
            try:
                connection = loop.run_until_complete(aiosqlite.connect(path))
                cursor = loop.run_until_complete(connection.cursor())
                Transfer = collections.namedtuple('Transfer', ['connection', 'cursor'])
                return Transfer(connection=connection, cursor=cursor)
            except RuntimeError:
                raise ConnectionFailure
        else:
            raise DatabaseFileNotFound(f'The database file in path {path!r} was not found')
    
    @staticmethod
    async def _execute_transer(db_from: 'Transfer', db_to: 'Transfer', guild_id: int): # type: ignore
        """|coro static method| Copy the contents from the old database file (v0.0.1), to the new database file (v0.0.2+)
        
            .. added:: v0.0.2
        """
        try:
            from_result = await db_from.connection.execute_fetchall('SELECT * FROM leaderboard')
        except aiosqlite.OperationalError:
            raise DiscordLevelingSystemError('One of the databases is missing the "leaderboard" table when attempting to transfer')
        else:
            OLD_PRAGMA_LAYOUT = [
                (0, 'member_id', 'INT', 0, None, 1),
                (1, 'member_name', 'TEXT', 1, None, 0),
                (2, 'member_level', 'INT', 1, None, 0),
                (3, 'member_xp', 'INT', 1, None, 0),
                (4, 'member_total_xp', 'INT', 1, None, 0)
            ]
            NEW_PRAGMA_LAYOUT = [
                (0, 'guild_id', 'INT', 1, None, 0),
                (1, 'member_id', 'INT', 1, None, 0),
                (2, 'member_name', 'TEXT', 1, None, 0),
                (3, 'member_level', 'INT', 1, None, 0),
                (4, 'member_xp', 'INT', 1, None, 0),
                (5, 'member_total_xp', 'INT', 1, None, 0)
            ]
            old_pragma_check = await db_from.connection.execute_fetchall('PRAGMA table_info(leaderboard)')
            new_pragma_check = await db_to.connection.execute_fetchall('PRAGMA table_info(leaderboard)')
            if all([old_pragma_check == OLD_PRAGMA_LAYOUT, new_pragma_check == NEW_PRAGMA_LAYOUT]):
                # ensure the database file that the data will be transferred to is blank, if so, copy the contents to the new database file
                await db_to.cursor.execute('SELECT COUNT(*) FROM leaderboard')
                count_result = await db_to.cursor.fetchone()
                if count_result[0] == 0:
                    to_execute = []
                    for data in from_result:
                        to_execute.append((guild_id, data[0], data[1], data[2], data[3], data[4]))
                    else:
                        await db_to.cursor.executemany(DiscordLevelingSystem._QUERY_NEW_MEMBER, to_execute)
                        await db_to.connection.commit()
                        print('Transfer complete')
                else:
                    raise DiscordLevelingSystemError('When transfering the data to the new database file (created file using v0.0.2+), that database file must contain no records')
            else:
                raise DiscordLevelingSystemError('The "transfer" method is only to be used with transfering the data from the database file from version 0.0.1. If you were already using a database file from version 0.0.2+, there is no need to use this method')
    
    @staticmethod
    def transfer(old: str, new: str, guild_id: int):
        """|static method| Transfer the database records from a database file created from v0.0.1 to a blank database file created using v0.0.2+. If you were already using a v0.0.2+
        database file, there's no need to use this method

        See the following link about transfers: https://github.com/Defxult/discordLevelingSystem#migrating-from-v001-to-v002
        
        Parameters
        ----------
        old: :class:`str`
            The path of the v0.0.1 database file
        
        new: :class:`str`
            The path of the v0.0.2+ database file
        
        guild_id: :class:`int`
            ID of the guild that was originally used with this library
        
        Raises
        ------
        - `ConnectionFailure`: The event loop is already running
        - `DatabaseFileNotFound`: "old" or "new" database file was not found
        - `DiscordLevelingSystemError`: One of the databases is missing the "leaderboard" table. A v0.0.2+ database file contains records, or there was an attempt to transfer records from a v0.0.2+ file to another v0.0.2+ file
        
            .. added:: v0.0.2
        """
        loop = asyncio.get_event_loop()
        transfer_from = DiscordLevelingSystem._get_transfer(old, loop)
        transfer_to = DiscordLevelingSystem._get_transfer(new, loop)
        loop.run_until_complete(DiscordLevelingSystem._execute_transer(transfer_from, transfer_to, guild_id))
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def add_record(self, guild_id: int, member_id: int, member_name: str, level: int):
        """|coro| Manually add a record to the database. If the record already exists (the :param:`guild_id` and :param:`member_id` was found), only the level will be updated. If there were no records that matched
        those values, all provided information will be added

        Parameters
        ----------
        guild_id: :class:`int`
            The guild ID to register
        
        member_id: :class:`int`
            The member ID to register
        
        member_name: :class:`str`
            The member name to register
        
        level: :class:`int`
            The member level to register. Must be from 0-100
        
        Raises
        ------
        - `DiscordLevelingSystemError`: The value given from a parameter was not of the correct type or "level" was not 0-100

            .. added:: v1.0.1
        """
        if all([isinstance(guild_id, int), isinstance(member_id, int), isinstance(level, int)]):
            if not (0 <= level <= 100):
                raise DiscordLevelingSystemError('Parameter "level" must be from 0-100')
            await self._update_record(member=member_id, level=level, xp=0, total_xp=LEVELS_AND_XP[str(level)], guild_id=guild_id, name=str(member_name), maybe_new_record=True)
        else:
            raise DiscordLevelingSystemError('All parameters that expect an int were not of type int')

    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def insert(self, bot: Union[Bot, AutoShardedBot], guild_id: int, users: Dict[int, int], using: str, overwrite: bool=False, show_results: bool=True):
        """|coro| Insert the records from your own leveling system into the library. A lot of leveling system tutorials out there use json files to store information. Although it might work, it is
        insufficient because json files are not made to act as a database. Using a database file has many benefits over a json file
        
        If you already have records in the database file and you want to insert your records on top of the records that already exist, it is suggested to backup that
        file using :meth:`DiscordLevelingSystem.backup_database_file()` first. If you don't have any records in your DiscordLevelingSystem database file, then there's no need to create a backup 

        Parameters
        ----------
        bot: Union[:class:`discord.ext.commands.Bot`, :class:`discord.ext.commands.AutoShardedBot`]
            Your bot instance variable
        
        guild_id: :class:`int`
            ID of the guild that you used your leveling system with
        
        users: Dict[:class:`int`, :class:`int`]
            This is the information that will be added to the database. The keys are user ID's, and the values are the users total XP or level.
            Note: This library only uses levels 0-100 and XP 0-1899250. If any number in this dict are over the levels/XP threshold, it is implicitly set back to this libraries maximum value

        using: :class:`str`
            What structure your leveling system used. Options: "xp" or "levels". Some leveling systems give users only XP and they are ranked up based on that XP value. Others use a combination of levels and XP. If all the values
            in the :param:`users` dict are based on XP, set this to "xp". If they are based on a users level, set this to "levels"
        
        overwrite: :class:`bool`
            (optional) If a user you've specified in the :param:`users` dict already has a record in the database, overwrite their current record with the one your inserting (defaults to `False`)
        
        show_results: :class:`bool`
            (optional) Print the results for how many of the :param:`users` were successfully added to the database file. If any are unsuccessful, their ID along with the value you provided will also be shown (defaults to `True`)
        
        Raises
        ------
        - `DiscordLevelingSystemError`: The value given from a parameter was not of the correct type. The :param:`users` dict was empty. Or your bot is not in the guild associated with :param:`guild_id`
            
            .. added:: v1.0.1
        """
        # Perform the necessary checks to ensure the proper values will be added to the database
        if not isinstance(guild_id, int):
            raise DiscordLevelingSystemError(f'Parameter "guild_id" expected int, got {guild_id.__class__.__name__}')
        if not users:
            raise DiscordLevelingSystemError('The "users" dict cannot be empty')
        for k, v in users.items():
            if not isinstance(k, int) or not isinstance(v, int):
                raise DiscordLevelingSystemError('All keys and values in the "users" dict must be of type int')
        
        guild = bot.get_guild(guild_id)
        if guild:
            using = using.lower()
            successfully_added: List[Member] = []
            skipped_users = []
            registered_users = []
            SkippedUser = collections.namedtuple('SkippedUser', ['id', 'value'])
            RegisteredUser = collections.namedtuple('RegisteredUser', ['id', 'name', 'value'])
            for user_id, user_level_or_xp in users.items():
                member = guild.get_member(user_id)
                if member:
                    if not overwrite and await self.is_in_database(user_id, guild):
                        registered_users.append(str(RegisteredUser(id=user_id, name=str(member), value=user_level_or_xp)))
                        continue
                    else:
                        if using == 'levels':
                            level = user_level_or_xp
                            if level < 0: level = 0
                            elif level > MAX_LEVEL: level = MAX_LEVEL
                            await self.set_level(member, level)
                            successfully_added.append(member)
                        
                        elif using == 'xp':
                            xp = user_level_or_xp
                            if xp < 0: xp = 0
                            elif xp > LEVELS_AND_XP[str(MAX_LEVEL)]: xp = LEVELS_AND_XP[str(MAX_LEVEL)]
                            await self.set_level(member, _find_level(xp))
                            successfully_added.append(member)
                        
                        else:
                            raise DiscordLevelingSystemError(f'Parameter "using" expected "levels" or "xp", got {using!r}')
                else:
                    skipped_users.append(str(SkippedUser(id=user_id, value=user_level_or_xp)))
            else:
                if show_results:
                    stats = cleandoc(f"""
                        ----------------------------------------
                        Discord Leveling System - Insert Results
                        ----------------------------------------
                        {len(successfully_added)} out of {len(users)} users were successfully added to the database file
                    """)
                    if successfully_added:
                        data: List[MemberData] = [str(await self.get_data_for(stored_member)) for stored_member in successfully_added]
                        joined_data = '\n'.join(data)
                        stats += f'\n\nThe below {len(successfully_added)} user(s) are now apart of the Discord Leveling System and are represented as a MemberData object\n{joined_data}'
                    
                    if skipped_users:
                        joined_skipped = '\n'.join(skipped_users)
                        stats += f'\n\nThe below {len(skipped_users)} user(s) were skipped because they are not currently in guild {guild_id}\n{joined_skipped}'
                    
                    if registered_users:
                        joined_registered = '\n'.join(registered_users)
                        stats += f'\n\nThe below {len(registered_users)} user(s) were skipped because they already have a record in the database and the "overwrite" kwarg was set to False\n{joined_registered}'
                    
                    print(stats)
        else:
            raise DiscordLevelingSystemError(f'Your bot is not in guild {guild_id}')
    
    def get_awards(self, guild: Optional[Union[Guild, int]]=None) -> Union[Dict[int, List[RoleAward]], List[RoleAward]]:
        """Get all :class:`RoleAward`'s or only the :class:`RoleAward`'s assigned to the specified guild

        Parameters
        ----------
        guild: Optional[Union[:class:`discord.Guild`, :class:`int`]]
            A guild object or a guild ID
        
        Returns
        -------
        Union[Dict[:class:`int`, List[:class:`RoleAward`]], List[:class:`RoleAward`]]: If :param:`guild` is :class:`None`, this returns the awards :class:`dict` that was set in constructor. If :param:`guild`
        is specified, it returns a List[:class:`RoleAward`] that matches the specified guild ID. Can also return :class:`None` if awards were never set or if the awards for the specified guild was not found
        
            .. added:: v1.0.0
        """
        if self._awards:
            if guild:
                try:
                    guild_id = guild.id if isinstance(guild, Guild) else guild
                    return self._awards[guild_id].copy()
                except KeyError:
                    return None
            else:
                return self._awards.copy()
        else:
            return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def add_xp(self, member: Member, amount: int):
        """|coro| Give XP to a member. This also changes their level so it matches the associated XP

        Parameters
        ----------
        member: :class:`discord.Member`
            The member to give XP to
        
        amount: :class:`int`
            Amount of XP to give to the member

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: Parameter "amount" was less than or equal to zero. The minimum value is 1 
        
            .. added:: v0.0.2
        """
        if amount <= 0:
            raise DiscordLevelingSystemError('Parameter "amount" was less than or equal to zero. The minimum value is 1')
        
        md = await self.get_data_for(member)
        if md:
            if md.total_xp >= MAX_XP:
                return
            else:
                new_total_xp = md.total_xp + amount
                new_total_xp = new_total_xp if new_total_xp <= MAX_XP else MAX_XP
                maybe_new_level = _find_level(new_total_xp)
                await self._update_record(member=member, level=maybe_new_level, xp=md.xp, total_xp=new_total_xp, guild_id=member.guild.id, name=str(member), maybe_new_record=True)
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def remove_xp(self, member: Member, amount: int):
        """|coro| Remove XP from a member. This also changes their level so it matches the associated XP

        Parameters
        ----------
        member: :class:`discord.Member`
            The member to remove XP from
        
        amount: :class:`int`
            Amount of XP to remove from the member

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: Parameter "amount" was less than or equal to zero. The minimum value is 1 
        
            .. added:: v0.0.2
        """
        if amount <= 0:
            raise DiscordLevelingSystemError('Parameter "amount" was less than or equal to zero. The minimum value is 1')
        
        md = await self.get_data_for(member)
        if md:
            if md.total_xp == 0:
                return
            else:
                new_total_xp = md.total_xp - amount
                new_total_xp = new_total_xp if new_total_xp >= 1 else 0
                maybe_new_level = _find_level(new_total_xp)
                await self._update_record(member=member, level=maybe_new_level, xp=md.xp, total_xp=new_total_xp, guild_id=member.guild.id)
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def set_level(self, member: Member, level: int):
        """|coro| Sets the level for the member. This also changes their total XP so it matches the associated level
        
        Parameters
        ----------
        member: :class:`discord.Member`
            The member who's level will be set
        
        level: :class:`int`
            Level to set. Must be from 0-100
                
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: Parameter "level" was not from 0-100
        
            .. added:: v0.0.2
        """
        if 0 <= level <= 100:
            await self._update_record(member=member, level=level, xp=0, total_xp=LEVELS_AND_XP[str(level)], guild_id=member.guild.id, name=str(member), maybe_new_record=True)
        else:
            raise DiscordLevelingSystemError('Parameter "level" must be from 0-100')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def change_cooldown(self, rate: int, per: float):
        """|coro| Update the cooldown rate
        
        Parameters
        ----------
        rate: :class:`int`
            The amount of messages each member can send before the cooldown triggers

        per: :class:`float`
            The amount of seconds each member has to wait before gaining more XP, aka the cooldown

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: The rate or per value was not greater than zero
        """
        if rate <= 0 or per <= 0:   raise DiscordLevelingSystemError('Invalid rate or per. Values must be greater than zero')
        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)
        self.__rate = rate
        self.__per = per

    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def refresh_names(self, guild: Guild) -> Optional[int]:
        """|coro| Update names inside the database. This does not add anything new. It simply verifies if the name in the database matches their current name, and if they don't match, update
        the database name
        
        Parameters
        ----------
        guild: :class:`discord.Guild`
            A guild object
        
        Returns
        -------
        Optional[:class:`int`]:
            The amount of records in the database that were updated

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        async with self._connection.execute('SELECT member_id, member_name FROM leaderboard WHERE guild_id = ?', (guild.id,)) as cursor:
            result = await cursor.fetchall()
            names_updated = 0
            if result:
                database_ids = [db[0] for db in result]
                database_names = [db[1] for db in result]
                to_execute = []
                for db_id, db_name in zip(database_ids, database_names):
                    member = guild.get_member(db_id)
                    if member:
                        if str(member) != db_name:
                            to_execute.append((str(member), db_id, guild.id))
                            names_updated += 1
                else: 
                    await cursor.executemany('UPDATE leaderboard SET member_name = ? WHERE member_id = ? AND guild_id = ?', to_execute)
                    await self._connection.commit()

            return names_updated
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def wipe_database(self, guild: Optional[Guild]=None, *, intentional: bool=False):
        """|coro| Delete EVERYTHING from the database. If :param:`guild` is specified, only the information related to that guild will be deleted

        Parameters
        ----------
        guild: Optional[:class:`discord.Guild`]
            The guild for which all information that is related to that guild will be deleted. If :class:`None`, everything will be deleted

        intentional: :class:`bool`
            A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `FailSafe`: "intentional" argument for this method was set to `False` in case you called this method by mistake
        
            .. changes::
                v1.0.0
                    Added :param:`guild`
        """
        if intentional:
            if guild:   await self._cursor.execute('DELETE FROM leaderboard WHERE guild_id = ?', (guild.id,))
            else:       await self._cursor.execute('DELETE FROM leaderboard')
            await self._connection.commit()
        else:
            raise FailSafe
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def clean_database(self, guild: Guild) -> Optional[int]:
        """|coro| Removes the data for members that are no longer in the guild, thus reducing the database file size. It is recommended to have this method in a background loop
        in order to keep the database file free of records that are no longer in use

        Parameters
        ----------
        guild: :class:`discord.Guild`
            The guild records to clean
        
        Returns
        -------
        Optional[:class:`int`]:
            The amount of records that were removed from the database
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        
            .. changes::
                v0.0.2
                    Replaced :param:`all_members` with :param:`guild`
        """
        result = await self._connection.execute_fetchall('SELECT member_id FROM leaderboard WHERE guild_id = ?', (guild.id,))
        all_ids = [i[0] for i in result]
        to_execute = []
        records_removed = 0

        for id_ in all_ids:
            if guild.get_member(id_):
                continue
            else:
                to_execute.append((id_, guild.id))
                records_removed += 1
        else:
            if records_removed:
                await self._cursor.executemany('DELETE FROM leaderboard WHERE member_id = ? AND guild_id = ?', to_execute)
                await self._connection.commit()
            return records_removed
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def reset_member(self, member: Member):
        """|coro| Sets the members XP, total XP, and level to zero
        
        Parameters
        ----------
        member: :class:`discord.Member`
            The member to reset
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        await self._cursor.execute('UPDATE leaderboard SET member_level = 0, member_xp = 0, member_total_xp = 0 WHERE member_id = ? AND guild_id = ?', (member.id, member.guild.id))
        await self._connection.commit()
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def reset_everyone(self, guild: Union[Guild, None], *, intentional: bool=False):
        """|coro| Sets EVERYONES XP, total XP, and level to zero in the database. Can specify which guild to reset

        Parameters
        ----------
        guild: Union[:class:`discord.Guild`, :class:`None`]
            The guild for which everyone will be reset. If this is set to :class:`None`, everyone in the entire database will be reset
        
        intentional: :class:`bool`
            A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `FailSafe`: "intentional" argument for this method was set to `False` in case you called this method by mistake
        
            .. changes::
                v0.0.2
                    Added :param:`guild`
        """
        if intentional:
            if guild: await self._cursor.execute('UPDATE leaderboard SET member_level = 0, member_xp = 0, member_total_xp = 0 WHERE guild_id = ?', (guild.id,))
            else:     await self._cursor.execute('UPDATE leaderboard SET member_level = 0, member_xp = 0, member_total_xp = 0')
            await self._connection.commit()
        else:
            raise FailSafe
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def export_as_json(self, path: str, guild: Union[Guild, None]):
        """|coro| Export a json file that represents the database to the path specified
        
        Parameters
        ----------
        path: :class:`str`
            Path to copy the json file to
        
        guild: :class:`discord.Guild`
            The guild for which the data should be extracted from. If :class:`None`, all guild information will be extracted from the database
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: The path does not exist or does not point to a directory
        
            .. changes::
                v0.0.2
                    Added :param:`guild`. Now supports a specific guild to export
                    Improved overall json format (easier to read)
        """
        if os.path.exists(path) and os.path.isdir(path):
            path = os.path.join(path, 'discord_leveling_system.json')
            container = []
            if guild:
                data = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ?', (guild.id,))
                levels = {}
                for m_id, m_name, m_lvl, m_xp, m_total_xp in data:
                    levels = {
                        'id' : m_id,
                        'name' : m_name,
                        'level' : m_lvl,
                        'xp' : m_xp,
                        'total_xp' : m_total_xp
                    }
                    container.append(levels.copy())
                else:
                    with open(path, mode='w') as fp:
                        json.dump(container, fp, indent=4)
            
            else:
                data = await self._connection.execute_fetchall('SELECT * FROM leaderboard')
                for info in data:
                    guild_id = info[0]
                    member_id = info[1]
                    member_name = info[2]
                    member_level = info[3]
                    member_xp = info[4]
                    member_total_xp = info[5]
                    levels = {
                        'guild_id' : guild_id,
                        'member_id' : member_id,
                        'name' : member_name,
                        'level' : member_level,
                        'xp' : member_xp,
                        'total_xp' : member_total_xp
                    }
                    container.append(levels.copy())
                else:
                    with open(path, mode='w') as fp:
                        json.dump(container, fp, indent=4)
        else:
            raise DiscordLevelingSystemError(f'The path {path!r} does not exist or does not point to a directory')

    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def raw_database_contents(self, guild: Optional[Guild]=None) -> List[tuple]:
        """|coro| Returns everything in the database. Can specify which guild information will be extracted

        Parameters
        ----------
        guild: Optional[:class:`discord.Guild`]
            The guild to extract the raw database contents from. If :class:`None`, information about all guilds will be extracted
        
        Returns
        -------
        List[:class:`tuple`]:
            The tuples inside the list represents each row of the database:
        
        - Index 0 is the guild ID
        - Index 1 is their ID
        - Index 2 is their name
        - Index 3 is their level
        - Index 4 is their XP
        - Index 5 is their total xp
        
        Can be an empty list if nothing is in the database
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        
            .. changes::
                v0.0.2
                    Added :param:`guild`
        """
        if guild:   return await self._connection.execute_fetchall('SELECT * FROM leaderboard WHERE guild_id = ?', (guild.id,))
        else:       return await self._connection.execute_fetchall('SELECT * FROM leaderboard')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def remove_from_database(self, member: Union[Member, int], guild: Optional[Guild]=None) -> Optional[bool]:
        """|coro| Remove a member from the database. This is not guild specific although it can be if :param:`guild` is specified

        Parameters
        ----------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member to remove. Can be the member object or that members ID

        guild: Optional[:class:`discord.Guild`]
            If this parameter is given, it will remove the record of the specified member only from the specified guild record. If :class:`None`, it will remove
            all records no matter the guild
        
        Returns
        -------
        Optional[:class:`bool`]:
            Returns `True` if the member was successfully removed from the database. `False` if the member was not in the database so there was nothing to remove

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `DiscordLevelingSystemError`: Parameter :param:`member` was not of type :class:`discord.Member` or :class:`int`
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        
            .. changes::
                v1.0.0
                    Added :param:`guild`
        """
        if isinstance(member, (Member, int)):
            member_id = member.id if isinstance(member, Member) else member
            removable = await self.is_in_database(member_id, guild=guild if guild else None)
            if removable:
                query = 'DELETE FROM leaderboard WHERE member_id = ? AND guild_id = ?' if guild else 'DELETE FROM leaderboard WHERE member_id = ?'
                params = (member_id, guild.id) if guild else (member_id,)
                
                await self._cursor.execute(query, params)
                await self._connection.commit()
            return removable
        else:
            raise DiscordLevelingSystemError(f'Parameter "member" expected discord.Member or int, got {member.__class__.__name__}')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def is_in_database(self, member: Union[Member, int], guild: Optional[Guild]=None) -> bool:
        """|coro| A quick check to see if a member is in the database. This is not guild specific although it can be if :param:`guild` is specified

        Parameters
        ----------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member to check for. Can be the member object or that members ID
        
        guild: Optional[:class:`discord.Guild`]
            The guild to check if the member is registered in
        
        Returns
        -------
        :class:`bool`

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: Parameter :param:`member` was not of type :class:`discord.Member` or :class:`int`
        
            .. changes::
                v1.0.0
                    Added :param:`guild`
        """
        if not isinstance(member, (Member, int)): raise DiscordLevelingSystemError(f'Parameter "member" expected discord.Member or int, got {member.__class__.__name__}')
        arg = member.id if isinstance(member, Member) else member
        query = 'SELECT * FROM leaderboard WHERE member_id = ? AND guild_id = ?' if guild else 'SELECT * FROM leaderboard WHERE member_id = ?'
        params = (arg, guild.id) if guild else (arg,)
        
        async with self._connection.execute(query, params) as cursor:
            result = await cursor.fetchone()
            if result: return True
            else: return False
        
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_record_count(self, guild: Optional[Guild]=None) -> int:
        """|coro| Get the amount of members that are registered in the database. If :param:`guild` is set to :class:`None`, all members in the database will be counted

        Parameters
        ----------
        guild: Optional[:class:`discord.Guild`]
            The guild for which to count the amount of records

        Returns
        -------
        :class:`int`

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        
            .. changes::
                v0.0.2
                    Added :param:`guild`
        """
        if guild:   await self._cursor.execute('SELECT COUNT(*) from leaderboard WHERE guild_id = ?', (guild.id,))
        else:       await self._cursor.execute('SELECT COUNT(*) from leaderboard')
        
        result = await self._cursor.fetchone()
        if result: return result[0]
        else: return 0
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def next_level_up(self, member: Member) -> int:
        """|coro| Get the amount of XP needed for the specified member to level up
        
        Parameters
        ----------
        member: :class:`discord.Member`
            Member to get the amount of XP needed for a level up
        
        Returns
        -------
        :class:`int`:
            Returns 0 if the member is currently at max level.
            Can return :class:`None` if the member is not in the database.

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        data = await self.get_data_for(member)
        if not data:
            return None
        if data.level == 100:
            return 0
        else:
            details = _next_level_details(data.level)
            return details.xp_needed - data.xp
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_xp_for(self, member: Member) -> int:
        """|coro| Get the XP for the specified member
        
        Parameters
        ----------
        member: :class:`discord.Member`
            Member to get the XP for
        
        Returns
        -------
        :class:`int`:
            Can be :class:`None` if the member isn't in the database

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        md = await self.get_data_for(member)
        if md: return md.xp
        else: return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_total_xp_for(self, member: Member) -> int:
        """|coro| Get the total XP for the specified member
        
        Parameters
        ----------
        member: :class:`discord.Member`
            Member to get the total XP for
        
        Returns
        -------
        :class:`int`:
            Can be :class:`None` if the member isn't in the database

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        md = await self.get_data_for(member)
        if md: return md.total_xp
        else: return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_level_for(self, member: Member) -> int:
        """|coro| Get the level for the specified member
        
        Parameters
        ----------
        member: :class:`discord.Member`
            Member to get the level for
        
        Returns
        -------
        :class:`int`:
            Can be :class:`None` if the member isn't in the database

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        md = await self.get_data_for(member)
        if md: return md.level
        else: return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_data_for(self, member: Member) -> MemberData:
        """|coro| Get the :class:`MemberData` object that represents the specified member
        
        Parameters
        ----------
        member: :class:`discord.Member`
            The member to get the data for
        
        Returns
        -------
        :class:`MemberData`:
            Can return :class:`None` if the member was not found in the database

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        async with self._connection.execute('SELECT * FROM leaderboard WHERE member_id = ? AND guild_id = ?', (member.id, member.guild.id)) as cursor:
            result = await cursor.fetchone()
            if result:
                m_id = result[1]
                m_name = result[2]
                m_level = result[3]
                m_xp = result[4]
                m_total_xp = result[5]
                m_rank = await self.get_rank_for(member)
                return MemberData(m_id, m_name, m_level, m_xp, m_total_xp, m_rank)
            else:
                return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def each_member_data(self, guild: Guild, sort_by: Optional[str]=None) -> List[MemberData]:
        """|coro| Return each member in the database as a :class:`MemberData` object for easy access to their XP, level, etc.

        Parameters
        ----------
        guild: :class:`discord.Guild`
            A guild object
        
        sort_by: Optional[:class:`str`]
            Return each member data sorted by: 
        
        - "name"
        - "level"
        - "xp"
        - "rank"
        - :class:`None`
        
        If :class:`None`, it will return in the order they were added to the database
        
        Returns
        -------
        List[:class:`MemberData`]

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: The value of :param:`sort_by` was not recognized or :param:`guild` was not of type :class:`discord.Guild`
        """
        if not isinstance(guild, Guild):
            raise DiscordLevelingSystemError(f'Parameter "guild" expected discord.Guild got {guild.__class__.__name__}')
        else:
            # NOTE: there's no need to worry about this method returning :class:`None` because as soon as someone sends a message they are added to the database

            async def result_to_memberdata(query_result) -> List[MemberData]:
                """Convert the query result into a :class:`list` of :class:`MemberData` objects"""
                data = []
                for m_id, m_name, m_level, m_xp, m_total_xp in query_result:
                    rank = None
                    member = guild.get_member(m_id)
                    if member:
                        rank = await self.get_rank_for(member) # if the member is None (no longer in guild), rank will be None. This is intentional
                    data.append(MemberData(m_id, m_name, m_level, m_xp, m_total_xp, rank))
                return data

            if not sort_by:
                result = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ?', (guild.id,))
                return await result_to_memberdata(result)
            else:
                sort_by = sort_by.lower()
                if sort_by in ('name', 'level', 'xp', 'rank'):
                    if sort_by == 'name':
                        result = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ? ORDER BY member_name COLLATE NOCASE', (guild.id,))
                        return await result_to_memberdata(result)
                    
                    elif sort_by == 'level':
                        result = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ? ORDER BY member_level DESC', (guild.id,))
                        return await result_to_memberdata(result)
                    
                    elif sort_by == 'xp':
                        result = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ? ORDER BY member_total_xp DESC', (guild.id,))
                        return await result_to_memberdata(result)

                    elif sort_by == 'rank':
                        def convert(md: MemberData) -> MemberData:
                            """Set the rank to an :class:`int` value of 0 because it is not possible to sort a list of :class:`int` that has :class:`None` values"""
                            if md.rank is None:
                                md.rank = 0
                            return md
                        
                        result = await self._connection.execute_fetchall('SELECT member_id, member_name, member_level, member_xp, member_total_xp FROM leaderboard WHERE guild_id = ?', (guild.id,))
                        all_data: List[MemberData] = await result_to_memberdata(result)
                        
                        converted = [convert(md) for md in all_data] # convert the data so it can be sorted properly
                        sorted_converted = sorted(converted, key=lambda md: md.rank)

                        no_rank = [md for md in sorted_converted if md.rank == 0]
                        with_rank = [md for md in sorted_converted if md.rank != 0]
                        pre_final = with_rank + no_rank
    
                        def zero_to_none(md: MemberData) -> MemberData:
                            """If they're not in the guild anymore, I don't want their rank to be presented as zero because that implies they are still in the guild, but just has
                            a rank of zero. Setting it back to :class:`None` makes it more readable and draws further implication that they're no longer in the guild
                            """
                            if md.rank == 0:
                                md.rank = None
                            return md
                        
                        final = [zero_to_none(md) for md in pre_final]
                        return final
                else:
                    raise DiscordLevelingSystemError(f'Parameter "sort_by" expected "name", "level", "xp", or "rank", {sort_by!r} was not recognized')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_rank_for(self, member: Member) -> int:
        """|coro| Get the rank for the specified member
        
        Parameters
        ----------
        member: :class:`discord.Member`
            Member to get the rank for
        
        Returns
        -------
        :class:`int`:
            Can be :class:`None` if the member isn't ranked yet

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        result = await self._connection.execute_fetchall('SELECT member_id FROM leaderboard WHERE guild_id = ? ORDER BY member_total_xp DESC', (member.guild.id,))
        all_ids = [m_id[0] for m_id in result]
        try:
            rank = all_ids.index(member.id) + 1
            return rank
        except ValueError:
            return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def sql_query_get(self, sql: str, parameters: Optional[Tuple[Union[str, int]]]=None, fetch: Union[str, int]='ALL') -> Union[List[tuple], tuple]:
        """|coro| Query and return something from the database using SQL. The following columns are apart of the "leaderboard" table:

        - guild_id
        - member_id
        - member_name
        - member_level
        - member_xp
        - member_total_xp

        Parameters
        ----------
        sql: :class:`str`
            SQL string used to query the database
        
        parameters: Optional[Tuple[Union[:class:`str`, :class:`int`]]]
            The parameters used for the database query
        
        fetch: Union[:class:`str`, :class:`int`]
            The amount of rows you would like back from the query. Options: 'ALL', 'ONE', or an integer value that is greater than zero
        
        Returns
        -------
        Union[List[:class:`tuple`], :class:`tuple`]:

        - Using `fetch='ALL'` returns List[:class:`tuple`]
        - Using `'fetch='ONE'` returns :class:`tuple`
        - Using `fetch=4` returns List[:class:`tuple`] with only four values
        
        Can also return an empty list if the query was valid but got nothing from it
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystemError`: Argument "fetch" was the wrong type or used an invalid value
        - `aiosqlite.Error`: Base aiosqlite error. Multiple errors can arise from this if the SQL query was invalid
        """
        if isinstance(fetch, str):
            fetch = fetch.upper()
            if fetch in ('ALL', 'ONE'):
                async with self._connection.execute(sql, parameters) as cursor:
                    if fetch == 'ALL':
                        return await cursor.fetchall()
                    elif fetch == 'ONE':
                        return await cursor.fetchone()
            else:
                raise DiscordLevelingSystemError(f'Fetch {fetch!r} not recognized')
        elif isinstance(fetch, int):
            if fetch > 0:
                async with self._connection.execute(sql, parameters) as cursor:
                    return await cursor.fetchmany(fetch)
            else:
                raise DiscordLevelingSystemError('Argument "fetch" must be greater than zero')
        else:
            raise DiscordLevelingSystemError(f'Argument "fetch" needs to be str or int, got {fetch.__class__.__name__}')
    
    def _get_last_award(self, current_award: RoleAward, guild_awards: List[RoleAward]) -> RoleAward:
        """Get the last :class:`RoleAward` that was given to the member. Returns the current :class:`RoleAward` if the last award is the current one
        
            .. changes::
                v0.0.2
                    Added :param:`guild_awards`
        """
        current_award_idx = guild_awards.index(current_award)
        last_award_idx = guild_awards.index(current_award) - 1
        if last_award_idx < 0:
            last_award_idx = current_award_idx

        if last_award_idx == current_award_idx:
            return current_award
        else:
            return guild_awards[last_award_idx]
    
    async def _refresh_name(self, message: Message):
        """|coro| If the members current database name doesn't match the name that's on discord, update the name in the database

            .. NOTE
                This is called AFTER we update or insert a new member into the database from :meth:`award_xp`, so :meth:`fetchone` will always return something
        """
        async with self._connection.execute('SELECT member_name FROM leaderboard WHERE member_id = ? AND guild_id = ?', (message.author.id, message.author.guild.id)) as cursor:
            data = await cursor.fetchone()
            database_name = data[0]
            if database_name != str(message.author):
                await cursor.execute('UPDATE leaderboard SET member_name = ? WHERE member_id = ? AND guild_id = ?', (str(message.author), message.author.id, message.author.guild.id))
                await self._connection.commit()
    
    async def _handle_level_up(self, message: Message, md: MemberData, leveled_up: bool):
        """|coro| Gives/removes roles from members that leveled up and met the :class:`RoleAward` requirement. This also sends the level up message
        
            .. changes::
                v0.0.2
                    Added handling for level up messages that are embeds
                    Added handling for random selections of level up messages
                    Added :param:`md`
                    Added :param:`leveled_up`
                    Added if check for :param:`leveled_up`
                    Added :func:`send_announcement`
                    Removed raising of exception (AwardedRoleNotFound) to support multi-guild leveling
                    Removed raising of exception (LevelUpChannelNotFound) to support multi-guild level up channel IDs
                v1.0.2
                    Added handling for event `on_dls_level_up`
        """
        if leveled_up:
            member = message.author       
            
            def role_exists(award: RoleAward):
                """Check to ensure the role associated with the :class:`RoleAward` still exists in the guild. If it does, it returns that discord role object for use"""
                role_obj = message.guild.get_role(award.role_id)
                if role_obj: return role_obj
                else: return False
            
            async def send_announcement(announcement_message, channel, send_kwargs):
                """|coro| Send the level up message

                    .. added:: v0.0.2
                """
                if isinstance(announcement_message, str):
                    await channel.send(announcement_message, **send_kwargs)
                else:
                    await channel.send(embed=announcement_message, **send_kwargs)
            
            # send the level up message
            if self.announce_level_up:
                
                # set the values for the level up announcement
                lua: LevelUpAnnouncement = random.choice(self.level_up_announcement) if isinstance(self.level_up_announcement, Sequence) else self.level_up_announcement
                lua._total_xp = md.total_xp
                lua._level = md.level
                lua._rank = md.rank
                announcement_message = lua._parse_message(lua.message, self._message_author)

                if lua.level_up_channel_ids:
                    channel_found = False
                    for channel_id in lua.level_up_channel_ids:
                        channel = message.guild.get_channel(channel_id)
                        if channel:
                            channel_found = True
                            break
                    
                    if channel_found:
                        await send_announcement(announcement_message, channel, lua._send_kwargs)
                    else:
                        await send_announcement(announcement_message, message.channel, lua._send_kwargs)
                else:
                    await send_announcement(announcement_message, message.channel, lua._send_kwargs)
            
            # check if there is a role award for the new level, if so, apply it
            if self._awards:
                try:
                    # get the list of RoleAwards that match the guild ID
                    guild_role_awards: List[RoleAward] = self._awards[message.guild.id]
                except KeyError:
                    return
                else:
                    # get the role award that matches the level up
                    role_award = [ra for ra in guild_role_awards if ra.level_requirement == md.level]
                    if role_award:
                        role_award = role_award[0]
                        if self.stack_awards:
                            role_obj: Role = role_exists(award=role_award)
                            if role_obj:
                                await member.add_roles(role_obj)
                            else:
                                return
                        else:
                            last_award: RoleAward = self._get_last_award(role_award, guild_role_awards)
                            role_to_remove: Role = role_exists(award=last_award)
                            role_to_add: Role = role_exists(award=role_award)
                            
                            # Note: Don't use an exception here because of multi-guild support
                            if not role_to_remove or not role_to_add:
                                return

                            if last_award == role_award:
                                await member.add_roles(role_to_add)
                            else:
                                await member.add_roles(role_to_add)
                                await member.remove_roles(role_to_remove)
            
            if self.bot is not None:
                self.bot.dispatch('dls_level_up', member, message, md)
    
    def _handle_amount_param(self, arg: Union[int, Sequence[int]]):
        """Simple check to ensure the proper types are being used for parameter "amount" in method :meth:`DiscordLevelingSystem.award_xp()`
        
            .. changes::
                v0.0.2
                    Added check to ensure the first value is larger than the next
                    Added check to ensure the each value is unique
                    Changed the value range from 1-100 to 1-25
                v1.0.3
                    Changed from list to Sequence
        """
        if isinstance(arg, (int, Sequence)):
            if isinstance(arg, int):
                # ensures the values are from 1-25
                if arg <= 0 or arg > 25:
                    raise DiscordLevelingSystemError('Parameter "amount" can only be a value from 1-25')
            else:
                # ensures there are only 2 values in the sequence
                if len(arg) != 2:
                    raise DiscordLevelingSystemError('Parameter "amount" sequence must only have two values')
                
                # ensures all values in the sequence are of type int
                for item in arg:
                    if not isinstance(item, int):
                        raise DiscordLevelingSystemError('Parameter "amount" sequence, all values must be of type int')
                
                # ensures all values in the sequence are >= 1 and <= 25
                for item in arg:
                    if item <= 0 or item > 25:
                        raise DiscordLevelingSystemError('Parameter "amount" sequence, all values can only be from 1-25')
                
                # ensures each value is unique
                if arg[0] == arg[1]:
                    raise DiscordLevelingSystemError('Parameter "amount" sequence expects both values to be unique')
                
                # ensures the first value is larger than the next
                if arg[1] < arg[0]:
                    raise DiscordLevelingSystemError('Parameter "amount" sequence expected value 1 to be larger than value 2')
        else:
            raise DiscordLevelingSystemError(f'Parameter "amount" expected int or Sequence, got {arg.__class__.__name__}')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def award_xp(self, *, amount: Union[int, Sequence[int]]=[15, 25], message: Message, refresh_name: bool=True, **kwargs):
        """|coro| Give XP to the member that sent a message

        Parameters
        ----------
        amount: Union[:class:`int`, Sequence[:class:`int`]]
            The amount of XP to award to the member per message. Must be from 1-25. Can be a sequence with a minimum and maximum length of two. If :param:`amount` is a sequence of two integers, it will randomly
            pick a number in between those numbers including the numbers provided
        
        message: :class:`discord.Message`
            A message object
        
        refresh_name: :class:`bool`
            Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is
            suggested to leave this as `True` so the database can always have the most up-to-date record

        Kwargs
        ------
        bonus: :class:`DiscordLevelingSystem.Bonus`
            Set the bonus values. Read the :class:`DiscordLevelingSystem.Bonus` doc string for more details (defaults to :class:`None`)
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        
            .. changes::
                v0.0.2
                    Added handling for bonus xp (kwarg "bonus")
                    Added initialization for :attr:`_message_author`
                    Replaced query with class attr
                    Moved the detection of a level up from :meth:`_handle_level_up` to here
        """
        if any([message.guild is None, self._determine_no_xp(message), message.author.bot, message.type != MessageType.default, self.active is False]):
            return
        else:
            self._handle_amount_param(arg=amount)
            if isinstance(amount, Sequence):
                amount = random.randint(amount[0], amount[1])
            
            # bonus XP
            bonus: DiscordLevelingSystem.Bonus = kwargs.get('bonus')
            if bonus:
                for role_id in bonus.role_ids:
                    role = message.guild.get_role(role_id)
                    if role in message.author.roles:
                        if bonus.multiply:
                            amount *= bonus.bonus_amount
                        else:
                            amount += bonus.bonus_amount
                        
                        if amount > 75:
                            amount = 75
                        break
            
            bucket = self._cooldown.get_bucket(message)
            on_cooldown = bucket.update_rate_limit()

            if not on_cooldown:
                member = message.author
                self._message_author = member
                async with self._connection.execute('SELECT * FROM leaderboard WHERE member_id = ? AND guild_id = ?', (member.id, member.guild.id)) as cursor:
                    record = await cursor.fetchone()
                    member_level_up = False
                    if record:
                        # update the database with the new amount
                        query = """
                            UPDATE leaderboard
                            SET member_xp = member_xp + ?, member_total_xp = member_total_xp + ?
                            WHERE member_id = ? AND guild_id = ?
                        """
                        await cursor.execute(query, (amount, amount, member.id, member.guild.id))
                        await self._connection.commit()

                        # get the updated member data (level is not updated yet)
                        md = await self.get_data_for(member)

                        next_details = _next_level_details(md.level)
                        if md.xp >= next_details.xp_needed and md.level < next_details.level:
                            # update the database with the new level and reset the current XP count
                            await cursor.execute('UPDATE leaderboard SET member_level = ?, member_xp = ? WHERE member_id = ? AND guild_id = ?', (next_details.level, 0, member.id, member.guild.id))
                            await self._connection.commit()
                            member_level_up = True

                        md = await self.get_data_for(member)
                        await self._handle_level_up(message, md, leveled_up=member_level_up)

                    else:
                        await cursor.execute(DiscordLevelingSystem._QUERY_NEW_MEMBER, (member.guild.id, member.id, str(member), 0, amount, amount))
                        await self._connection.commit()

                    if refresh_name:
                        await self._refresh_name(message)
