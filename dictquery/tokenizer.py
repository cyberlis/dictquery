from collections import namedtuple
import re
from dictquery.exceptions import DQSyntaxError


Token = namedtuple('Token', ['type', 'value'])

token_specification = [
    ('NUMBER',      r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'),
    ('BOOLEAN',     r'TRUE|FALSE'),
    ('NONE',        r'NULL|NONE|NIL'),
    ('NOW',         r'NOW'),
    ('STRING',      r'{}|{}'.format(
                        r'"([^"\\]*|\\["\\bfnrt\/]|\\u[0-9a-f]{4})*"',
                        r"'([^'\\]*|\\['\\bfnrt\/]|\\u[0-9a-f]{4})*'")),
    ('LPAR',        r'\('),
    ('RPAR',        r'\)'),
    ('LBRACKET',    r'\['),
    ('RBRACKET',    r'\]'),
    ('NOTEQUAL',    r'\!=|\<\>'),
    ('EQUAL',       r'=='),
    ('LTE',         r'\<='),
    ('GTE',         r'\>='),
    ('LT',          r'\<'),
    ('GT',          r'\>'),
    ('LIKE',        r'[\s ]+LIKE[\s ]+'),
    ('MATCH',       r'[\s ]+MATCH[\s ]+'),
    ('CONTAINS',    r'[\s ]+CONTAINS[\s ]+|[\s ]+CONTAIN[\s ]+'),
    ('IN',          r'[\s ]+IN[\s ]+'),
    ('OR',          r'[\s ]+OR[\s ]+'),
    ('AND',         r'[\s ]+AND[\s ]+'),
    ('NOT',         r'NOT[\s ]+'),
    ('COMMA',       r'\,'),
    ('REGEXP',      r'/.*(?<!\\)/'),
    ('KEY',         r'[a-zA-Z_][a-zA-Z0-9_]*|`([^`\\]*|\\[`\\bfnrt\/]|\\u[0-9a-f]{4})*`'),
    ('WS',          r'[\n\s\t ]+'),
    ('MISMATCH',    r'.'),
]

tok_regex = re.compile(
    '|'.join('(?P<%s>%s)' % pair for pair in token_specification),
    re.IGNORECASE)

def gen_tokens(text, skip_ws=True):
    for match in tok_regex.finditer(text):
        tok_type = match.lastgroup
        if tok_type == 'MISMATCH':
            raise DQSyntaxError("Unexpected character at pos %d" % match.start())
        if tok_type == 'WS' and skip_ws:
            continue
        value = match.group(tok_type)
        yield Token(tok_type, value)
