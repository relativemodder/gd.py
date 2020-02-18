"""Implement StringView for parsing command inputs.
This code is mostly copied from discord.py, with some adjustments.
(https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/view.py)
"""

from ..errors import CommandParseError
from ..typing import Optional

from ..utils.text_tools import make_repr

__all__ = ('StringView',)

# mapping of opening -> closing quotes
_quotes = {
    '`': '`', '"': '"', '‘': '’', '‚': '‛', '“': '”', '„': '‟', '⹂': '⹂',
    '「': '」', '『': '』', '〝': '〞', '﹁': '﹂', '﹃': '﹄', '＂': '＂',
    '｢': '｣', '«': '»', '‹': '›', '《': '》', '〈': '〉', "'": "'"
}
_all_quotes = set(_quotes.keys()) | set(_quotes.values())


class StringView:
    def __init__(self, string: str) -> None:
        self.index = 0
        self.string = string
        self.end = len(string)
        self.previous = 0

    def __repr__(self) -> str:
        info = {
            'index': self.index,
            'previous': self.previous,
            'end': self.end,
            'eof': self.eof
        }
        return make_repr(self, info)

    @property
    def current(self) -> Optional[str]:
        return None if self.eof else self.string[self.index]

    @property
    def eof(self) -> bool:
        return self.index >= self.end

    def undo(self) -> None:
        self.index = self.previous

    def skip_ws(self) -> bool:
        pos = 0
        while not self.eof:
            try:
                current = self.string[self.index + pos]
                if not current.isspace():
                    break
                pos += 1
            except IndexError:
                break

        self.previous = self.index
        self.index += pos
        return self.previous != self.index

    def skip_string(self, string: str) -> bool:
        strlen = len(string)
        if self.string[self.index:self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def read_rest(self) -> str:
        result = self.string[self.index:]
        self.previous = self.index
        self.index = self.end
        return result

    def read(self, n: int) -> str:
        result = self.string[self.index:self.index + n]
        self.previous = self.index
        self.index += n
        return result

    def get(self) -> Optional[str]:
        try:
            result = self.string[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1
        return result

    def get_word(self) -> str:
        pos = 0
        while not self.eof:
            try:
                current = self.string[self.index + pos]
                if current.isspace():
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.string[self.index:self.index + pos]
        self.index += pos
        return result

    def get_quoted_word(self) -> Optional[str]:
        current = self.current
        if current is None:
            return None

        close_quote = _quotes.get(current)
        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            _escaped_quotes = _all_quotes

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise CommandParseError('Expected closing quote: {}'.format(close_quote))
                return ('').join(result)

            # currently we accept strings in the format of 'hello world'
            # to embed a quote inside the string you must escape it: 'a \'world\''
            if current == '\\':
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise CommandParseError('Expected closing quote: {}'.format(close_quote))
                    # if we aren't then we just let it through
                    return ('').join(result)

                if next_char in _escaped_quotes:
                    # escaped quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            if not is_quoted and current in _all_quotes:
                # we aren't quoted
                raise CommandParseError('Unexpected quote: {}'.format(close_quote))

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or next_char.isspace()
                if not valid_eof:
                    raise CommandParseError('Invalid end of quoted string: {}'.format(next_char))

                # we're quoted so it's okay
                return ('').join(result)

            if current.isspace() and not is_quoted:
                # end of word found
                return ('').join(result)

            result.append(current)
