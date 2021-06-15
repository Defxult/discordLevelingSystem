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

class DiscordLevelingSystemError(Exception):
    """Base exception for :class:`DiscordLevelingSystem`"""
    def __init__(self, message: str):
        super().__init__(message)

class RoleAwardError(DiscordLevelingSystemError):
    """Base exception for :class:`DiscordLevelingSystem`"""
    def __init__(self, message: str):
        super().__init__(message)

class ConnectionFailure(DiscordLevelingSystemError):
    """Attempted to connect to the database file when the event loop is already running"""
    def __init__(self):
        super().__init__('Cannot connect to database file because the event loop is already running')

class NotConnected(DiscordLevelingSystemError):
    """Attempted to use a method that requires a connection to a database file"""
    def __init__(self):
        super().__init__('You attempted to use a method that requires a database connection. Did you forget to connect to the database file first using "DiscordLevelingSystem.connect_to_database_file()"?')

class DatabaseFileNotFound(DiscordLevelingSystemError):
    """The database file was not found"""
    def __init__(self, message):
        super().__init__(message)

class ImproperRoleAwardOrder(RoleAwardError):
    """When setting the awards list in the :class:`DiscordLevelingSystem` constructor, :attr:`RoleAward.level_requirement` was not greater than the last level"""
    def __init__(self, message):
        super().__init__(message)

class ImproperLeaderboard(DiscordLevelingSystemError):
    """Raised when the leaderboard table in the database file does not have the correct settings"""
    def __init__(self):
        super().__init__('It seems like the leaderboard table was altered. Components changed or deleted')

class LeaderboardNotFound(DiscordLevelingSystemError):
    """When accessing the "DiscordLevelingSystem.db" file, the table "leaderboard" was not found inside that file"""
    def __init__(self):
        super().__init__('When accessing the "DiscordLevelingSystem.db" file, the table "leaderboard" was not found inside that file. Use DiscordLevelingSystem.create_database_file() to create the file')

class FailSafe(DiscordLevelingSystemError):
    """Raised when the expected value for a method that can cause massive unwanted results, such as :meth:`DiscordLevelingSystem.wipe_database()`, was set to `False`"""
    def __init__(self):
        super().__init__('Failsafe condition raised due to default argument. "intentional" was set to False')
        