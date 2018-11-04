from datetime import datetime
import fnmatch
import operator
import re

from dictquery.exceptions import DQException, DQEvaluationError, DQValidationError
from dictquery.datavalue import query_value, DataQueryItem
from dictquery.parsers import (
    DataQueryParser, AndExpression, OrExpression, NotExpression,
    KeyExpression, VALUE_EXPRESSIONS)


class KeyExistenceValidatorVisitor:
    """Validates query to  have KEY literal"""
    def __init__(self, ast):
        self.ast = ast

    def evaluate(self):
        """Returns True if ast is valid"""
        if self.ast is None:
            return
        if isinstance(self.ast, VALUE_EXPRESSIONS):
            raise DQValidationError("Expected expression or key")
        self.ast.accept(self)
        return True

    def _get_binary_operands(self, expr):
        if not isinstance(expr.left, KeyExpression) and not isinstance(expr.right, KeyExpression):
            raise DQValidationError("Left or Right operand must be `KeyExpression`")
        return expr.left.accept(self), expr.right.accept(self)

    def visit_lt(self, expr):
        return self._get_binary_operands(expr)

    def visit_lte(self, expr):
        return self._get_binary_operands(expr)

    def visit_gt(self, expr):
        return self._get_binary_operands(expr)

    def visit_gte(self, expr):
        return self._get_binary_operands(expr)

    def visit_equal(self, expr):
        return self._get_binary_operands(expr)

    def visit_notequal(self, expr):
        return self._get_binary_operands(expr)

    def visit_contains(self, expr):
        return self._get_binary_operands(expr)

    def visit_in(self, expr):
        return self._get_binary_operands(expr)

    def visit_match(self, expr):
        return self._get_binary_operands(expr)

    def visit_like(self, expr):
        return self._get_binary_operands(expr)

    def visit_key(self, expr):
        return expr

    def visit_number(self, expr):
        return expr

    def visit_boolean(self, expr):
        return expr

    def visit_string(self, expr):
        return expr

    def visit_now(self, expr):
        return expr

    def visit_none(self, expr):
        return expr

    def visit_regexp(self, expr):
        return expr

    def visit_array(self, expr):
        return expr

    def visit_not(self, expr):
        if isinstance(expr.value, VALUE_EXPRESSIONS):
            raise DQValidationError(
                "NOT must be used with AND, OR, KEY or with Binary Operations, not values")
        return expr.value.accept(self)

    def visit_and(self, expr):
        if isinstance(expr.left, VALUE_EXPRESSIONS) or isinstance(expr.right, VALUE_EXPRESSIONS):
            raise DQValidationError('AND operands must be KEY or Operations, not values')
        return expr.left.accept(self), expr.right.accept(self)

    def visit_or(self, expr):
        if isinstance(expr.left, VALUE_EXPRESSIONS) or isinstance(expr.right, VALUE_EXPRESSIONS):
            raise DQValidationError('OR operands must be KEY or Operations, not values')
        return expr.left.accept(self), expr.right.accept(self)


class DataQueryVisitor:
    """Default data visitor. Evaluates to `True` or `False`. Checks if `data` satisfies `ast`"""
    def __init__(self, ast, use_nested_keys=True,
                 key_separator='.', case_sensitive=True,
                 raise_keyerror=False):
        self.use_nested_keys = use_nested_keys
        self.key_separator = key_separator
        self.raise_keyerror = raise_keyerror
        self.case_sensitive = case_sensitive
        self.ast = ast
        self.data = None

    def _get_dict_value(self, dict_key):
        if self.data is None:
            raise DQException('self.data is not specified')
        return query_value(
            self.data, dict_key, self.use_nested_keys,
            self.key_separator, self.raise_keyerror)

    def evaluate(self, data):
        if self.ast is None:
            return False
        try:
            self.data = data
            result = bool(self.ast.accept(self))
        finally:
            self.data = None
        return result

    def match(self, data):
        return self.evaluate(data)

    def visit_lt(self, expr):
        return operator.lt(expr.left.accept(self), expr.right.accept(self))

    def visit_lte(self, expr):
        return operator.le(expr.left.accept(self), expr.right.accept(self))

    def visit_gt(self, expr):
        return operator.gt(expr.left.accept(self), expr.right.accept(self))

    def visit_gte(self, expr):
        return operator.ge(expr.left.accept(self), expr.right.accept(self))

    def visit_equal(self, expr):
        return operator.eq(expr.left.accept(self), expr.right.accept(self))

    def visit_notequal(self, expr):
        return operator.ne(expr.left.accept(self), expr.right.accept(self))

    def visit_contains(self, expr):
        return operator.contains(expr.left.accept(self), expr.right.accept(self))

    def visit_in(self, expr):
        return operator.contains(expr.right.accept(self), expr.left.accept(self))

    def visit_match(self, expr):
        left = expr.left.accept(self)
        # if dictvalue.DataQueryItem class or class with the same interface
        if hasattr(left, 'match'):
            return  left.match(expr.right.accept(self))
        return expr.right.accept(self).match(left) is not None

    def visit_like(self, expr):
        left = expr.left.accept(self)
        # if dictvalue.DataQueryItem class or class with the same interface
        if hasattr(left, 'like'):
            return  left.like(expr.right.accept(self))
        return fnmatch.fnmatchcase(expr.left.accept(self), expr.right.accept(self))

    def visit_key(self, expr):
        return DataQueryItem(
            key=expr.value,
            values=self._get_dict_value(expr.value),
            case_sensitive=self.case_sensitive,)

    def visit_number(self, expr):
        return float(expr.value)

    def visit_boolean(self, expr):
        return expr.value.lower() == 'true'

    def visit_string(self, expr):
        return expr.value if self.case_sensitive else expr.value.lower()

    def visit_now(self, expr):
        return datetime.utcnow()

    def visit_none(self, expr):
        return None

    def visit_regexp(self, expr):
        if self.case_sensitive:
            return re.compile(expr.value)
        else:
            return re.compile(expr.value, re.IGNORECASE)

    def visit_array(self, expr):
        result = []
        for item in expr.value:
            result.append(item.accept(self))
        return result

    def visit_not(self, expr):
        return not bool(expr.value.accept(self))

    def visit_and(self, expr):
        leftval = bool(expr.left.accept(self))
        if not leftval:
            return leftval
        rightval = bool(expr.right.accept(self))
        return leftval and rightval

    def visit_or(self, expr):
        leftval = bool(expr.left.accept(self))
        if leftval:
            return leftval
        rightval = bool(expr.right.accept(self))
        return leftval or rightval


class MongoQueryVisitor:
    """Visitor converts `ast` to mongo query object"""
    def __init__(self, ast, case_sensitive=True):
        self.case_sensitive = case_sensitive
        self.ast = ast

    def _get_binary_operands(self, expr):
        if not isinstance(expr.left, KeyExpression):
            raise DQEvaluationError("Left operand must be `KeyExpression`")
        return expr.left.accept(self), expr.right.accept(self)

    def _get_and_or_operands(self, expr):
        if isinstance(expr.left, VALUE_EXPRESSIONS) or isinstance(expr.right, VALUE_EXPRESSIONS):
            raise DQEvaluationError("For `AND`, `OR` operands must be expression or key")

        if isinstance(expr.left, KeyExpression):
            left = {expr.left.accept(self): {'$exists': True}}
        else:
            left = expr.left.accept(self)

        if isinstance(expr.right, KeyExpression):
            right = {expr.right.accept(self): {'$exists': True}}
        else:
            right = expr.right.accept(self)
        return left, right

    def evaluate(self):
        if self.ast is None:
            return {}
        if isinstance(self.ast, KeyExpression):
            return {self.ast.accept(self): {'$exists': True}}
        if isinstance(self.ast, VALUE_EXPRESSIONS):
            raise DQEvaluationError("Expected expression or key")
        return self.ast.accept(self)

    def visit_lt(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$lt': right}}

    def visit_lte(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$lte': right}}

    def visit_gt(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$gt': right}}

    def visit_gte(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$gte': right}}

    def visit_equal(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$eq': right}}

    def visit_notequal(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$ne': right}}

    def visit_contains(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$eq': right}}

    def visit_in(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$in': right}}

    def visit_match(self, expr):
        left, right = self._get_binary_operands(expr)
        return {left: {'$regex': right}}

    def visit_like(self, expr):
        left, right = self._get_binary_operands(expr)
        right = fnmatch.translate(right)
        pattern =  re.compile(right, 0 if self.case_sensitive else re.IGNORECASE)
        return {left: {'$regex': pattern}}

    def visit_key(self, expr):
        return expr.value

    def visit_number(self, expr):
        return float(expr.value)

    def visit_boolean(self, expr):
        return expr.value.lower() == 'true'

    def visit_string(self, expr):
        return expr.value if self.case_sensitive else expr.value.lower()

    def visit_now(self, expr):
        return datetime.utcnow()

    def visit_none(self, expr):
        return None

    def visit_regexp(self, expr):
        if self.case_sensitive:
            return re.compile(expr.value)
        else:
            return re.compile(expr.value, re.IGNORECASE)

    def visit_array(self, expr):
        result = []
        for item in expr.value:
            result.append(item.accept(self))
        return result

    def visit_not(self, expr):
        # not (x and y) = not x or not y
        if isinstance(expr.value, AndExpression):
            result = OrExpression(
                left=NotExpression(expr.value.left),
                right=NotExpression(expr.value.right)).accept(self)
        elif isinstance(expr.value, OrExpression):
            val = expr.value.accept(self)
            result = {'$nor': val['$or']}
        elif isinstance(expr.value, KeyExpression):
            result = {expr.value.accept(self): {'$exists': False}}
        else:
            result = {}
            val = expr.value.accept(self)
            for key, value in list(val.items()):
                if '$regex' in value:
                    result[key] = {'$not': value['$regex']}
                else:
                    result[key] = {'$not': value}
        return result

    def visit_and(self, expr):
        left, right = self._get_and_or_operands(expr)
        return {'$and': [left, right]}

    def visit_or(self, expr):
        left, right = self._get_and_or_operands(expr)
        return {'$or': [left, right]}
