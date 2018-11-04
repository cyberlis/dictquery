# -*- coding: utf-8 -*-
from datetime import datetime
import unittest

from dictquery.exceptions import DQValidationError
from dictquery.parsers import DataQueryParser
from dictquery.visitors import KeyExistenceValidatorVisitor


class TestKeyExistenceValidatorVisitor(unittest.TestCase):
    def test_visit_values(self):
        parser = DataQueryParser()
        ast = parser.parse('12')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('"hello"')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('NONE')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('True')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('NOW')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse(r'/\d+/')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

    def test_visit_and(self):
        parser = DataQueryParser()
        ast = parser.parse('12 AND 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello AND 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello == 3 AND 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello == 3 AND world > 3')
        visitor = KeyExistenceValidatorVisitor(ast)
        self.assertTrue(visitor.evaluate())

    def test_visit_or(self):
        parser = DataQueryParser()
        ast = parser.parse('12 OR 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello OR 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello == 3 OR 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello == 3 OR world > 3')
        visitor = KeyExistenceValidatorVisitor(ast)
        self.assertTrue(visitor.evaluate())

    def test_visit_not(self):
        parser = DataQueryParser()
        ast = parser.parse('NOT 3')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('NOT False')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('NOT hello')
        visitor = KeyExistenceValidatorVisitor(ast)
        self.assertTrue(visitor.evaluate())

    def test_visit_binary_ops(self):
        parser = DataQueryParser()
        ast = parser.parse('12 == 45')
        visitor = KeyExistenceValidatorVisitor(ast)
        with self.assertRaises(DQValidationError):
            visitor.evaluate()

        ast = parser.parse('hello == 3')
        visitor = KeyExistenceValidatorVisitor(ast)
        self.assertTrue(visitor.evaluate())

        ast = parser.parse('3 == hello')
        visitor = KeyExistenceValidatorVisitor(ast)
        self.assertTrue(visitor.evaluate())


if __name__ == '__main__':
    unittest.main()
