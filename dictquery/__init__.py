from dictquery.visitors import (
    DataQueryVisitor,
    MongoQueryVisitor,
)
from dictquery.parsers import DataQueryParser

__version__ = '0.5.0'
parser = DataQueryParser()


def query_to_mongo(query, case_sensitive=True):
    """Converts DictQuery query to mongo query"""
    ast = parser.parse(query)
    mq = MongoQueryVisitor(ast, case_sensitive)
    return mq.evaluate()


def compile(query, use_nested_keys=True,
            key_separator='.', case_sensitive=True,
            raise_keyerror=False):
    """Builder parses query and returns configured reusable DataQueryVisitor object."""
    ast = parser.parse(query)
    return DataQueryVisitor(
        ast, use_nested_keys=use_nested_keys,
        key_separator=key_separator, case_sensitive=case_sensitive,
        raise_keyerror=raise_keyerror)


def match(data, query):
    """Checks if `data` object satisfies `query`"""
    ast = parser.parse(query)

    dq = DataQueryVisitor(ast)
    return dq.evaluate(data)


def filter(data, query, use_nested_keys=True,
           key_separator='.', case_sensitive=True,
           raise_keyerror=False):
    """Filters iterable. Checks if each item satisfies `query`"""
    ast = parser.parse(query)
    dq = DataQueryVisitor(
        ast, use_nested_keys=use_nested_keys,
        key_separator=key_separator, case_sensitive=case_sensitive,
        raise_keyerror=raise_keyerror)
    for item in data:
        if not dq.evaluate(item):
            continue
        yield item
