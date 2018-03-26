from collections import namedtuple
from datetime import datetime
import fnmatch
import logging
import operator
from pprint import pprint
import re
import unittest


__version__ = '0.2.0'


LOG_FORMAT = "%(asctime)-15s %(levelname)-8s %(name)-5s [%(filename)s:%(lineno)d]: %(message)s"

# Setup logging
root_logger = logging.getLogger()
log_handler = logging.StreamHandler()
formatter = logging.Formatter(LOG_FORMAT)
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.DEBUG)
root_logger.addHandler(log_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger('dictquery')


class DQException(Exception):
    pass


class DQSyntaxError(DQException, SyntaxError):
    pass


class DQEvalutionError(DQException):
    pass


class DQKeyError(DQException, KeyError):
    pass


Token = namedtuple('Token', ['type', 'value'])


token_specification = [
    ('NUMBER',      r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'),
    ('BOOLEAN',     r'TRUE|FALSE'),
    ('NONE',        r'NULL|NONE|NIL'),
    ('NOW',         r'NOW'),
    ('STRING',      r'{}|{}'.format(
                        r'"([^"\\]*|\\["\\bfnrt\/]|\\u[0-9a-f]{4})*"',
                        r"'([^'\\]*|\\['\\bfnrt\/]|\\u[0-9a-f]{4})*'")),
    ('KEY',         r'`([^`\\]*|\\[`\\bfnrt\/]|\\u[0-9a-f]{4})*`'),
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
    ('LIKE',        r'LIKE'),
    ('MATCH',       r'MATCH'),
    ('CONTAIN',     r'CONTAIN'),
    ('IN',          r'IN'),
    ('OR',          r'OR'),
    ('AND',         r'AND'),
    ('NOT',         r'NOT'),
    ('COMMA',       r'\,'),
    ('REGEXP',      r'/.*(?<!\\)/'),
    ('WS',          r'[\n\s\t ]+'),
    ('MISMATCH',    r'.'),
]

tok_regex = re.compile(
    '|'.join('(?P<%s>%s)' % pair for pair in token_specification),
    re.IGNORECASE)

def gen_tokens(pattern, text, skip_ws=True):
    for match in pattern.finditer(text):
        tok_type = match.lastgroup
        if tok_type == 'MISMATCH':
            raise DQSyntaxError("Unexpected character at pos %d" % match.start())
        if tok_type == 'WS' and skip_ws:
            continue
        value = match.group(tok_type)
        yield Token(tok_type, value)


"""
Grammar

statement :=  expression {OR|AND expression}

expression := NOT expr | expr

expr := ( statement )
        | key != | <= | >= | < | > | == value
        | key IN ARRAY | STRING
        | key LIKE STRING
        | key MATCH STRING
        | key CONTAIN ARRAY | STRING

key := STRING
value := ARRAY | BOOLEAN | STRING | NUMBER | NONE | NOW | REGEXP
array := [ ] | [ value {, value} ]
"""

operations_map = {
    'CONTAIN': operator.contains,
    'EQUAL': operator.eq,
    'NOTEQUAL': operator.ne,
    'LT': operator.lt,
    'GT': operator.gt,
    'LTE': operator.le,
    'GTE': operator.ge
}

BINARY_OPS = ('IN', 'NOTEQUAL', 'LTE', 'GTE', 'LT', 'GT',
              'EQUAL', 'MATCH', 'LIKE', 'CONTAIN')
VALUES = ('BOOLEAN', 'NUMBER', 'NONE', 'NOW', 'STRING', 'REGEXP')


class DictQueryParser:

    def parse(self, text):
        self.tokens = gen_tokens(tok_regex, text)
        self.tok = None
        self.nexttok = None
        self._advance()
        return self.statement()


    def _advance(self):
        self.tok, self.nexttok = self.nexttok, next(self.tokens, None)


    def _accept(self, toktype):
        if not self.nexttok:
            return False

        if isinstance(toktype, (list, tuple)):
            if self.nexttok.type in toktype:
                self._advance()
                return True

        elif self.nexttok.type == toktype:
            self._advance()
            return True

        return False


    def _expect(self, toktype):
        if not self._accept(toktype):
            raise DQSyntaxError("Expected token %s" % str(toktype))


    def statement(self):
        leftval = self.expression()
        while self._accept(('OR', 'AND')):
            op = self.tok
            rightval = self.expression()
            leftval = (op, leftval, rightval)
        return leftval


    def expression(self):
        if self._accept('NOT'):
            return (self.tok, self.expr())
        return self.expr()


    def expr(self):
        if self._accept('LPAR'):
            obj = self.statement()
            self._expect('RPAR')
            return obj

        leftval = self.value()
        if self._accept('MATCH'):
            op = self.tok
            self._expect('REGEXP')
            rightval = self.tok
            return (op, leftval, rightval)

        if self._accept('LIKE'):
            op = self.tok
            self._expect('STRING')
            rightval = self.tok
            return (op, leftval, rightval)

        if self._accept(BINARY_OPS):
            op = self.tok
            rightval = self.value()
            return (op, leftval, rightval)
        return leftval


    def value(self):
        if self._accept('KEY'):
            return Token('KEY', self.tok.value[1:-1])

        if self._accept(VALUES):
            return self.tok

        if self.nexttok.type == 'LBRACKET':
            return self.array()

        raise DQSyntaxError("Can't parse expr")


    def array(self):
        self._expect('LBRACKET')
        result = []
        if self._accept('RBRACKET'):
            return result
        result.append(self.value())
        while self._accept('COMMA'):
            result.append(self.value())
        self._expect('RBRACKET')
        return Token('ARRAY', result)


def get_dict_value(query_dict, dict_key, use_nested_keys=True,
                   key_separator='.', raise_keyerror=False):
    result = []
    if use_nested_keys:
        keys = dict_key.split(key_separator)
    else:
        keys = [dict_key]
    dict_stack = [(query_dict, keys)]
    while dict_stack:
        current_value, current_keys = dict_stack.pop()
        if len(current_keys) == 1:
            try:
                result.append(current_value[current_keys[0]])
            except KeyError:
                pass
            continue

        if not isinstance(current_value, (list, tuple, dict)):
            continue

        if isinstance(current_value, dict):
            try:
                next_value = current_value[current_keys[0]]
            except KeyError:
                continue
            if isinstance(next_value, dict):
                dict_stack.append((next_value, current_keys[1:]))
                continue
            elif isinstance(next_value, (list, tuple)):
                current_value = next_value
            else:
                continue

        if isinstance(current_value, (list, tuple)):
            for item in current_value:
                if not isinstance(item, dict):
                    continue
                dict_stack.append((item, current_keys[1:]))

    if not result and raise_keyerror:
        raise DQKeyError("Key '%s' not found" % dict_key)
    return result


def _eval_token(token, case_sensitive=True):
    if token.type == 'NUMBER':
        return float(token.value)
    if token.type == 'BOOLEAN':
        return token.value.lower() == 'true'
    if token.type == 'STRING':
        return token.value[1:-1] if case_sensitive else token.value[1:-1].lower()
    if token.type == 'NONE':
        return None
    if token.type == 'NOW':
        return datetime.utcnow()
    if token.type == 'REGEXP':
        if case_sensitive:
            return re.compile(token.value[1:-1])
        else:
            return re.compile(token.value[1:-1], re.IGNORECASE)
    if token.type == 'ARRAY':
        arr = []
        for arr_tok in token.value:
            arr.append(_eval_token(arr_tok, case_sensitive))
        return arr
    raise DQEvalutionError('Unexpected token {} {}'.format(token.type, token.value))


class DictQuery:
    def __init__(self, query, use_nested_keys=True,
                 key_separator='.', case_sensitive=True,
                 raise_keyerror=False):
        self.query = query
        self.use_nested_keys = use_nested_keys
        self.key_separator = key_separator
        self.raise_keyerror = raise_keyerror
        self.case_sensitive = case_sensitive
        self.parser = DictQueryParser()
        self.ast = self.parser.parse(self.query)
        logger.debug("AST: {}".format(self.ast))


    def _get_dict_value(self, query_dict, dict_key):
        return get_dict_value(
            query_dict, dict_key, self.use_nested_keys,
            self.key_separator, self.raise_keyerror)

    def _calc_expr(self, query_dict, op, left, right):
        left_value, right_value = None, None
        if left.type != 'KEY' and right.type != 'KEY':
            raise DQEvalutionError("Requared dict key in expression")
        if left.type == 'KEY':
            left_value = self._get_dict_value(query_dict, left.value)
        else:
            left_value = _eval_token(left, self.case_sensitive)

        if right.type == 'KEY':
            right_value = self._get_dict_value(query_dict, right.value)
        else:
            right_value = _eval_token(right, self.case_sensitive)

        result = []
        if left.type == 'KEY' and right.type == 'KEY':
            for left_item in left_value:
                for right_item in right_value:
                    result.append(operations_map[op.type](left_item, right_item))
            return any(result)

        for item in (left_value if left.type == 'KEY' else right_value):
            if isinstance(item, str) and not self.case_sensitive:
                item = item.lower()
            left_item = item if left.type == 'KEY' else left_value
            right_item = item if right.type == 'KEY' else right_value

            if op.type in operations_map:
                result.append(operations_map[op.type](left_item, right_item))
            if op.type == 'IN':
                result.append((left_item in right_item))
            if op.type == 'LIKE':
                result.append(fnmatch.fnmatchcase(left_item, right_item))
            if op.type == 'MATCH':
                result.append(right_item.match(left_item) is not None)
        return any(result)


    def _eval_expr(self, query_dict, tree):
        if isinstance(tree, Token) and tree.type == 'KEY':
            dict_value = self._get_dict_value(query_dict, tree.value)
            return any(dict_value)

        op_token = tree[0]
        if op_token.type == 'NOT':
            return (not self._eval_expr(query_dict, tree[1]))

        if op_token.type in BINARY_OPS:
            return self._calc_expr(query_dict, op_token, tree[1], tree[2])

        if op_token.type == 'AND':
            leftval = self._eval_expr(query_dict, tree[1])
            if not leftval:
                return False
            rightval = self._eval_expr(query_dict, tree[2])
            if not rightval:
                return False
            return True

        if op_token.type == 'OR':
            leftval = self._eval_expr(query_dict, tree[1])
            if leftval:
                return True
            rightval = self._eval_expr(query_dict, tree[2])
            return bool(rightval)


    def match(self, query_dict):
        return self._eval_expr(query_dict, self.ast)


def compile(query, use_nested_keys=True,
            key_separator='.', case_sensitive=True,
            raise_keyerror=False):
    return DictQuery(
        query, use_nested_keys=use_nested_keys,
        key_separator=key_separator, case_sensitive=case_sensitive,
        raise_keyerror=raise_keyerror)


def match(query_dict, query):
    dq = DictQuery(query)
    return dq.match(query_dict)


def filter(data, query, use_nested_keys=True,
           key_separator='.', case_sensitive=True,
           raise_keyerror=False):
    dq = DictQuery(
        query, use_nested_keys=use_nested_keys,
        key_separator=key_separator, case_sensitive=case_sensitive,
        raise_keyerror=raise_keyerror)
    for item in data:
        if not dq.match(item):
            continue
        yield item
