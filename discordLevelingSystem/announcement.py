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

from collections.abc import Sequence
from typing import ClassVar, Optional, Union

from discord import AllowedMentions, Embed, Member as DMember

from .errors import DiscordLevelingSystemError

default_message = '[$mention], you are now **level [$level]!**'
default_mentions = AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)


class AnnouncementMemberGuild:
    """Helper class for :class:`AnnouncementMember`
    
        .. added:: v1.1.0 (moved from :class:`AnnouncementMember`, was just :class:`Guild`)
    """
    icon_url: ClassVar[str] = '[$g_icon_url]'
    id: ClassVar[str] = '[$g_id]'
    name: ClassVar[str] = '[$g_name]'

class AnnouncementMember:
    """Helper class for :class:`LevelUpAnnouncement`
    
        .. added:: v0.0.2
        .. changes::
            v1.1.0
                Replaced the guild class. Added it as a variable instead (Guild class is now separate)
                Added :attr:`display_avatar_url`
                Added :attr:`banner_url`
    """
    avatar_url: ClassVar[str] = '[$avatar_url]'
    banner_url: ClassVar[str] = '[$banner_url]'
    created_at: ClassVar[str] = '[$created_at]'
    default_avatar_url: ClassVar[str] = '[$default_avatar_url]'
    discriminator: ClassVar[str] = '[$discriminator]'
    display_avatar_url: ClassVar[str] = '[$display_avatar_url]'
    display_name: ClassVar[str] = '[$display_name]'
    id: ClassVar[str] = '[$id]'
    joined_at: ClassVar[str] = '[$joined_at]'
    mention: ClassVar[str] = '[$mention]'
    name: ClassVar[str] = '[$name]'
    nick: ClassVar[str] = '[$nick]'
    
    Guild: ClassVar[AnnouncementMemberGuild] = AnnouncementMemberGuild

class LevelUpAnnouncement:
    """A helper class for setting up messages that are sent when someone levels up
    
    Parameters
    ----------
    message: Union[:class:`str`, :class:`discord.Embed`]
        The message that is sent when someone levels up (defaults to `"<mention>, you are now **level <level>!**"`)
    
    level_up_channel_ids: Optional[Sequence[:class:`int`]]
        The text channel IDs where all level up messages will be sent for each server. If :class:`None`, the level up message will be sent in the channel where they sent the message
    
    allowed_mentions: :class:`discord.AllowedMentions`
        The :class:`discord.AllowedMentions` object that is used to determine who can be pinged in the level up message (defaults to `AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)`)
    
    tts: :class:`bool`
        When the level up message is sent, have discord read the level up message aloud
    
    delete_after: Optional[:class:`float`]
        Delete the level up message after an x amount of seconds
    
    Attributes
    ----------
    - `message`
    - `level_up_channel_ids`
    
    Class Attributes
    ----------------
    The below class attributes are used to implement the values that are associated with the members level up information
    - `LevelUpAnnouncement.TOTAL_XP`: The members current total XP amount
    - `LevelUpAnnouncement.LEVEL`: The members current level
    - `LevelUpAnnouncement.RANK`: The members current rank
    
    You can access a reduced version of pycord's `discord.Member` object via the :class:`LevelUpAnnouncement.Member` attribute. That attribute (class) contains the following information
    about a member and the guild

    - `LevelUpAnnouncement.Member.avatar_url`
    - `LevelUpAnnouncement.Member.banner_url`
    - `LevelUpAnnouncement.Member.created_at`
    - `LevelUpAnnouncement.Member.default_avatar_url`
    - `LevelUpAnnouncement.Member.discriminator`
    - `LevelUpAnnouncement.Member.display_avatar_url`
    - `LevelUpAnnouncement.Member.display_name`
    - `LevelUpAnnouncement.Member.id`
    - `LevelUpAnnouncement.Member.joined_at`
    - `LevelUpAnnouncement.Member.mention`
    - `LevelUpAnnouncement.Member.name`
    - `LevelUpAnnouncement.Member.nick`
    - `LevelUpAnnouncement.Member.Guild.icon_url`
    - `LevelUpAnnouncement.Member.Guild.id`
    - `LevelUpAnnouncement.Member.Guild.name`
    
    Example
    -------
    ```
    announcement = LevelUpAnnouncement(message=f'{LevelUpAnnouncement.Member.mention} you leveled up! Your rank is now {LevelUpAnnouncement.RANK}')
    lvl = DiscordLevelingSystem(..., level_up_announcement=announcement)
    ```
    
        .. changes::
            v0.0.2
                Now accepts embeds as the message parameter
                Removed :attr:`LevelUpAnnouncement.AUTHOR_MENTION`
                Removed :attr:`LevelUpAnnouncement.XP`
                Added :attr:`LevelUpAnnouncement.Member`
    """
    
    TOTAL_XP: ClassVar[str] = '[$total_xp]'
    LEVEL: ClassVar[str] = '[$level]'
    RANK: ClassVar[str] = '[$rank]'
    Member: ClassVar[AnnouncementMember] = AnnouncementMember

    def __init__(self, message: Union[str, Embed]=default_message, level_up_channel_ids: Optional[Sequence[int]]=None, allowed_mentions: AllowedMentions=default_mentions, tts: bool=False, delete_after: Optional[float]=None):
        self.message = message
        self.level_up_channel_ids = level_up_channel_ids
        self._total_xp: int = None
        self._level: int = None
        self._rank: int = None
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
            LevelUpAnnouncement.TOTAL_XP : self._total_xp,
            LevelUpAnnouncement.LEVEL : self._level,
            LevelUpAnnouncement.RANK : self._rank
        }
        for mrkd, value in markdowns.items():
            to_convert = to_convert.replace(mrkd, str(value))
        return to_convert
    
    def _convert_member_markdown(self, to_convert: str, message_author: DMember) -> str:
        """Convert the member markdown text to the value it represents

            .. added:: v0.0.2
            .. changes::
                v1.1.0
                    Updated `discord.Member.avatar_url` -> `discord.Member.avatar.url`
                    Updated `discord.Guild.icon_url` -> `discord.Guild.icon.url`
                    Added `discord.Member.display_avatar.url`
                    Added `discord.Member.banner.url`
        """
        markdowns = {
            # member
            AnnouncementMember.avatar_url : message_author.avatar.url,
            AnnouncementMember.banner_url : message_author.banner.url if message_author.banner is not None else None,
            AnnouncementMember.created_at : message_author.created_at,
            AnnouncementMember.default_avatar_url : message_author.default_avatar.url,
            AnnouncementMember.discriminator : message_author.discriminator,
            AnnouncementMember.display_avatar_url : message_author.display_avatar.url,
            AnnouncementMember.display_name : message_author.display_name,
            AnnouncementMember.id : message_author.id,
            AnnouncementMember.joined_at : message_author.joined_at,
            AnnouncementMember.mention : message_author.mention,
            AnnouncementMember.name : message_author.name,
            AnnouncementMember.nick : message_author.nick,

            # guild
            AnnouncementMember.Guild.icon_url : message_author.guild.icon.url,
            AnnouncementMember.Guild.id : message_author.guild.id,
            AnnouncementMember.Guild.name : message_author.guild.name
        }
        for mrkd, value in markdowns.items():
            to_convert = to_convert.replace(mrkd, str(value))
        return to_convert
    
    def _parse_message(self, message: Union[str, Embed], message_author: DMember) -> Union[str, Embed]:
        """
            .. changes::
                v0.0.2
                    Added handling for embed announcements
                    Added handling for LevelUpAnnouncement.Member markdowns
                    Moved markdown conversion to its own method (`_convert_markdown`)
        """
        if isinstance(message, str):
            partial = self._convert_markdown(message)
            full = self._convert_member_markdown(partial, message_author)
            return full
        
        elif isinstance(message, Embed):
            embed = message
            new_dict_embed = {}
            temp_formatted = []

            def e_dict_to_converted(embed_value: dict) -> dict:
                """If the value from the :class:`discord.Embed` dictionary contains a :class:`LevelUpAnnouncement` markdown, convert the markdown to it's 
                associated value and return it for use
                    
                    .. added:: v0.0.2
                """
                temp_dict = {}
                for key, value in embed_value.items():
                    if not isinstance(value, str):
                        temp_dict[key] = value
                    else:
                        partial = self._convert_markdown(value)
                        full = self._convert_member_markdown(partial, message_author)
                        temp_dict[key] = full
                else:
                    return temp_dict.copy()

            for embed_key, embed_value in embed.to_dict().items():
                # description, title, etc...
                if isinstance(embed_value, str):
                    partial = self._convert_markdown(embed_value)
                    full = self._convert_member_markdown(partial, message_author)
                    new_dict_embed[embed_key] = full
                
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
