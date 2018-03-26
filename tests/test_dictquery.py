# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import unittest
from dictquery import (
    Token, DictQueryParser,
    get_dict_value, match, _eval_token,
    DQKeyError, DQSyntaxError, DictQuery)


class TestMatchDict(unittest.TestCase):
    def test_parse_key(self):
        parser = DictQueryParser()
        self.assertEqual(parser.parse('`key1`'), Token('KEY', 'key1'))

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
            get_dict_value({'user.username': 'cyberlis'},
                            'user.username',
                            raise_keyerror=True,
                            use_nested_keys=True)

        self.assertEqual(
            get_dict_value({'user.username': 'cyberlis'},
                           'user.username',
                           raise_keyerror=True,
                           use_nested_keys=False),
            ['cyberlis']
        )
        with self.assertRaises(DQKeyError):
            get_dict_value({'users': [{'fullname': {'lastname': 'cyberlis'}},]},
                           'users.fullname.firstname', raise_keyerror=True)

    def test_not(self):
        self.assertTrue(match({'age': 18}, 'NOT `age` == 12'))

    def test_equal(self):
        self.assertTrue(match({'age': 18}, '`age` == 18'))
        self.assertFalse(match({'age': 18}, '`age` == 12'))

    def test_notequal(self):
        self.assertTrue(match({'age': 18}, '`age` != 12'))
        self.assertFalse(match({'age': 18}, '`age` != 18'))

    def test_lt(self):
        self.assertTrue(match({'age': 18}, '`age` < 20'))
        self.assertFalse(match({'age': 18}, '`age` < 17'))
        self.assertFalse(match({'age': 18}, '`age` < 18'))

    def test_gt(self):
        self.assertTrue(match({'age': 18}, '`age` > 12'))
        self.assertFalse(match({'age': 18}, '`age` > 20'))
        self.assertFalse(match({'age': 18}, '`age` > 18'))

    def test_lte(self):
        self.assertTrue(match({'age': 18}, '`age` <= 20'))
        self.assertTrue(match({'age': 18}, '`age` <= 18'))
        self.assertFalse(match({'age': 18}, '`age` <= 17'))

    def test_gte(self):
        self.assertTrue(match({'age': 18}, '`age` >= 12'))
        self.assertTrue(match({'age': 18}, '`age` >= 18'))
        self.assertFalse(match({'age': 18}, '`age` >= 20'))

    def test_in(self):
        self.assertTrue(match({'role': 'admin'}, '`role` in ["admin", "observer"]'))
        self.assertTrue(match({'age': 18}, '`age` in [12, 56, 78, 18, 90, 20]'))
        self.assertFalse(match({'role': 'user'}, '`role` in ["admin", "observer"]'))

    def test_like(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(match(data, '`username` LIKE "*admin*"'))
        self.assertTrue(match(data, '`username` LIKE "test*"'))
        self.assertTrue(match(data, '`username` LIKE "test?admin?username"'))
        self.assertFalse(match(data, '`username` LIKE "test"'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, '`username` LIKE 23'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, '"test" LIKE `username`'))

    def test_match(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(match(data, r'`username` MATCH /.*admin.*/'))
        self.assertTrue(match(data, r'`username` MATCH /test.*/'))
        self.assertTrue(match({'age': '98'}, r'`age` MATCH /\d+/'))
        self.assertFalse(match(data, r'`username` MATCH /qwerty/'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, r'/\d+/ MATCH `username`'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, r'`username` MATCH "test"'))

    def test_contain(self):
        self.assertTrue(match({'roles': ['admin', 'observer']}, '`roles` CONTAIN "admin"'))
        self.assertFalse(match({'roles': ['admin', 'observer']}, '`roles` CONTAIN "user"'))

    def test_now(self):
        utcnow = datetime.utcnow()
        self.assertTrue(
            match({'time': utcnow - timedelta(hours=1)},
            "`time` < NOW"))
        self.assertFalse(
            match({'time': utcnow - timedelta(hours=1)},
            "`time` == NOW"))

    def test_only_keys(self):
        self.assertTrue(match({'username': 'cyberlis', 'age': 26}, "`username` AND `age`"))
        self.assertTrue(match({'username': 'cyberlis', 'age': 26}, "`username`"))
        self.assertFalse(match({'username': 'cyberlis', 'age': 0}, "`age`"))
        self.assertFalse(match({'username': 'cyberlis'}, "`age`"))
        self.assertFalse(match({'username': 'cyberlis', 'age': 0}, "`username` AND `age`"))

    def test_pars(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(match(data, "(`a`) AND (`c`)"))
        self.assertTrue(match(data, "((`a`) AND (`c`))"))
        self.assertTrue(match(data, "((((`a`)) AND ((`c`))))"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, "(`a`) AND (`c`"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(match(data, ")`a` AND `c`"))

    def test_eval_order(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(match(data, "`a` == 1 OR `c` == 0"))
        self.assertFalse(match(data, "`a` == 0 AND `c` == 1"))
        self.assertTrue(match(data, "`a` == 0 AND `c` == 1 OR `z` == 0"))
        self.assertFalse(match(data, "`a` == 0 AND (`c` == 1 OR `z` == 0)"))

    def test_case_sensitive(self):
        data = {'username': 'CybeRLiS'}
        dq_case_sensitive = DictQuery("`username` == 'cyberlis'", case_sensitive=True)
        dq_case_insensitive = DictQuery("`username` == 'cyberlis'", case_sensitive=False)
        self.assertFalse(dq_case_sensitive.match(data))
        self.assertTrue(dq_case_insensitive.match(data))
        dq_cis_in = DictQuery(
            "`username` IN ['cybeRLIS', 'rinagorhs']",
            case_sensitive=False)
        self.assertTrue(dq_cis_in.match(data))
        dq_cs_match = DictQuery(r"`username` MATCH /cyberlis/", case_sensitive=True)
        dq_cis_match = DictQuery(r"`username` MATCH /cyberlis/", case_sensitive=False)
        self.assertFalse(dq_cs_match.match(data))
        self.assertTrue(dq_cis_match.match(data))

        dq_cs_like = DictQuery(r"`username` LIKE 'cyberlis'", case_sensitive=True)
        dq_cis_like = DictQuery(r"`username` LIKE 'cyberlis'", case_sensitive=False)
        self.assertFalse(dq_cs_like.match(data))
        self.assertTrue(dq_cis_like.match(data))

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

    def test_key_order(self):
        data1 = {'age': 26}
        data2 = {'x': 12, 'y': 33}
        data3 = {'age': 12, 'friends': [
            {'age': 14},
            {'age': 16},
            {'age': 18},
            {'age': 20},
        ]}
        self.assertTrue(match(data1, "26 == `age`"))
        self.assertTrue(match(data1, "[23, 45, 12, 26] CONTAIN `age`"))
        self.assertTrue(match(data1, "`age` == `age`"))
        self.assertTrue(match(data2, "`x` < `y`"))
        self.assertFalse(match(data2, "`x` >= `y`"))
        self.assertTrue(match(data2, "`x` != `y`"))
        self.assertTrue(match(data3, "`age` < `friends.age`"))


if __name__ == '__main__':
    unittest.main()
