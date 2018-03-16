# -*- coding: utf-8 -*-

from dictquery import (
    Token, DictQueryParser, get_dict_value, DQKeyError, match, _eval_token)
import unittest


class TestMatchDict(unittest.TestCase):
    def test_parse_key(self):
        parser = DictQueryParser()
        self.assertEqual(parser.parse('"key1"'), Token('KEY', 'key1'))
        self.assertEqual(parser.parse("'key1'"), Token('KEY', 'key1'))

    def test_get_dict_value(self):
        self.assertEqual(
            get_dict_value({'user': 'cyberlis'}, 'user'),
            ['cyberlis']
        )
        self.assertEqual(
            get_dict_value({'user': {'firstname': 'cyberlis'}}, 'user.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            get_dict_value({'user': {'fullname': {'firstname': 'cyberlis'}}},
                           'user.fullname.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            get_dict_value({'users': [{'firstname': 'cyberlis'},
                                      {'firstname': 'rinagorsha'}]},
                           'users.firstname'),
            ['rinagorsha', 'cyberlis']
        )
        self.assertEqual(
            get_dict_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users.fullname.firstname'),
            ['rinagorsha', 'cyberlis']
        )
        self.assertEqual(
            get_dict_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'odd_item': 'odd_value'},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users.fullname.firstname'),
            ['rinagorsha', 'cyberlis']
        )
        self.assertEqual(
            get_dict_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      23, 'hello', 'world']},
                           'users.fullname.firstname'),
            ['cyberlis']
        )
        self.assertEqual(
            get_dict_value({'users': [{'fullname': {'lastname': 'cyberlis'}},]},
                           'users.fullname.firstname'),
            []
        )
        self.assertEqual(
            get_dict_value({'users': [{'fullname': {'firstname': 'cyberlis'}},
                                      {'odd_item': 'odd_value'},
                                      {'fullname': {'firstname': 'rinagorsha'}}]},
                           'users/fullname/firstname', key_separator='/'),
            ['rinagorsha', 'cyberlis']
        )
        with self.assertRaises(DQKeyError):
            get_dict_value({'users': [{'fullname': {'lastname': 'cyberlis'}},]},
                           'users.fullname.firstname', raise_keyerror=True)

    def test_not(self):
        self.assertTrue(match({'age': 18}, 'NOT "age" = 12'))

    def test_equal(self):
        self.assertTrue(match({'age': 18}, '"age" = 18'))
        self.assertFalse(match({'age': 18}, '"age" = 12'))

    def test_notequal(self):
        self.assertTrue(match({'age': 18}, '"age" != 12'))
        self.assertFalse(match({'age': 18}, '"age" != 18'))

    def test_lt(self):
        self.assertTrue(match({'age': 18}, '"age" < 20'))
        self.assertFalse(match({'age': 18}, '"age" < 17'))
        self.assertFalse(match({'age': 18}, '"age" < 18'))

    def test_gt(self):
        self.assertTrue(match({'age': 18}, '"age" > 12'))
        self.assertFalse(match({'age': 18}, '"age" > 20'))
        self.assertFalse(match({'age': 18}, '"age" > 18'))

    def test_lte(self):
        self.assertTrue(match({'age': 18}, '"age" <= 20'))
        self.assertTrue(match({'age': 18}, '"age" <= 18'))
        self.assertFalse(match({'age': 18}, '"age" <= 17'))

    def test_gte(self):
        self.assertTrue(match({'age': 18}, '"age" >= 12'))
        self.assertTrue(match({'age': 18}, '"age" >= 18'))
        self.assertFalse(match({'age': 18}, '"age" >= 20'))

    def test_in(self):
        self.assertTrue(match({'role': 'admin'}, '"role" in ["admin", "observer"]'))
        self.assertTrue(match({'age': 18}, '"age" in [12, 56, 78, 18, 90, 20]'))
        self.assertFalse(match({'role': 'user'}, '"role" in ["admin", "observer"]'))

    def test_like(self):
        self.assertTrue(match({'username': 'test_admin_username'}, '"username" LIKE "*admin*"'))
        self.assertTrue(match({'username': 'test_admin_username'}, '"username" LIKE "test*"'))
        self.assertTrue(match({'username': 'test_admin_username'}, '"username" LIKE "test?admin?username"'))
        self.assertFalse(match({'username': 'test_admin_username'}, '"username" LIKE "test"'))

    def test_match(self):
        self.assertTrue(match({'username': 'test_admin_username'}, r'"username" MATCH /.*admin.*/'))
        self.assertTrue(match({'username': 'test_admin_username'}, r'"username" MATCH /test.*/'))
        self.assertTrue(match({'age': '98'}, r'"age" MATCH /\d+/'))
        self.assertFalse(match({'username': 'test_admin_username'}, r'"username" MATCH /qwerty/'))

    def test_contain(self):
        self.assertTrue(match({'roles': ['admin', 'observer']}, '"roles" CONTAIN "admin"'))
        self.assertFalse(match({'roles': ['admin', 'observer']}, '"roles" CONTAIN "user"'))

    def test_only_keys(self):
        self.assertTrue(match({'username': 'cyberlis', 'age': 26}, "'username' AND 'age'"))
        self.assertTrue(match({'username': 'cyberlis', 'age': 26}, "'username'"))
        self.assertFalse(match({'username': 'cyberlis', 'age': 0}, "'age'"))
        self.assertFalse(match({'username': 'cyberlis'}, "'age'"))
        self.assertFalse(match({'username': 'cyberlis', 'age': 0}, "'username' AND 'age'"))

    def test_eval_token(self):
        self.assertEqual(_eval_token(Token('NUMBER', '34')), 34)
        self.assertEqual(_eval_token(Token('BOOLEAN', 'true')), True)
        self.assertEqual(_eval_token(Token('BOOLEAN', 'false')), False)
        self.assertEqual(_eval_token(Token('NONE', 'none')), None)
        self.assertEqual(_eval_token(Token('NONE', 'null')), None)
        self.assertEqual(_eval_token(Token('NONE', 'nil')), None)
        self.assertEqual(_eval_token(Token('STRING', '"hello"')), 'hello')
        self.assertEqual(_eval_token(Token('STRING', '"world"')), 'world')
        self.assertEqual(_eval_token(Token('ARRAY', [Token('STRING', '"hello"'), Token('NUMBER', 12),
                                                     Token('BOOLEAN', 'true'), Token('NONE', 'none'),])),
                         ['hello', 12, True, None])
        self.assertEqual(
            _eval_token(Token('REGEXP', r'/[abcd]+\d\s*finish/')).pattern,
            r'[abcd]+\d\s*finish')


if __name__ == '__main__':
    unittest.main()
