# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import unittest
from dictquery.parsers import (
    DataQueryParser, NumberExpression, BooleanExpression, NoneExpression,
    NowExpression, StringExpression, KeyExpression, ArrayExpression,
    RegexpExpression, EqualExpression, NotEqualExpression, LTExpression,
    LTEExpression, GTExpression, GTEExpression, LikeExpression,
    MatchExpression, ContainsExpression, InExpression, OrExpression,
    AndExpression, NotExpression,)


class TestVisitorParser(unittest.TestCase):
    def test_parse_empty(self):
        parser = DataQueryParser()
        result = parser.parse('')
        self.assertIsNone(result)

    def test_parse_key(self):
        parser = DataQueryParser()
        result = parser.parse('`key1`')
        self.assertIsInstance(result, KeyExpression)
        self.assertEqual(result.value, 'key1')

    def test_parse_number(self):
        parser = DataQueryParser()
        result = parser.parse('35')
        self.assertIsInstance(result, NumberExpression)
        self.assertEqual(result.value, '35')

    def test_parse_none(self):
        parser = DataQueryParser()
        result = parser.parse('NONE')
        self.assertIsInstance(result, NoneExpression)
        self.assertEqual(result.value, 'NONE')

    def test_parse_bool(self):
        parser = DataQueryParser()
        result = parser.parse('FALSE')
        self.assertIsInstance(result, BooleanExpression)
        self.assertEqual(result.value, 'FALSE')

    def test_parse_now(self):
        parser = DataQueryParser()
        result = parser.parse('NOW')
        self.assertIsInstance(result, NowExpression)
        self.assertEqual(result.value, 'NOW')

    def test_parse_regexp(self):
        parser = DataQueryParser()
        result = parser.parse(r'/\d+/')
        self.assertIsInstance(result, RegexpExpression)
        self.assertEqual(result.value, r'\d+')

    def test_parse_array(self):
        parser = DataQueryParser()
        result = parser.parse('[34, 11, "hello", "world"]')
        result_types = [
            NumberExpression,
            NumberExpression,
            StringExpression,
            StringExpression]
        for val, t in zip(result.value, result_types):
            self.assertIsInstance(val, t)

        self.assertEqual(result.value[0].value, '34')
        self.assertEqual(result.value[1].value, '11')
        self.assertEqual(result.value[2].value, 'hello')
        self.assertEqual(result.value[3].value, 'world')

    def test_parse_equal(self):
        parser = DataQueryParser()
        result = parser.parse('35 == 13')
        self.assertIsInstance(result, EqualExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_notequal(self):
        parser = DataQueryParser()
        result = parser.parse('35 != 13')
        self.assertIsInstance(result, NotEqualExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_in(self):
        parser = DataQueryParser()
        result = parser.parse('"hello" IN "hello world"')
        self.assertIsInstance(result, InExpression)
        self.assertEqual(result.left.value, 'hello')
        self.assertEqual(result.right.value, 'hello world')

    def test_parse_contains(self):
        parser = DataQueryParser()
        result = parser.parse('"hello world" CONTAINS "hello"')
        self.assertIsInstance(result, ContainsExpression)
        self.assertEqual(result.left.value, 'hello world')
        self.assertEqual(result.right.value, 'hello')

    def test_parse_like(self):
        parser = DataQueryParser()
        result = parser.parse('"hello world" LIKE "*hello"')
        self.assertIsInstance(result, LikeExpression)
        self.assertEqual(result.left.value, 'hello world')
        self.assertEqual(result.right.value, '*hello')

    def test_parse_match(self):
        parser = DataQueryParser()
        result = parser.parse(r'"hello world" MATCH /$hello.*/')
        self.assertIsInstance(result, MatchExpression)
        self.assertEqual(result.left.value, 'hello world')
        self.assertEqual(result.right.value, r'$hello.*')

    def test_parse_gt(self):
        parser = DataQueryParser()
        result = parser.parse('35 > 13')
        self.assertIsInstance(result, GTExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_gte(self):
        parser = DataQueryParser()
        result = parser.parse('35 >= 13')
        self.assertIsInstance(result, GTEExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_lt(self):
        parser = DataQueryParser()
        result = parser.parse('35 < 13')
        self.assertIsInstance(result, LTExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_lte(self):
        parser = DataQueryParser()
        result = parser.parse('35 <= 13')
        self.assertIsInstance(result, LTEExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_not(self):
        parser = DataQueryParser()
        result = parser.parse('NOT 45')
        self.assertIsInstance(result, NotExpression)
        self.assertEqual(result.value.value, '45')

    def test_parse_not_expr(self):
        parser = DataQueryParser()
        result = parser.parse('NOT "hello" IN "hello world"')
        self.assertIsInstance(result, NotExpression)
        self.assertEqual(result.value.left.value, 'hello')
        self.assertEqual(result.value.right.value, 'hello world')

    def test_parse_and(self):
        parser = DataQueryParser()
        result = parser.parse('35 AND 13')
        self.assertIsInstance(result, AndExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

    def test_parse_or(self):
        parser = DataQueryParser()
        result = parser.parse('35 OR 13')
        self.assertIsInstance(result, OrExpression)
        self.assertEqual(result.left.value, '35')
        self.assertEqual(result.right.value, '13')

if __name__ == '__main__':
    unittest.main()
