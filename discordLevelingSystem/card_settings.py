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

from io import BufferedIOBase
from os import PathLike
from typing import Optional, Union


class Settings:
    """
    Represents the settings for the rank card

    Parameters
    ----------
    background: :class:`Union[PathLike, BufferedIOBase, str]`
        The background image for the rank card. This can be a path to a file or a file-like object in `rb` mode or URL

    bar_color: :class:`Optional[str]`
        The color of the XP bar. This can be a hex code or a color name. Default is `white`
    
    text_color: :class:`Optional[str]`
        The color of the text. This can be a hex code or a color name. Default is `white`

    Attributes
    ----------
    - `background`
    - `bar_color`
    - `text_color`
    """

    __slots__ = ('background', 'bar_color', 'text_color')

    def __init__(
        self,
        backgroud: Union[PathLike, BufferedIOBase, str],
        bar_color: Optional[str] = 'white',
        text_color: Optional[str] = 'white'
    ) -> None:
        self.background = backgroud
        self.bar_color = bar_color
        self.text_color = text_color
    
    def to_dict(self) -> dict:
        return {key : getattr(self, key) for key in self.__class__.__slots__}