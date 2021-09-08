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

from collections import Counter
from typing import Dict, List, Optional, Union

from .errors import ImproperRoleAwardOrder, RoleAwardError


class RoleAward:
    """Represents the role that will be awarded to the member upon meeting the XP requirement

    Parameters
    ----------
    role_id: :class:`int`
        ID of the role that is to be awarded
    
    level_requirement: :class:`int`
        What level is required for a member to be awarded the role
    
    role_name: Optional[:class:`str`]
        A name you can set for the award. Nothing is done with this value, it is used for visual identification purposes only
    
    Attributes
    ----------
    - `role_id`
    - `level_requirement`
    - `role_name`
    - `mention`
    """

    __slots__ = ('role_id', 'level_requirement', 'role_name', 'mention')

    def __init__(self, role_id: int, level_requirement: int, role_name: Optional[str]=None):
        self.role_id = role_id
        self.level_requirement = level_requirement
        
        # v0.0.2
        self.role_name = role_name
        
        # v1.0.0
        self.mention = f'<@&{role_id}>'

    def __repr__(self):
        return f'<RoleAward role_id={self.role_id} level_requirement={self.level_requirement} role_name={self.role_name!r}>'
    
    def __eq__(self, value):
        if isinstance(value, RoleAward):
            return all([self.role_id == value.role_id, self.level_requirement == value.level_requirement])
        else:
            return False
    
    @staticmethod
    def _check(awards: Union[Dict[int, List['RoleAward']], None]):
        if awards:
            if not isinstance(awards, (dict, type(None))): raise RoleAwardError(f'"awards" expected dict or None, got {awards.__class__.__name__}')

            # ensure all dict keys and values are of the correct type
            for key, value in awards.items():
                if not isinstance(key, int): raise RoleAwardError('When setting the "awards" dict, all keys must be of type int')
                if not isinstance(value, list): raise RoleAwardError('When setting the "awards" dict, all values must be of type list')
                if isinstance(value, list) and not all([isinstance(role_award, RoleAward) for role_award in value]): raise RoleAwardError('When setting the "awards" dict, all values in the list must be of type RoleAward')
            else:
                RoleAward._guild_id_check(awards.keys())
                for award in awards.values():
                    RoleAward._role_id_check(award)
                    RoleAward._level_req_check(award)
                    RoleAward._verify_duplicate_awards(award)
                    RoleAward._verify_awards_integrity(award)
    
    @staticmethod
    def _guild_id_check(guild_ids: List[int]):
        """|static method| Ensures all guild IDs are unique
        
            .. added:: v0.0.2
        """
        counter = Counter(guild_ids)
        if max(counter.values()) != 1:
            raise RoleAwardError('When assigning role awards, all guild IDs must be unique')

    @staticmethod
    def _role_id_check(awards: List['RoleAward']):
        """|static method| Ensure all IDs are unique"""
        role_id_counter = Counter([award.role_id for award in awards])
        if max(role_id_counter.values()) != 1:
            raise RoleAwardError("There cannot be duplicate ID numbers when using role awards. All ID's must be unique")
    
    @staticmethod
    def _level_req_check(awards: List['RoleAward']):
        """|static method| Ensures all level requirements/level requirements values are unique and greater than zero"""
        # ensure all level requirements are unique
        lvl_req_counter = Counter([award.level_requirement for award in awards])
        if max(lvl_req_counter.values()) != 1:
            raise RoleAwardError("There cannot be duplicate level requirements when using role awards. All level requirements must be unique")
        
        # ensure all level requirement values are greater than zero
        lvl_reqs = [award.level_requirement for award in awards if award.level_requirement <= 0]
        if lvl_reqs:
            raise RoleAwardError('All level requirement values must greater than zero')
    
    @staticmethod
    def _verify_duplicate_awards(awards: List['RoleAward']):
        """|static method| Only used in the :class:`DiscordLevelingSystem` constructor. Ensures all :class:`RoleAward` objects submitted are unique"""
        object_ids = [id(obj) for obj in awards]
        counter = Counter(object_ids)
        if max(counter.values()) != 1:
            raise RoleAwardError('There cannot be duplicate role award objects when setting the "awards"')
    
    @staticmethod
    def _verify_awards_integrity(awards: List['RoleAward']):
        """|static method| Only used in the :class:`DiscordLevelingSystem` constructor. Ensures the awards submitted to its constructor are in ascending order according to their level requirement"""
        previous_level_requirement = 0
        for award in awards:
            if award.level_requirement < previous_level_requirement:
                raise ImproperRoleAwardOrder('When setting "awards", role award level requirements must be in ascending order')
            previous_level_requirement = award.level_requirement
