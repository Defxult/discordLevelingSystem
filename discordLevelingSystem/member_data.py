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

class MemberData:
    """Represents a members record from the database converted to an object where each value from their record can be easily accessed. Used in coordination with :class:`DiscordLevelingSystem`

    Attributes
    ----------
    id_number: :class:`int`
        The members ID
        
    name: :class:`str`
        The members name

    level: :class:`int`
        The members level
        
    xp: :class:`int`
        The members xp

    total_xp: :class:`int`
        The members total xp

    rank: :class:`int`
        The members rank
    
    mention: :class:`str`
        The discord member mention string
    """

    __slots__ = ('id_number', 'name', 'level', 'xp', 'total_xp', 'rank', 'mention')

    def __init__(self, id_number: int, name: str, level: int, xp: int, total_xp: int, rank: int):
        self.id_number = id_number
        self.name = name
        self.level = level
        self.xp = xp
        self.total_xp = total_xp
        self.rank = rank
        self.mention = '<@%s>' % id_number
    
    def __repr__(self):
        return f'<MemberData id_number={self.id_number} name={self.name!r} level={self.level} xp={self.xp} total_xp={self.total_xp} rank={self.rank}>'
        