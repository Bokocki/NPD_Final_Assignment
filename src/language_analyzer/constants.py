"""Constants used across the language analyzer."""

import string

# Valid Polish letters (lowercase only; comparisons should use .lower())
POLISH_LETTERS: frozenset[str] = frozenset("aąbcćdeęfghijklłmnńoópqrsśtuwvxyzźż")

# Punctuation characters that disqualify a dictionary line from mapping
PUNCT_FILTER: frozenset[str] = frozenset(string.punctuation) - frozenset("-")
