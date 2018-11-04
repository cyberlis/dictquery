# -*- coding: utf-8 -*-
from datetime import datetime
import unittest

from dictquery.parsers import DataQueryParser
from dictquery.visitors import DataQueryVisitor


class TestDataQueryVisitor(unittest.TestCase):
    def test_visit_number(self):
        parser = DataQueryParser()
        ast = parser.parse('12')
        dqv = DataQueryVisitor(ast)
        self.assertEqual(ast.accept(dqv), 12)

    def test_visit_none(self):
        parser = DataQueryParser()
        ast = parser.parse('NONE')
        dqv = DataQueryVisitor(ast)
        self.assertEqual(ast.accept(dqv), None)

    def test_visit_now(self):
        parser = DataQueryParser()
        ast = parser.parse('NOW')
        dqv = DataQueryVisitor(ast)
        self.assertIsInstance(ast.accept(dqv), datetime)

    def test_visit_bool(self):
        parser = DataQueryParser()
        ast1 = parser.parse('TRUE')
        ast2 = parser.parse('FALSE')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_string(self):
        parser = DataQueryParser()
        ast = parser.parse('"hello"')
        dqv = DataQueryVisitor(ast)
        self.assertEqual(ast.accept(dqv), 'hello')

    def test_visit_array(self):
        parser = DataQueryParser()
        ast = parser.parse('[12, "hello"]')
        dqv = DataQueryVisitor(ast)
        self.assertEqual(ast.accept(dqv), [12, 'hello'])

    def test_visit_key(self):
        parser = DataQueryParser()
        ast1 = parser.parse('hello')
        ast2 = parser.parse('world')
        ast3 = parser.parse('`qwerty.x`')
        dqv = DataQueryVisitor(ast1)
        dqv.data = {'hello': 'world', 'qwerty': {'x': 42}}
        self.assertEqual(ast1.accept(dqv).values, ["world"])
        self.assertEqual(ast2.accept(dqv).values, [])
        self.assertEqual(ast3.accept(dqv).values, [42])

    def test_visit_regexp(self):
        parser = DataQueryParser()
        ast = parser.parse(r'/[abcd]+\d\s*finish/')
        dqv = DataQueryVisitor(ast)
        self.assertEqual(ast.accept(dqv).pattern, r'[abcd]+\d\s*finish')

    def test_visit_equal(self):
        parser = DataQueryParser()
        ast1 = parser.parse('12 == 12')
        ast2 = parser.parse('12 == 3')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_notequal(self):
        parser = DataQueryParser()
        ast1 = parser.parse('12 != 3')
        ast2 = parser.parse('12 != 12')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_lt(self):
        parser = DataQueryParser()
        ast1 = parser.parse('12 < 23')
        ast2 = parser.parse('12 < 3')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_lte(self):
        parser = DataQueryParser()
        ast1 = parser.parse('12 <= 23')
        ast2 = parser.parse('12 <= 3')
        ast3 = parser.parse('12 <= 12')

        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)
        self.assertEqual(ast3.accept(dqv), True)

    def test_visit_gt(self):
        parser = DataQueryParser()
        ast1 = parser.parse('23 > 12')
        ast2 = parser.parse('3 > 12')

        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_gte(self):
        parser = DataQueryParser()
        ast1 = parser.parse('23 >= 12')
        ast2 = parser.parse('3 >= 12')
        ast3 = parser.parse('12 >= 12')

        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)
        self.assertEqual(ast3.accept(dqv), True)

    def test_visit_in(self):
        parser = DataQueryParser()
        ast1 = parser.parse('"hello" IN "hello world"')
        ast2 = parser.parse('"hello1" IN "hello world"')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_contains(self):
        parser = DataQueryParser()
        ast1 = parser.parse('"hello world" CONTAINS "world"')
        ast2 = parser.parse('"hello world" CONTAINS "hello1"')

        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_like(self):
        parser = DataQueryParser()
        ast1 = parser.parse('"hello world" LIKE "*world"')
        ast2 = parser.parse('"hello world" LIKE "hello?world"')
        ast3 = parser.parse('"hello world" LIKE "*admin*"')

        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), True)
        self.assertEqual(ast3.accept(dqv), False)

    def test_visit_match(self):
        parser = DataQueryParser()
        ast1 = parser.parse(r'"hello world" MATCH /.*world.*/')
        ast2 = parser.parse(r'"hello world" MATCH /hello1/')
        dqv = DataQueryVisitor(ast1)
        self.assertEqual(ast1.accept(dqv), True)
        self.assertEqual(ast2.accept(dqv), False)

    def test_visit_empty(self):
        parser = DataQueryParser()
        ast = parser.parse('')
        dqv = DataQueryVisitor(ast)
        self.assertFalse(dqv.evaluate({}))


if __name__ == '__main__':
    unittest.main()
