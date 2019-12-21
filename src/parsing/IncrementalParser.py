import re


class IncrementalParser:

    def __init__(self, text):
        self._text = text.strip()

    def text(self):
        return self._text

    def extract(self, pattern):
        """
        Given a RegEx pattern returns a list containing the text captured by the capture groups, in order.
        Returns None if the pattern did not match anything, otherwise returns a list which might contain None
        if an optional capture group did not match.

        All the text that matches the pattern is then removed for the next call to 'extract'.
        """
        res = re.match(pattern, self._text)
        if res:
            matches = [res.group(x) for x in range(1, len(res.groups()) + 1)]
            for match in matches:
                if match:
                    self._text = self._text.replace(match, '', 1).strip()

            return matches
