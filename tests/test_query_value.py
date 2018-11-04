# -*- coding: utf-8 -*-
import unittest
from dictquery.datavalue import query_value
from dictquery.exceptions import DQKeyError


class TestQueryValue(unittest.TestCase):
    def test_get_query_value(self):
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

if __name__ == '__main__':
    unittest.main()
