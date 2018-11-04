# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import unittest

from dictquery.exceptions import DQSyntaxError
import dictquery as dq


class TestMatchCompile(unittest.TestCase):
    def test_not(self):
        self.assertTrue(dq.match({'age': 18}, 'NOT age == 12'))

    def test_equal(self):
        self.assertTrue(dq.match({'age': 18}, 'age == 18'))
        self.assertFalse(dq.match({'age': 18}, 'age == 12'))

    def test_notequal(self):
        self.assertTrue(dq.match({'age': 18}, 'age != 12'))
        self.assertFalse(dq.match({'age': 18}, 'age != 18'))

    def test_lt(self):
        self.assertTrue(dq.match({'age': 18}, 'age < 20'))
        self.assertFalse(dq.match({'age': 18}, 'age < 17'))
        self.assertFalse(dq.match({'age': 18}, 'age < 18'))

    def test_gt(self):
        self.assertTrue(dq.match({'age': 18}, 'age > 12'))
        self.assertFalse(dq.match({'age': 18}, 'age > 20'))
        self.assertFalse(dq.match({'age': 18}, 'age > 18'))

    def test_lte(self):
        self.assertTrue(dq.match({'age': 18}, 'age <= 20'))
        self.assertTrue(dq.match({'age': 18}, 'age <= 18'))
        self.assertFalse(dq.match({'age': 18}, 'age <= 17'))

    def test_gte(self):
        self.assertTrue(dq.match({'age': 18}, 'age >= 12'))
        self.assertTrue(dq.match({'age': 18}, 'age >= 18'))
        self.assertFalse(dq.match({'age': 18}, 'age >= 20'))

    def test_in(self):
        self.assertTrue(dq.match({'role': 'admin'}, 'role in ["admin", "observer"]'))
        self.assertTrue(dq.match({'age': 18}, 'age in [12, 56, 78, 18, 90, 20]'))
        self.assertFalse(dq.match({'role': 'user'}, 'role in ["admin", "observer"]'))

    def test_like(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(dq.match(data, 'username LIKE "*admin*"'))
        self.assertTrue(dq.match(data, 'username LIKE "test*"'))
        self.assertTrue(dq.match(data, 'username LIKE "test?admin?username"'))
        self.assertFalse(dq.match(data, 'username LIKE "test"'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, 'username LIKE 23'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, '"test" LIKE username'))

    def test_match(self):
        data = {'username': 'test_admin_username'}
        self.assertTrue(dq.match(data, r'username MATCH /.*admin.*/'))
        self.assertTrue(dq.match(data, r'username MATCH /test.*/'))
        self.assertTrue(dq.match({'age': '98'}, r'age MATCH /\d+/'))
        self.assertFalse(dq.match(data, r'username MATCH /qwerty/'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, r'/\d+/ MATCH username'))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, r'username MATCH "test"'))

    def test_contains(self):
        self.assertTrue(dq.match({'roles': ['admin', 'observer']}, 'roles CONTAINS "admin"'))
        self.assertFalse(dq.match({'roles': ['admin', 'observer']}, 'roles CONTAINS "user"'))

    def test_now(self):
        utcnow = datetime.utcnow()
        self.assertTrue(
            dq.match({'time': utcnow - timedelta(hours=1)},
            "time < NOW"))
        self.assertFalse(
            dq.match({'time': utcnow - timedelta(hours=1)},
            "time == NOW"))

    def test_only_keys(self):
        self.assertTrue(dq.match({'username': 'cyberlis', 'age': 26}, "username AND age"))
        self.assertTrue(dq.match({'username': 'cyberlis', 'age': 26}, "username"))
        self.assertFalse(dq.match({'username': 'cyberlis', 'age': 0}, "age"))
        self.assertFalse(dq.match({'username': 'cyberlis'}, "age"))
        self.assertFalse(dq.match({'username': 'cyberlis', 'age': 0}, "username AND age"))

    def test_pars(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(dq.match(data, "(a) AND (c)"))
        self.assertTrue(dq.match(data, "((a) AND (c))"))
        self.assertTrue(dq.match(data, "((((a)) AND ((c))))"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, "(a) AND (c"))
        with self.assertRaises(DQSyntaxError):
            self.assertTrue(dq.match(data, ")a AND c"))

    def test_eval_order(self):
        data = {'a': 1, 'b': 0, 'c': 1, 'x': 0, 'y': 1, 'z': 0}
        self.assertTrue(dq.match(data, "a == 1 OR c == 0"))
        self.assertFalse(dq.match(data, "a == 0 AND c == 1"))
        self.assertTrue(dq.match(data, "a == 0 AND c == 1 OR z == 0"))
        self.assertFalse(dq.match(data, "a == 0 AND (c == 1 OR z == 0)"))

    def test_case_sensitive(self):
        data = {'username': 'CybeRLiS'}
        dq_case_sensitive = dq.compile("username == 'cyberlis'", case_sensitive=True)
        dq_case_insensitive = dq.compile("username == 'cyberlis'", case_sensitive=False)
        self.assertFalse(dq_case_sensitive.match(data))
        self.assertTrue(dq_case_insensitive.match(data))
        dq_cis_in = dq.compile(
            "username IN ['cybeRLIS', 'rinagorhs']",
            case_sensitive=False)
        self.assertTrue(dq_cis_in.match(data))
        dq_cs_match = dq.compile(r"username MATCH /cyberlis/", case_sensitive=True)
        dq_cis_match = dq.compile(r"username MATCH /cyberlis/", case_sensitive=False)
        self.assertFalse(dq_cs_match.match(data))
        self.assertTrue(dq_cis_match.match(data))

        dq_cs_like = dq.compile(r"username LIKE 'cyberlis'", case_sensitive=True)
        dq_cis_like = dq.compile(r"username LIKE 'cyberlis'", case_sensitive=False)
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
        self.assertTrue(dq.match(data1, "26 == age"))
        self.assertTrue(dq.match(data1, "[23, 45, 12, 26] CONTAINS age"))
        self.assertTrue(dq.match(data1, "age == age"))
        self.assertTrue(dq.match(data2, "x < y"))
        self.assertFalse(dq.match(data2, "x >= y"))
        self.assertTrue(dq.match(data2, "x != y"))
        self.assertTrue(dq.match(data3, "age < `friends.age`"))



if __name__ == '__main__':
    unittest.main()
