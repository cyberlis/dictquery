# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import unittest

from dictquery.exceptions import DQKeyError, DQSyntaxError
from dictquery.datavalue import query_value
from dictquery.parsers import (
    DataQueryParser, NumberExpression, BooleanExpression, NoneExpression,
    NowExpression, StringExpression, KeyExpression, ArrayExpression,
    RegexpExpression, EqualExpression, NotEqualExpression, LTExpression,
    LTEExpression, GTExpression, GTEExpression, LikeExpression,
    MatchExpression, ContainsExpression, InExpression, OrExpression,
    AndExpression, NotExpression,)
from dictquery.tokenizer import Token
from dictquery.visitors import DataQueryVisitor
import dictquery as dq

class TestMatchDict(unittest.TestCase):
    def test_get_dict_value(self):
        self.assertEqual(
            query_value({'user': 'cyberlis'}, 'user'),
            ['cyberlis']
        )
        self.assertEqual(
            query_value({'user': {'firstname': 'cyberlis'}}, 'user.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            query_value({'user': {'fullname': {'firstname': 'cyberlis'}}},
                           'user.fullname.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            query_value({'users': [{'firstname': 'cyberlis'},
                                      {'firstname': 'rinagorsha'}]},
                           'users.firstname'),
            ['cyberlis', 'rinagorsha']
        )
        self.assertEqual(
            query_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users.fullname.firstname'),
            ['cyberlis', 'rinagorsha']
        )
        self.assertEqual(
            query_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'odd_item': 'odd_value'},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users.fullname.firstname'),
            ['cyberlis', 'rinagorsha']
        )
        self.assertEqual(
            query_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      23, 'hello', 'world']},
                           'users.fullname.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            query_value({'users': [{'fullname': {'lastname': 'cyberlis'}},]},
                           'users.fullname.firstname'),
            []
        )
        self.assertEqual(
            query_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'odd_item': 'odd_value'},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users/fullname/firstname', key_separator='/'),
            ['cyberlis', 'rinagorsha']
        )
        with self.assertRaises(DQKeyError):
            query_value({'user.username': 'cyberlis'},
                            'user.username',
                            raise_keyerror=True,
                            use_nested_keys=True)

        self.assertEqual(
            query_value({'user.username': 'cyberlis'},
                           'user.username',
                           raise_keyerror=True,
                           use_nested_keys=False),
            ['cyberlis']
        )
        with self.assertRaises(DQKeyError):
            query_value({'users': [{'fullname': {'lastname': 'cyberlis'}},]},
                           'users.fullname.firstname', raise_keyerror=True)

    def test_not(self):
        self.assertTrue(dq.match({'age': 18}, 'NOT `age` == 12'))

    def test_equal(self):
        self.assertTrue(dq.match({'age': 18}, '`age` == 18'))
        self.assertFalse(dq.match({'age': 18}, '`age` == 12'))

    def test_notequal(self):
        self.assertTrue(dq.match({'age': 18}, '`age` != 12'))
        self.assertFalse(dq.match({'age': 18}, '`age` != 18'))

    def test_lt(self):
        self.assertTrue(dq.match({'age': 18}, '`age` < 20'))
        self.assertFalse(dq.match({'age': 18}, '`age` < 17'))
        self.assertFalse(dq.match({'age': 18}, '`age` < 18'))

    def test_gt(self):
        self.assertTrue(dq.match({'age': 18}, '`age` > 12'))
        self.assertFalse(dq.match({'age': 18}, '`age` > 20'))
        self.assertFalse(dq.match({'age': 18}, '`age` > 18'))

    def test_lte(self):
        self.assertTrue(dq.match({'age': 18}, '`age` <= 20'))
        self.assertTrue(dq.match({'age': 18}, '`age` <= 18'))
        self.assertFalse(dq.match({'age': 18}, '`age` <= 17'))

    def test_gte(self):
        self.assertTrue(dq.match({'age': 18}, '`age` >= 12'))
        self.assertTrue(dq.match({'age': 18}, '`age` >= 18'))
        self.assertFalse(dq.match({'age': 18}, '`age` >= 20'))

    def test_in(self):
        self.assertTrue(dq.match({'role': 'admin'}, '`role` in ["admin", "observer"]'))
        self.assertTrue(dq.match({'age': 18}, '`age` in [12, 56, 78, 18, 90, 20]'))
        self.assertFalse(dq.match({'role': 'user'}, '`role` in ["admin", "observer"]'))

    def test_like(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(dq.match(data, '`username` LIKE "*admin*"'))
        self.assertTrue(dq.match(data, '`username` LIKE "test*"'))
        self.assertTrue(dq.match(data, '`username` LIKE "test?admin?username"'))
        self.assertFalse(dq.match(data, '`username` LIKE "test"'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, '`username` LIKE 23'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, '"test" LIKE `username`'))

    def test_match(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(dq.match(data, r'`username` MATCH /.*admin.*/'))
        self.assertTrue(dq.match(data, r'`username` MATCH /test.*/'))
        self.assertTrue(dq.match({'age': '98'}, r'`age` MATCH /\d+/'))
        self.assertFalse(dq.match(data, r'`username` MATCH /qwerty/'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, r'/\d+/ MATCH `username`'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, r'`username` MATCH "test"'))

    def test_contains(self):
        self.assertTrue(dq.match({'roles': ['admin', 'observer']}, '`roles` CONTAINS "admin"'))
        self.assertFalse(dq.match({'roles': ['admin', 'observer']}, '`roles` CONTAINS "user"'))

    def test_now(self):
        utcnow = datetime.utcnow()
        self.assertTrue(
            dq.match({'time': utcnow - timedelta(hours=1)},
            "`time` < NOW"))
        self.assertFalse(
            dq.match({'time': utcnow - timedelta(hours=1)},
            "`time` == NOW"))

    def test_only_keys(self):
        self.assertTrue(dq.match({'username': 'cyberlis', 'age': 26}, "`username` AND `age`"))
        self.assertTrue(dq.match({'username': 'cyberlis', 'age': 26}, "`username`"))
        self.assertFalse(dq.match({'username': 'cyberlis', 'age': 0}, "`age`"))
        self.assertFalse(dq.match({'username': 'cyberlis'}, "`age`"))
        self.assertFalse(dq.match({'username': 'cyberlis', 'age': 0}, "`username` AND `age`"))

    def test_pars(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(dq.match(data, "(`a`) AND (`c`)"))
        self.assertTrue(dq.match(data, "((`a`) AND (`c`))"))
        self.assertTrue(dq.match(data, "((((`a`)) AND ((`c`))))"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, "(`a`) AND (`c`"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, ")`a` AND `c`"))

    def test_eval_order(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(dq.match(data, "`a` == 1 OR `c` == 0"))
        self.assertFalse(dq.match(data, "`a` == 0 AND `c` == 1"))
        self.assertTrue(dq.match(data, "`a` == 0 AND `c` == 1 OR `z` == 0"))
        self.assertFalse(dq.match(data, "`a` == 0 AND (`c` == 1 OR `z` == 0)"))

    def test_case_sensitive(self):
        data = {'username': 'CybeRLiS'}
        dq_case_sensitive = dq.compile("`username` == 'cyberlis'", case_sensitive=True)
        dq_case_insensitive = dq.compile("`username` == 'cyberlis'", case_sensitive=False)
        self.assertFalse(dq_case_sensitive.match(data))
        self.assertTrue(dq_case_insensitive.match(data))
        dq_cis_in = dq.compile(
            "`username` IN ['cybeRLIS', 'rinagorhs']",
            case_sensitive=False)
        self.assertTrue(dq_cis_in.match(data))
        dq_cs_match = dq.compile(r"`username` MATCH /cyberlis/", case_sensitive=True)
        dq_cis_match = dq.compile(r"`username` MATCH /cyberlis/", case_sensitive=False)
        self.assertFalse(dq_cs_match.match(data))
        self.assertTrue(dq_cis_match.match(data))

        dq_cs_like = dq.compile(r"`username` LIKE 'cyberlis'", case_sensitive=True)
        dq_cis_like = dq.compile(r"`username` LIKE 'cyberlis'", case_sensitive=False)
        self.assertFalse(dq_cs_like.match(data))
        self.assertTrue(dq_cis_like.match(data))

    def test_key_order(self):
        data1 = {'age': 26}
        data2 = {'x': 12, 'y': 33}
        data3 = {'age': 12, 'friends': [
            {'age': 14},
            {'age': 16},
            {'age': 18},
            {'age': 20},
        ]}
        self.assertTrue(dq.match(data1, "26 == `age`"))
        self.assertTrue(dq.match(data1, "[23, 45, 12, 26] CONTAINS `age`"))
        self.assertTrue(dq.match(data1, "`age` == `age`"))
        self.assertTrue(dq.match(data2, "`x` < `y`"))
        self.assertFalse(dq.match(data2, "`x` >= `y`"))
        self.assertTrue(dq.match(data2, "`x` != `y`"))
        self.assertTrue(dq.match(data3, "`age` < `friends.age`"))


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
        ast1 = parser.parse('`hello`')
        ast2 = parser.parse('`world`')
        dqv = DataQueryVisitor(ast1)
        dqv.data = {'hello': 'world'}
        self.assertEqual(ast1.accept(dqv).values, ["world"])
        self.assertEqual(ast2.accept(dqv).values, [])

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
