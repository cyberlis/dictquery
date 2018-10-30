try:
    from collections.abc import Iterable, Sequence, Mapping
except ImportError:
    from collections import Iterable, Sequence, Mapping

import fnmatch
import operator
import re
from dictquery.exceptions import DQKeyError


try:
  basestring
except NameError:
  basestring = str


def _is_instance(obj):
    """is custom class instance"""
    return hasattr(obj,'__dict__') or hasattr(obj,'__slots__')

def _is_iterable(obj):
    return isinstance(obj, (Iterable, Sequence))

def _is_mapping(obj):
    return isinstance(obj, Mapping)

def _get_instance_value(obj, key):
    try:
        return getattr(obj, key)
    except AttributeError:
        raise KeyError('key: {} not found'.format(key))

def _get_mapping_value(obj, key):
    return obj[key]


class AbsItem:
    def __init__(self, value):
        self.value = value

    def get_value(self, key):
        raise NotImplementedError()


class InstanceItem(AbsItem):
    def get_value(self, key):
        try:
            yield getattr(self.value, key)
        except AttributeError:
            raise KeyError('key: {} not found'.format(key))


class MappingItem(AbsItem):
    def get_value(self, key):
        yield self.value[key]


class IterableItem(AbsItem):
    def get_value(self, key):
        for item in self.value:
            try:
                if _is_mapping(item):
                    yield _get_mapping_value(item, key)
                elif _is_instance(item):
                    yield _get_instance_value(item, key)
            except KeyError:
                continue


def item_factory(value):
    if _is_mapping(value):
        return MappingItem(value)
    elif _is_instance(value):
        return InstanceItem(value)
    elif _is_iterable(value):
        return IterableItem(value)
    return None


def query_value(data, data_key, use_nested_keys=True,
                key_separator='.', raise_keyerror=False):
    result = []
    if use_nested_keys:
        keys = data_key.split(key_separator)
    else:
        keys = [data_key]

    def get_value(value, keys):
        if not keys:
            return
        item = item_factory(value)
        if item is None:
            return

        if len(keys) == 1:
            try:
                for val in item.get_value(keys[0]):
                    result.append(val)
            except KeyError:
                pass
            return

        try:
            for next_val in item.get_value(keys[0]):
                get_value(next_val, keys[1:])
        except KeyError:
            return

    get_value(data, keys)
    if not result and raise_keyerror:
        raise DQKeyError("Key '{}' not found".format(data_key))
    return result


class DataQueryItem:
    def __init__(self, key, values, case_sensitive=True, strategy=any):
        self.key = key
        self.values = values
        self.strategy = strategy
        self.case_sensitive = case_sensitive

    def __apply_op(self, other, op):
        result = []
        for val in self.values:
            if isinstance(val, basestring) and not self.case_sensitive:
                val = val.lower()
            result.append(op(val, other))
        return bool(result and self.strategy(result))

    def __lt__(self, other):
        return self.__apply_op(other, operator.lt)

    def __le__(self, other):
        return self.__apply_op(other, operator.le)

    def __eq__(self, other):
        return self.__apply_op(other, operator.eq)

    def __ne__(self, other):
        return self.__apply_op(other, operator.ne)

    def __gt__(self, other):
        return self.__apply_op(other, operator.gt)

    def __ge__(self, other):
        return self.__apply_op(other, operator.ge)

    def __contains__(self, item):
        return self.__apply_op(item, operator.contains)

    def __len__(self):
        """checks if object is True or False. for bool operation to work with this class in python2.7"""
        if not self.values:
            return 0
        return 1 if self.strategy(bool(val) for val in self.values) else 0

    def __bool__(self):
        return bool(self.__len__())

    def match(self, regexp):
        return self.__apply_op(regexp, lambda val, r: re.match(r, val))

    def like(self, pattern):
        return self.__apply_op(pattern, fnmatch.fnmatchcase)
