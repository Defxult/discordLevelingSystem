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

from typing import Union

from discord import AllowedMentions, Embed

from .errors import DiscordLevelingSystemError

default_message = '[$mention], you are now **level [$level]!**'
default_mentions = AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)
class LevelUpAnnouncement:
    """A helper class for setting up messages that are sent when someone levels up
    
    Parameters
    ----------
    message: Union[:class:`str`, :class:`discord.Embed`]
        (optional) The message that is sent when someone levels up (defaults to `"<mention>, you are now **level <level>!**"`)
    
    level_up_channel_id: :class:`int`
        (optional) The text channel ID where all level up messages will be sent. If :class:`None`, the level up message will be sent in the channel where they sent the message (defaults to :class:`None`)
    
    allowed_mentions: :class:`discord.AllowedMentions`
        (optional) The :class:`discord.AllowedMentions` object that is used to determine who can be pinged in the level up message (defaults to `AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)`)
    
    tts: :class:`bool`
        (optional) When the level up message is sent, have discord read the level up message aloud (defaults to `False`)
    
    delete_after: :class:`float`
        (optional) Delete the level up message after an x amount of seconds (defaults to :class:`None`)
    
    
    Attributes
    ----------
    - `message`
    - `level_up_channel_id`
    
    Class Attributes
    ----------------
    The below class attributes are used to implement the values that are associated with the members level up information
    - `LevelUpAnnouncement.AUTHOR_MENTION`: The member that leveled up
    - `LevelUpAnnouncement.XP`: The members current XP amount
    - `LevelUpAnnouncement.TOTAL_XP`: The members current total XP amount
    - `LevelUpAnnouncement.LEVEL`: The members current level
    - `LevelUpAnnouncement.RANK`: The members current rank
    
    Example
    -------
    ```
    announcement = LevelUpAnnouncement(message=f'{LevelUpAnnouncement.AUTHOR_MENTION} you leveled up! Your rank is now {LevelUpAnnouncement.RANK}')
    lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)
    ```
    
        .. changes::
            v0.0.2
                Now accepts embeds as the message parameter
    """
    AUTHOR_MENTION = '[$mention]'
    XP = '[$xp]'
    TOTAL_XP = '[$total_xp]'
    LEVEL = '[$level]'
    RANK = '[$rank]'

    def __init__(self, message: Union[str, Embed]=default_message, level_up_channel_id: int=None, allowed_mentions: AllowedMentions=default_mentions, tts: bool=False, delete_after: float=None):
        self.message = message
        self.level_up_channel_id = level_up_channel_id
        self._author_mention = None
        self._xp = None
        self._total_xp = None
        self._level = None
        self._rank = None
        self._send_kwargs = {
            'allowed_mentions' : allowed_mentions,
            'tts' : tts,
            'delete_after' : delete_after
        }
    
    def _convert_markdown(self, to_convert: str) -> str:
        """Convert the markdown text to the value it represents

            .. added:: v0.0.2
        """
        markdowns = {
            LevelUpAnnouncement.AUTHOR_MENTION : self._author_mention,
            LevelUpAnnouncement.XP : self._xp,
            LevelUpAnnouncement.TOTAL_XP : self._total_xp,
            LevelUpAnnouncement.LEVEL : self._level,
            LevelUpAnnouncement.RANK : self._rank
        }
        for mrkd, value in markdowns.items():
            to_convert = to_convert.replace(mrkd, str(value))
        return to_convert
    
    def _parse_message(self, message: Union[str, Embed]) -> Union[str, Embed]:
        """
            .. changes::
                v0.0.2
                    Added handling for embed announcements
                    Moved markdown conversion to its own method (`_convert_markdown`)
        """
        if isinstance(message, str):
            return self._convert_markdown(message)
        
        elif isinstance(message, Embed):
            embed = message
            new_dict_embed = {}
            temp_formatted = []

            def e_dict_to_converted(embed_value: dict):
                """If the value from the :class:`discord.Embed` dictionary contains a :class:`LevelUpAnnouncement` markdown, convert the markdown to it's 
                associated value and return it for use
                    
                    .. added:: v0.0.2
                """
                temp_dict = {}
                for key, value in embed_value.items():
                    if not isinstance(value, str):
                        temp_dict[key] = value
                    else:
                        temp_dict[key] = self._convert_markdown(value)
                else:
                    return temp_dict.copy()

            for embed_key, embed_value in embed.to_dict().items():
                # description, title, etc...
                if isinstance(embed_value, str):
                    new_dict_embed[embed_key] = self._convert_markdown(embed_value)
                
                # field inline values or discord.Color
                elif isinstance(embed_value, (int, bool)):
                    new_dict_embed[embed_key] = embed_value
                
                # footer, author, etc...
                elif isinstance(embed_value, dict):
                    new_dict_embed[embed_key] = e_dict_to_converted(embed_value)
                
                # fields
                elif isinstance(embed_value, list):
                    for item in embed_value: # "item" is a dict
                        temp_formatted.append(e_dict_to_converted(item))
                    new_dict_embed[embed_key] = temp_formatted.copy()
                    temp_formatted.clear()

            return Embed.from_dict(new_dict_embed)

        else:
            raise DiscordLevelingSystemError(f'Level up announcement parameter "message" expected a str or discord.Embed, got {message.__class__.__name__}')