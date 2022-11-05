"""
Grammar

orstatement :=  andstatement {OR andstatement}
andstatement :=  expression {AND expression}

expression := NOT expr | expr

expr := ( orstatement )
        | key != | <= | >= | < | > | == value | key
        | key IN ARRAY | STRING | key
        | key LIKE STRING
        | key MATCH STRING
        | key CONTAINS ARRAY | STRING

key := STRING
value := ARRAY | BOOLEAN | STRING | NUMBER | NONE | NOW | REGEXP
array := [ ] | [ value {, value} ]
"""
from dictquery.exceptions import DQSyntaxError
from dictquery.tokenizer import Token, gen_tokens


BINARY_OPS = ('IN', 'NOTEQUAL', 'LTE', 'GTE', 'LT', 'GT',
              'EQUAL', 'MATCH', 'LIKE', 'CONTAINS')
VALUES = ('BOOLEAN', 'NUMBER', 'NONE', 'NOW', 'STRING', 'REGEXP')


class LiteralExpression:
    def __init__(self, value):
        self.value = value

    def accept(self, visitor):
        return visitor.visit_literal(self)


class UnaryExpression:
    def __init__(self, value):
        self.value = value

    def accept(self, visitor):
        return visitor.visit_unary(self)


class BinaryExpression:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def accept(self, visitor):
        return visitor.visit_binary(self)


class NumberExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_number(self)


class BooleanExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_boolean(self)


class NoneExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_none(self)


class NowExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_now(self)


class StringExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_string(self)


class KeyExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_key(self)


class RegexpExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_regexp(self)


class ArrayExpression(LiteralExpression):
    def accept(self, visitor):
        return visitor.visit_array(self)


class InExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_in(self)


class EqualExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_equal(self)


class NotEqualExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_notequal(self)


class MatchExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_match(self)


class LikeExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_like(self)


class ContainsExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_contains(self)


class LTExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_lt(self)


class LTEExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_lte(self)


class GTExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_gt(self)


class GTEExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_gte(self)


class AndExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_and(self)


class OrExpression(BinaryExpression):
    def accept(self, visitor):
        return visitor.visit_or(self)


class NotExpression(UnaryExpression):
    def accept(self, visitor):
        return visitor.visit_not(self)


token_to_class = {
    'NUMBER': NumberExpression,
    'BOOLEAN': BooleanExpression,
    'NONE': NoneExpression,
    'NOW': NowExpression,
    'STRING': StringExpression,
    'KEY': KeyExpression,
    'ARRAY': ArrayExpression,
    'REGEXP': RegexpExpression,
    'EQUAL': EqualExpression,
    'NOTEQUAL': NotEqualExpression,
    'LT': LTExpression,
    'LTE': LTEExpression,
    'GT': GTExpression,
    'GTE': GTEExpression,
    'LIKE': LikeExpression,
    'MATCH': MatchExpression,
    'CONTAINS': ContainsExpression,
    'IN': InExpression,
    'OR': OrExpression,
    'AND': AndExpression,
    'NOT': NotExpression,
}

VALUE_EXPRESSIONS = (
    NumberExpression, BooleanExpression, NoneExpression,
    NowExpression, StringExpression, ArrayExpression,
    RegexpExpression)


class DataQueryParser:
    def parse(self, query):
        query = query.strip()
        if not query:
            return None
        self.tokens = gen_tokens(query)
        self.tok = None
        self.nexttok = None
        self._advance()
        return self.orstatement()

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

    def orstatement(self):
        leftval = self.andstatement()
        while self._accept('OR'):
            op = token_to_class[self.tok.type]
            rightval = self.andstatement()
            leftval = op(leftval, rightval)
        return leftval

    def andstatement(self):
        leftval = self.expression()
        while self._accept('AND'):
            op = token_to_class[self.tok.type]
            rightval = self.expression()
            leftval = op(leftval, rightval)
        return leftval

    def expression(self):
        if self._accept('NOT'):
            return token_to_class[self.tok.type](self.expr())
        return self.expr()

    def expr(self):
        if self._accept('LPAR'):
            obj = self.orstatement()
            self._expect('RPAR')
            return obj

        leftval = self.value()
        if self._accept('MATCH'):
            op = token_to_class[self.tok.type]
            self._expect('REGEXP')
            rightval = token_to_class['REGEXP'](self.tok.value[1:-1])
            return op(leftval, rightval)

        if self._accept('LIKE'):
            op = token_to_class[self.tok.type]
            self._expect('STRING')
            rightval = token_to_class['STRING'](self.tok.value[1:-1])
            return op(leftval, rightval)

        if self._accept('IN'):
            op = token_to_class[self.tok.type]
            rightval = self.value()
            valid_types = (StringExpression, ArrayExpression, KeyExpression)
            if not isinstance(rightval, valid_types):
                raise DQSyntaxError("Expected STRING, ARRAY, KEY")
            return op(leftval, rightval)

        if self._accept(BINARY_OPS):
            op = token_to_class[self.tok.type]
            rightval = self.value()
            return op(leftval, rightval)
        elif self.nexttok is not None and \
                self.nexttok.type not in ('OR', 'AND', 'RPAR'):
            raise DQSyntaxError(
                "Expected binary operation %s" % ', '.join(BINARY_OPS))
        return leftval

    def value(self):
        if self._accept('KEY'):
            value = self.tok.value[1:-1] if self.tok.value[0] == "`" else self.tok.value
            return token_to_class['KEY'](value)

        if self._accept('STRING'):
            return token_to_class['STRING'](self.tok.value[1:-1])

        if self._accept('REGEXP'):
            return token_to_class['REGEXP'](self.tok.value[1:-1])

        if self._accept(VALUES):
            return token_to_class[self.tok.type](self.tok.value)

        if self._accept('LBRACKET'):
            return self.array()
        raise DQSyntaxError("Can't parse expr")

    def array(self):
        result = []
        if self._accept('RBRACKET'):
            return token_to_class['ARRAY'](result)
        result.append(self.value())
        while self._accept('COMMA'):
            result.append(self.value())
        self._expect('RBRACKET')
        return token_to_class['ARRAY'](result)
