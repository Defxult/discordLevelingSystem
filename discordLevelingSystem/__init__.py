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
    - `version` Current version of the library
    - `releasetype` Either "final" (the PyPI version) or "pre-release" (the GitHub version)
    - `patch` The last significant bug fix

    >>> print(discordLevelingSystem.version_info())
    """
    from collections import namedtuple
    VersionInfo = namedtuple('VersionInfo', ['version', 'releasetype', 'patch'])
    return VersionInfo(version='1.1.0', releasetype='pre-release', patch='1a')

__source__ = 'https://github.com/Defxult/discordLevelingSystem'
__all__ = (
    'LevelUpAnnouncement',
    'DiscordLevelingSystem',
    'MemberData',
    'RoleAward'
)
