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

from functools import wraps
import os

import aiosqlite

from .errors import DatabaseFileNotFound, LeaderboardNotFound, ImproperLeaderboard, NotConnected

def _return_self(args: list):
    """Return the class instance"""
    return args[0]

def db_file_exists(func):
    """Ensure the database file exists before performing any operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        instance = _return_self(args)
        if not any([instance._database_file_path, instance._connection]):
            raise DatabaseFileNotFound('The database file was not found. Did you forget to connect to it first using "DiscordLevelingSystem.connect_to_database_file()"?')
        
        def path_exists() -> bool:
            """This is only to check if the path is :class:`None`. If it is, it raises a `TypeError`, and the traceback the user sees doesn't make any sense. This produces a cleaner
            traceback, and if the path does exist, return `True`"""
            nonlocal instance
            try:
                existance = os.path.exists(instance._database_file_path)
            except TypeError:
                raise NotConnected
            else:
                return existance

        # if it gets this far, that means :meth:`DiscordLevelingSystem.connect_to_file()` was ran, the connection
        # object was set, the file path was stored, and that file does end in ".db". This checks it again because
        # this check applies to various other methods that need to verify that the file exists. Using :meth:`DiscordLevelingSystem.connect_to_file()`
        # has its own check just like this, and that method will only be called to setup the initial connection
        if path_exists():
            if os.path.isfile(instance._database_file_path) and instance._database_file_path.endswith('.db'):
                return await func(*args, **kwargs)
            else:
                raise DatabaseFileNotFound('A file ending with ".db" was not found')
        else:
            raise DatabaseFileNotFound(f'The file {instance._database_file_path!r} does not exist')
    return wrapper

def leaderboard_exists(func):
    """Ensures the "leaderboard" table exists in the "DiscordLevelingSystem.db" file"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        instance = _return_self(args)
        try:
            async with instance._connection.execute('SELECT * FROM leaderboard'):
                pass
        except aiosqlite.OperationalError:
            raise LeaderboardNotFound
        else:
            return await func(*args, **kwargs)
    return wrapper

def verify_leaderboard_integrity(func):
    """Ensures the values of the leaderboard table are the values needed in order to operate on said table
    
        .. changes::
            v0.0.2
                Added pragma for guild_id
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        PRAGMA_LAYOUT = [
            (0, 'guild_id', 'INT', 1, None, 0),
            (1, 'member_id', 'INT', 1, None, 0),
            (2, 'member_name', 'TEXT', 1, None, 0),
            (3, 'member_level', 'INT', 1, None, 0),
            (4, 'member_xp', 'INT', 1, None, 0),
            (5, 'member_total_xp', 'INT', 1, None, 0)
        ]
        instance = _return_self(args)
        async with instance._connection.execute('PRAGMA table_info(leaderboard)') as cursor:
            current_layout = await cursor.fetchall()
            if current_layout == PRAGMA_LAYOUT:
                return await func(*args, **kwargs)
            else:
                raise ImproperLeaderboard
    return wrapper
