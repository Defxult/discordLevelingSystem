"""
MIT License

Copyright (c) 2021 Defxult#8269

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
from datetime import datetime
import json
import os
import random
import shutil
from typing import Union, List, Tuple, Dict, Optional

import aiosqlite
from discord.ext.commands import BucketType, CooldownMapping
from discord import Member, Role, Message, Guild

from .announcement import LevelUpAnnouncement
from .decorators import db_file_exists, leaderboard_exists, verify_leaderboard_integrity
from .errors import *
from .levels_xp_needed import LEVELS_AND_XP, _next_level_details
from .member_data import MemberData
from .role_awards import RoleAward


class DiscordLevelingSystem:
    """A local discord.py leveling system powered by SQLite

    Parameters
    ----------
    rate: :class:`int`
        (optional) The amount of messages each member can send before the cooldown triggers (defaults to 1)

    per: :class:`float`
        (optional) The amount of seconds each member has to wait before gaining more XP, aka the cooldown (defaults to 60.0)
    
    awards: :class:`List[RoleAward]`
        (optional) The role given to a member when they reach a :class:`RoleAward` level requirement (defaults to :class:`None`)

    Kwargs
    ------
    no_xp_roles: :class:`List[int]`
        (optional) A list of role ID's. Any member with any of those roles will not gain XP when sending messages (defaults to :class:`None`)
    
    no_xp_channels: :class:`List[int]`
        (optional) A list of text channel ID's. Any member sending messages in any of those text channels will not gain XP (defaults to :class:`None`)
    
    announce_level_up: :class:`bool`
        (optional) If `True`, level up messages will be sent when a member levels up (defaults to `True`)

    stack_awards: :class:`bool`
        (optional) If this is `True`, when the member levels up the assigned role award will be applied. If `False`, the previous role award will be removed
        and the level up assigned role will also be applied (defaults to `True`)

    level_up_announcement: :class:`LevelUpAnnouncement`
        (optional) The message that is sent when someone levels up (defaults to :class:`LevelUpAnnouncement()`)
    
    Attributes
    ----------
    - `awards`
    - `no_xp_roles`
    - `no_xp_channels`
    - `announce_level_up`
    - `stack_awards`
    - `level_up_announcement`
    """

    def __init__(self, rate: int=1, per: float=60.0, awards: Union[List[RoleAward], None]=None, **kwargs):
        if rate <= 0 or per <= 0:   raise DiscordLevelingSystemError('Invalid rate or per. Values must be greater than zero')
        self._rate = rate
        self._per = per
        self.awards = awards

        self.no_xp_roles: List[int] = kwargs.get('no_xp_roles')
        self.no_xp_channels: List[int] = kwargs.get('no_xp_channels')
        self.announce_level_up: bool = kwargs.get('announce_level_up', True)
        self.stack_awards: bool = kwargs.get('stack_awards', True)
        self.level_up_announcement: LevelUpAnnouncement = kwargs.get('level_up_announcement', LevelUpAnnouncement())

        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)
        self._connection: aiosqlite.Connection = None
        self._cursor: aiosqlite.Cursor = None
        self._loop = asyncio.get_event_loop()
        self._database_file_path: str = None
        self._default_levels = True

        RoleAward._verify_awards_integrity(awards)
        RoleAward._verify_duplicate_awards(awards)
    
    @staticmethod
    def create_database_file(path: str):
        """|static method| Create the database file and implement the SQL data for the database
        
        Parameter
        ---------
        path: :class:`str`
            The location to create the database file
        
        Raises
        ------
        - `ConnectionFailure`: Attempted to connect to the database file when the event loop is already running
        - `DiscordLevelingSystemError`: The path does not exist or the path points to a file instead of a directory
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
                            member_id INT PRIMARY KEY,
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

        with_timestamp: :class:`bool`:
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
        
        Parameter
        ---------
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

    def _determine_no_xp(self, message: Message) -> bool:
        """Check if the channel the member is sending messages in is a no XP channel. This also checks if any of the roles they have is a no XP role"""
        has_no_xp_role = False
        in_no_xp_channel = False

        # make sure the no xp roles and no xp text channels still exists in the guild
        if self.no_xp_roles:
            for no_xp_role_id in self.no_xp_roles:
                role = message.guild.get_role(no_xp_role_id)
                if not role:
                    raise DiscordLevelingSystemError(f'The no XP role with ID {no_xp_role_id} was not found in the guild')
            else:
                # if we get to this point, all no xp roles still exist in the guild
                author_role_ids = [r.id for r in message.author.roles] # message.author.roles will never be :class:`None` because users will ALWAYS have at least one role. the @everyone role
                for role_id in self.no_xp_roles:
                    if role_id in author_role_ids:
                        has_no_xp_role = True
                        break
        
        # if :var:`has_no_xp_role` is True, there's no point in doing another loop to check if their in a no XP channel because only 1 needs to be True to determine the action that 
        # needs to be taken. Just check if :var:`has_no_xp_role` is True and if it is, return
        if has_no_xp_role:
            return has_no_xp_role

        if self.no_xp_channels:
            for no_xp_channel_id in self.no_xp_channels:
                channel = message.guild.get_channel(no_xp_channel_id)
                if not channel:
                    raise DiscordLevelingSystemError(f'The no XP channel with ID {no_xp_channel_id} was not found in the guild')
            else:
                # if we get to this point, all no xp channels still exist in the guild
                if message.channel.id in self.no_xp_channels:
                    in_no_xp_channel = True

        return any([has_no_xp_role, in_no_xp_channel])
    
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
        """
        if rate <= 0 or per <= 0:   raise DiscordLevelingSystemError('Invalid rate or per. Values must be greater than zero')
        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)

    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def refresh_names(self, guild: Guild) -> Optional[int]:
        """|coro| Update names inside the database. This does not add anything new. It simply verifies if the name in the database matches their current name, and if they don't match, update
        the database name
        
        Parameter
        ---------
        guild: :class:`discord.Guild`
            A guild object
        
        Returns
        -------
        :class:`Optional[int]`:
            The amount of records in the database that were updated

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        async with self._connection.execute('SELECT member_id, member_name FROM leaderboard') as cursor:
            result = await cursor.fetchall()
            names_updated = 0
            if result:
                database_ids = [db[0] for db in result]
                database_names = [db[1] for db in result]
                for db_id, db_name in zip(database_ids, database_names):
                    member = guild.get_member(db_id)
                    if member:
                        if str(member) != db_name:
                            await cursor.execute('UPDATE leaderboard SET member_name = ? WHERE member_id = ?', (str(member), db_id))
                            await self._connection.commit()
                            names_updated += 1

            return names_updated
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def wipe_database(self, *, intentional: bool=False):
        """|coro| Delete EVERYTHING from the database

        Parameters
        ----------
        intentional: :class:`bool`:
            (optional) A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone (defaults to `False`)

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `FailSafe`: "intentional" argument for this method was set to `False` in case you called this method by mistake
        """
        if intentional:
            await self._cursor.execute('DELETE FROM leaderboard')
            await self._connection.commit()
        else:
            raise FailSafe
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def clean_database(self, all_members: List[Member]) -> Optional[int]:
        """|coro| Removes the data for members that are no longer in the guild, thus reducing the database file size. It is recommended to have this method in a background loop
        in order to keep the database file free of records that are no longer in use

        Parameter
        ---------
        all_members: :class:`List[discord.Member]`
            A list of all guild `discord.Member` objects
        
        Returns
        -------
        :class:`Optional[int]`:
            The amount of records that were removed from the database
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        async with self._connection.execute('SELECT member_id FROM leaderboard') as cursor:
            active_member_ids = [m.id for m in all_members]
            records_removed = 0
            for row in await cursor.fetchall():
                member_id = row[0]
                if member_id not in active_member_ids:
                    await cursor.execute('DELETE FROM leaderboard WHERE member_id = ?', (member_id,))
                    await self._connection.commit()
                    records_removed += 1
            return records_removed
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def reset_member(self, member: Member):
        """|coro| Sets the members XP, total XP, and level to zero
        
        Parameter
        ---------
        member: :class:`discord.Member`
            The member to reset
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        await self._cursor.execute('UPDATE leaderboard SET member_level = 0, member_xp = 0, member_total_xp = 0 WHERE member_id = ?', (member.id,))
        await self._connection.commit()
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def reset_everyone(self, *, intentional: bool=False):
        """|coro| Sets EVERYONES XP, total XP, and level to zero in the database

        Parameters
        ----------
        intentional: :class:`bool`:
            (optional) A simple kwarg to try and ensure that this action is indeed what you want to do. Once executed, this cannot be undone (defaults to `False`)

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `FailSafe`: "intentional" argument for this method was set to `False` in case you called this method by mistake
        """
        if intentional:
            await self._cursor.execute('UPDATE leaderboard SET member_level = 0, member_xp = 0, member_total_xp = 0')
            await self._connection.commit()
        else:
            raise FailSafe
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def export_as_json(self, path: str):
        """|coro| Export a json file that represents the database to the path specified
        
        Parameter
        ---------
        path :class:`str`:
            Path to copy the json file to
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        - `DiscordLevelingSystem`: The path does not exist or does not point to a directory
        """
        if os.path.exists(path) and os.path.isdir(path):
            path = os.path.join(path, 'discord_leveling_system.json')
            levels = {}
            data = await self._connection.execute_fetchall('SELECT * FROM leaderboard')
            for m_id, m_name, m_lvl, m_xp, m_total_xp in data:
                levels[str(m_id)] = {
                    'name' : m_name,
                    'level' : m_lvl,
                    'xp' : m_xp,
                    'total_xp' : m_total_xp
                }
            with open(path, mode='w') as fp:
                json.dump(levels, fp, indent=4)
        else:
            raise DiscordLevelingSystemError(f'The path {path!r} does not exist or does not point to a directory')

    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def raw_database_contents(self) -> List[tuple]:
        """|coro| Returns everything in the database
        
        Returns
        -------
        :class:`List[tuple]`:
            The tuples inside the list represents each row of the database. Each tuple contains five values.
                Index 0 is their ID
                Index 1 is their name
                Index 2 is their level
                Index 3 is their XP
                Index 4 is their total xp.
            Can be an empty list if nothing is in the database
        
        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        return await self._connection.execute_fetchall('SELECT * FROM leaderboard')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def remove_from_database(self, member: Union[Member, int]) -> Optional[bool]:
        """|coro| Remove a member from the database

        Parameter
        ---------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member to remove. Can be the member object or that members ID
        
        Returns
        -------
        :class:`Optional[bool]`:
            Returns `True` if the member was successfully removed from the database. `False` if the member was not in the database so there was nothing to remove

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `DiscordLevelingSystemError`: Parameter :param:`member` was not of type :class:`discord.Member` or :class:`int`
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        if isinstance(member, (Member, int)):
            if isinstance(member, Member):
                if await self.is_in_database(member):
                    await self._cursor.execute('DELETE FROM leaderboard WHERE member_id = ?', (member.id,))
                    await self._connection.commit()
                    return True
                else:
                    return False
            else:
                member_id = member
                if await self.is_in_database(member_id):
                    await self._cursor.execute('DELETE FROM leaderboard WHERE member_id = ?', (member_id,))
                    await self._connection.commit()
                    return True
                else:
                    return False
        else:
            raise DiscordLevelingSystemError(f'Paramater "member" expected discord.Member or int, got {member.__class__.__name__}')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def is_in_database(self, member: Union[Member, int]) -> bool:
        """|coro| A quick check to see if a member is in the database

        Parameter
        ---------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member to check for. Can be the member object or that members ID
        
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
        """
        if isinstance(member, Member):
            arg = member.id
        elif isinstance(member, int):
            arg = member
        else:
            raise DiscordLevelingSystemError(f'Parameter "member" expected discord.Member or int, got {member.__class__.__name__}')

        async with self._connection.execute('SELECT * FROM leaderboard WHERE member_id = ?', (arg,)) as cursor:
            result = await cursor.fetchone()
            if result: return True
            else: return False
        
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_record_count(self) -> int:
        """|coro| Get the amount of members that are registered in the database

        Returns
        -------
        :class:`int`

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        async with self._connection.execute('SELECT COUNT(*) from leaderboard') as cursor:
            result = await cursor.fetchone()
            if result: return result[0]
            else: return 0
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def next_level_up(self, member: Member) -> int:
        """|coro| Get the amount of XP needed for the specified member to level up
        
        Parameter
        ---------
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
            next_level = details[0]
            next_level_xp_needed = details[1]
            return next_level_xp_needed - data.xp
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def get_xp_for(self, member: Member) -> int:
        """|coro| Get the XP for the specified member
        
        Parameter
        ---------
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
        
        Parameter
        ---------
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
        
        Parameter
        ---------
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
        
        Parameter
        ---------
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
        async with self._connection.execute('SELECT * FROM leaderboard WHERE member_id = ?', (member.id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                m_id = result[0]
                m_name = result[1]
                m_level = result[2]
                m_xp = result[3]
                m_total_xp = result[4]
                m_rank = await self.get_rank_for(member)
                return MemberData(m_id, m_name, m_level, m_xp, m_total_xp, m_rank)
            else:
                return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def each_member_data(self, guild: Guild, sort_by: str=None) -> List[MemberData]:
        """|coro| Return each member in the database as a :class:`MemberData` object for easy access to their XP, level, etc.

        Parameters
        ----------
        guild: :class:`discord.Guild`
            A :class:`discord.Guild` object
        
        sort_by: :class:`str`
            (optional) Return each member data sorted by: "name", "level", "xp", "rank", or :class:`None`. If :class:`None`, it will return in the order they were added to the database (defaults to :class:`None`)
        
        Returns
        -------
        :class:`List[MemberData]`

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
                result = await self._connection.execute_fetchall('SELECT * FROM leaderboard')
                return await result_to_memberdata(result)
            else:
                sort_by = sort_by.lower()
                if sort_by in ('name', 'level', 'xp', 'rank'):
                    if sort_by == 'name':
                        result = await self._connection.execute_fetchall('SELECT * FROM leaderboard ORDER BY member_name COLLATE NOCASE')
                        return await result_to_memberdata(result)
                    
                    elif sort_by == 'level':
                        result = await self._connection.execute_fetchall('SELECT * FROM leaderboard ORDER BY member_level DESC')
                        return await result_to_memberdata(result)
                    
                    elif sort_by == 'xp':
                        result = await self._connection.execute_fetchall('SELECT * FROM leaderboard ORDER BY member_total_xp DESC')
                        return await result_to_memberdata(result)

                    elif sort_by == 'rank':
                        def convert(md: MemberData):
                            """Set the rank to an :class:`int` value of 0 because it is not possible to sort a list of :class:`int` that has :class:`None` values"""
                            if md.rank is None:
                                md.rank = 0
                            return md
                        
                        result = await self._connection.execute_fetchall('SELECT * FROM leaderboard')
                        all_data: List[MemberData] = await result_to_memberdata(result)
                        
                        converted = [convert(md) for md in all_data] # convert the data so it can be sorted properly
                        sorted_converted = sorted(converted, key=lambda md: md.rank)

                        no_rank = [md for md in sorted_converted if md.rank == 0]
                        with_rank = [md for md in sorted_converted if md.rank != 0]
                        pre_final = with_rank + no_rank
    
                        def zero_to_none(md: MemberData):
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
        
        Parameter
        ---------
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
        result = await self._connection.execute_fetchall('SELECT member_id FROM leaderboard ORDER BY member_total_xp DESC')
        all_ids = [m_id[0] for m_id in result]
        try:
            rank = all_ids.index(member.id) + 1
            return rank
        except ValueError:
            return None
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def sql_query_get(self, sql: str, parameters: Tuple[Union[str, int]]=None, fetch: Union[str, int]='ALL') -> Union[List[tuple], tuple]:
        """|coro| Query and return something from the database using SQL

        Parameters
        ----------
        sql: :class:`str`
            SQL string used to query the database

        parameters: :class:`Tuple[Union[str, int]]`
            (optional) The parameters use for the database query (defaults to :class:`None`)
        
        fetch: :class:`Union[str, int]`
            (optional) The amount of rows you would like back from the query. Options: 'ALL', 'ONE', or an integer value that is greater than zero (defaults to 'ALL')
        
        Returns
        -------
        :class:`Union[List[tuple], tuple]`:
            Using `fetch='ALL'` returns `List[tuple]`
            Using `'fetch='ONE'` returns `tuple`
            Using `fetch=4` returns `List[tuple]` with only four values
            Can also return :class:`None` if nothing matched the query

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
    
    def _get_last_award(self, current_award: RoleAward) -> RoleAward:
        """Get the last :class:`RoleAward` that was given to the member. Returns the current :class:`RoleAward` if the last award is the current one"""
        current_award_idx = self.awards.index(current_award)
        last_award_idx = self.awards.index(current_award) - 1
        if last_award_idx < 0:
            last_award_idx = current_award_idx

        if last_award_idx == current_award_idx:
            return current_award
        else:
            return self.awards[last_award_idx]
    
    def _get_next_award(self, current_award: RoleAward) -> RoleAward:
        """Get the next :class:`RoleAward` that will be given to the member. Returns the current :class:`RoleAward` if the next award is the current one"""
        current_award_idx = self.awards.index(current_award)
        next_award_idx = self.awards.index(current_award) + 1
        if next_award_idx > len(self.awards) - 1:
            next_award_idx = current_award_idx

        if next_award_idx == current_award_idx:
            return current_award
        else:
            return self.awards[next_award_idx]
    
    async def _refresh_name(self, message: Message):
        """|coro| If the members current database name doesn't match the name that's on discord, update the name in the database

            .. NOTE
                This is called AFTER we update or insert a new member into the database from :meth:`award_xp`, so :meth:`fetchone` will always return something
        """
        async with self._connection.execute('SELECT member_name FROM leaderboard WHERE member_id = ?', (message.author.id,)) as cursor:
            data = await cursor.fetchone()
            database_name = data[0]
            if database_name != str(message.author):
                await cursor.execute('UPDATE leaderboard SET member_name = ? WHERE member_id = ?', (str(message.author), message.author.id))
                await self._connection.commit()
    
    async def _handle_level_up(self, message: Message):
        """|coro| Gives/removes roles from members that leveled up and met the :class:`RoleAward` requirement. This also sends the level up message"""
        member = message.author

        # if member_data is :class:`None`, their not in the database so raise an error
        member_data = await self.get_data_for(member)
        if not member_data: # if this executes, they manually got a member. the member needs to send messages as normal to get XP
            raise DiscordLevelingSystemError('Cannot award XP to someone that is not in the database')
        
        # check if they're already max level. if so, the rest doesn't need to be executed
        max_xp = LEVELS_AND_XP['100']
        max_level = 100
        if member_data.xp >= max_xp and member_data.level >= max_level:
            return

        def role_exists(award: RoleAward):
            """Check to ensure the role associated with the :class:`RoleAward` still exists in the guild. If it does, it returns that discord role object for use"""
            role_obj = message.guild.get_role(award.role_id)
            if role_obj: return role_obj
            else: return False

        details = _next_level_details(member_data.level)
        next_level = int(details[0])
        next_level_xp = details[1]

        # if this results to True, they just leveled up
        if member_data.xp >= next_level_xp and member_data.level < next_level:
            
            # update the database and refresh member data with the new information
            await self._cursor.execute('UPDATE leaderboard SET member_xp = 0, member_level = ? WHERE member_id = ?', (next_level, member.id,))
            await self._connection.commit()
            updated_data = await self.get_data_for(member)

            # send the level up message
            if self.announce_level_up:
                
                # set the values for the level up announcement
                lua = self.level_up_announcement
                lua._author_mention = updated_data.mention
                lua._xp = updated_data.xp
                lua._total_xp = updated_data.total_xp
                lua._level = updated_data.level
                lua._rank = updated_data.rank
                announcement_message = lua._parse_message(lua.message)

                if lua.level_up_channel_id:
                    channel = message.guild.get_channel(lua.level_up_channel_id)
                    if channel:
                        await channel.send(announcement_message, **lua._send_kwargs)
                    else:
                        raise LevelUpChannelNotFound(lua.level_up_channel_id)
                else:
                    await message.channel.send(announcement_message, **lua._send_kwargs)
            

            # check if there is a role award (could be :class:`None`) for the new level, if so, apply it
            if self.awards:
                role_award = [ra for ra in self.awards if ra.level_requirement == updated_data.level]
                if role_award:
                    role_award = role_award[0]
                    if self.stack_awards:
                        role_obj: Role = role_exists(award=role_award)
                        if role_obj:
                            await member.add_roles(role_obj)
                        else:
                            raise AwardedRoleNotFound(role_award.role_id)
                    else:
                        last_award: RoleAward = self._get_last_award(role_award)
                        role_to_remove: Role = role_exists(award=last_award)
                        role_to_add: Role = role_exists(award=role_award)
                        
                        if not role_to_remove:  raise AwardedRoleNotFound(last_award.role_id)
                        if not role_to_add:     raise AwardedRoleNotFound(role_award.role_id)

                        if last_award == role_award:
                            await member.add_roles(role_to_add)
                        else:
                            await member.add_roles(role_to_add)
                            await member.remove_roles(role_to_remove)
    
    def _handle_amount_param(self, arg):
        """Simple check to ensure the proper types are being used for parameter "amount" in method :meth:`DiscordLevelingSystem.award_xp()`"""
        if isinstance(arg, (int, list)):
            if isinstance(arg, int):
                if arg <= 0 or arg > 100:
                    raise DiscordLevelingSystemError('Parameter "amount" can only be a value from 1-100')
            else:
                # ensures there are only 2 values in the list
                if len(arg) != 2:
                    raise DiscordLevelingSystemError('Parameter "amount" list must only have two values')
                
                # ensures all values in the list are of type int
                for item in arg:
                    if type(item) is not int:
                        raise DiscordLevelingSystemError('Parameter "amount" list, all values must be of type int')
                
                # ensures all values in the list are >= 1 and <= 100
                for item in arg:
                    if item <= 0 or item > 100:
                        raise DiscordLevelingSystemError('Parameter "amount" list, all values can only be from 1-100')
        else:
            raise DiscordLevelingSystemError(f'Parameter "amount" expected int or list, got {arg.__class__.__name__}')
    
    @db_file_exists
    @leaderboard_exists
    @verify_leaderboard_integrity
    async def award_xp(self, *, amount: Union[int, List[int]]=[15, 25], message: Message, refresh_name: bool=True):
        """|coro| Give XP to the member that sent a message

        Parameters
        ----------
        amount: Union[:class:`int`, :class:`List[int]`]
            The amount of XP to award to the member per message. Must be from 1-100. Can be a list with a minimum and maximum length of two. If :param:`amount` is a list of two integers, it will randomly
            pick a number in between those numbers including the numbers provided. Example:
        
        message: :class:`discord.Message`
            A :class:`discord.Message` object
        
        refresh_name: :class:`bool`
            (optional) Everytime the member sends a message, check if their name still matches the name in the database. If it doesn't match, update the database to match their current name. It is
            suggested to leave this as `True` so the database can always have the most up-to-date record (defaults to `True`)

        Raises
        ------
        - `DatabaseFileNotFound`: The database file was not found
        - `LeaderboardNotFound`: Table "leaderboard" in the database file is missing
        - `ImproperLeaderboard`: Leaderboard table was altered. Components changed or deleted
        - `NotConnected`: Attempted to use a method that requires a connection to a database file
        """
        if message.guild is None or self._determine_no_xp(message) or message.author.bot:
            return
        else:
            self._handle_amount_param(arg=amount)
            if isinstance(amount, list):
                amount = random.randint(amount[0], amount[1])
            bucket = self._cooldown.get_bucket(message)
            on_cooldown = bucket.update_rate_limit()

            if not on_cooldown:
                new_member_query = """
                    INSERT INTO leaderboard
                    VALUES (?, ?, ?, ?, ?)
                """
                existing_member_query = """
                    UPDATE leaderboard
                    SET member_xp = member_xp + ?, member_total_xp = member_total_xp + ?
                    WHERE member_id = ?
                """
                member = message.author
                async with self._connection.execute('SELECT * FROM leaderboard WHERE member_id = ?', (member.id,)) as cursor:
                    record = await cursor.fetchone()
                    if record:
                        await cursor.execute(existing_member_query, (amount, amount, member.id))
                        await self._connection.commit()
                    else:
                        await cursor.execute(new_member_query, (member.id, str(member), 0, amount, amount))
                        await self._connection.commit()

                    await self._handle_level_up(message)
                    if refresh_name: await self._refresh_name(message)
