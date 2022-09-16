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
from .rank_card import RankCard

__source__ = 'https://github.com/Defxult/discordLevelingSystem'
__all__ = (
    'LevelUpAnnouncement',
    'DiscordLevelingSystem',
    'MemberData',
    'RoleAward',
    'RankCard'
)
