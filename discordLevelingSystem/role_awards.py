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

import collections
from typing import List

from .errors import RoleAwardError, ImproperRoleAwardOrder

class RoleAward:
    """Represents the role that will be awarded to the member upon meeting the XP requirement

    Attributes
    ----------
    role_id: :class:`int`
        ID of the role that is to be awarded
    
    level_requirement: :class:`int`
        What level is required for a member to be awarded the role
    """
    _level_container = []
    _role_id_container = []

    __slots__ = ('role_id', 'level_requirement', 'role_mention')

    def __init__(self, role_id: int, level_requirement: int):
        self.role_id = role_id
        self.level_requirement = level_requirement

        RoleAward._role_id_container.append(role_id)
        RoleAward._level_container.append(level_requirement)

        RoleAward._check_duplicate_ids()
        RoleAward._check_duplicate_lvl_req()

    def __repr__(self):
        return f'<RoleAward role_id={self.role_id} level_requirement={self.level_requirement}>'
    
    def __eq__(self, value):
        if isinstance(value, RoleAward):
            same_id = False
            same_lvl_req = False
            if self.role_id == value.role_id:
                same_id = True
            if self.level_requirement == value.level_requirement:
                same_lvl_req = True
            return all([same_id, same_lvl_req])
        else:
            return False
    
    @classmethod
    def _check_duplicate_ids(cls):
        """|class method| Ensure all IDs are unique"""
        counter = collections.Counter(cls._role_id_container)
        if max(counter.values()) != 1:
            raise RoleAwardError('There cannot be duplicate ID numbers when using role awards. All ID\'s must be unique')
    
    @classmethod
    def _check_duplicate_lvl_req(cls):
        """|class method| Ensure all level requirements are unique"""
        lvl_reqs = [lvl for lvl in cls._level_container if lvl <= 0]
        if len(lvl_reqs) > 0:
            raise RoleAwardError('Level requirement values must greater than zero')
        
        counter = collections.Counter(cls._level_container)
        if max(counter.values()) != 1:
            raise RoleAwardError('There cannot be duplicate level requirements when using role awards. All level requirements must be unique')

    @staticmethod
    def _verify_duplicate_awards(awards: List['RoleAward']):
        """|static method| Only used in the :class:`DiscordLevelingSystem` constructor. Ensures all :class:`RoleAward` objects submitted are unique"""
        if awards:
            object_ids = [id(obj) for obj in awards]
            counter = collections.Counter(object_ids)
            if max(counter.values()) != 1:
                raise RoleAwardError('There cannot be duplicate role award objects when setting the "awards" parameter in the DiscordLevelingSystem constructor')
    
    @staticmethod
    def _verify_awards_integrity(awards: List['RoleAward']):
        """|static method| Only used in the :class:`DiscordLevelingSystem` constructor. Ensures the awards submitted to its constructor are in ascending order according to their level requirement"""
        if awards:
            previous_level_requirement = 0
            for award in awards:
                if award.level_requirement < previous_level_requirement:
                    raise ImproperRoleAwardOrder('When setting the "awards" parameter in the DiscordLevelingSystem constructor, role award level requirements must be in ascending order')
                previous_level_requirement = award.level_requirement
