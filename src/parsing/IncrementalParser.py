import re

class IncrementalParser:

    def __init__(self, text):
        self._text = text.strip()

    def text(self):
        return self._text

    '''
    Given a RegEx pattern returns a list containing the text captured by the capture groups, in order.
    Returns None if the pattern did not match anything, otherwise returns a list which might contain None
    if an optional capture group did not match.
    
    All the text that matches the pattern is then removed for the next call to 'extract'.
    '''
    def extract(self, pattern):
        res = re.search(pattern, self._text)
        if res:
            matches = list(map(lambda x: res.group(x), range(1, len(res.groups()) + 1)))
            for match in matches:
                if match:
                    self._text = self._text.replace(match, '').strip()

            return matches
