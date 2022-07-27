"""
Discord Leveling System
~~~~~~~~~~~~~~~~~~~~~~~

A library to implement a leveling system into a discord bot. Contains features such as XP, level, ranks, and role awards.

:copyright: (c) 2021-present Defxult#8269
:license: MIT

"""

from .announcement import LevelUpAnnouncement
from .leveling_system import DiscordLevelingSystem
from .member_data import MemberData
from .role_awards import RoleAward


def version_info():
    """Shows the current version, release type, and patch of the library

    >>> print(discordLevelingSystem.version_info())
    """
    from typing import NamedTuple, Literal
    class VersionInfo(NamedTuple):
        major: int
        minor: int
        patch: int
        releaseLevel: Literal['alpha', 'beta', 'candidate', 'final']
        
        @property
        def _version(self) -> str:
            return f'{self.major}.{self.minor}.{self.patch}'

    return VersionInfo(major=1, minor=2, patch=0, releaseLevel='candidate')

__source__ = 'https://github.com/Defxult/discordLevelingSystem'
__all__ = (
    'LevelUpAnnouncement',
    'DiscordLevelingSystem',
    'MemberData',
    'RoleAward'
)
