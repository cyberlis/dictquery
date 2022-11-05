from dictquery.datavalue import query_value
from dictquery.exceptions import DQValidationError
from dictquery.visitors import (
    DataQueryVisitor,
    MongoQueryVisitor,
    KeyExistenceValidatorVisitor)
from dictquery.parsers import DataQueryParser

__version__ = '0.5.0.dev1'
parser = DataQueryParser()


def is_query_valid(query):
    ast = parser.parse(query)
    visitor = KeyExistenceValidatorVisitor(ast)
    try:
        visitor.evaluate()
    except DQValidationError:
        return False
    return True

def query_to_mongo(query, case_sensitive=True):
    """Converts DictQuery query to mongo query"""
    ast = parser.parse(query)
    mq = MongoQueryVisitor(ast, case_sensitive)
    return mq.evaluate()


def compile(query, use_nested_keys=True,
            key_separator='.', case_sensitive=True,
            raise_keyerror=False, validate=True):
    """Builder parses query and returns configured reusable DataQueryVisitor object."""
    ast = parser.parse(query)
    if validate:
        KeyExistenceValidatorVisitor(ast).evaluate()
    return DataQueryVisitor(
        ast, use_nested_keys=use_nested_keys,
        key_separator=key_separator, case_sensitive=case_sensitive,
        raise_keyerror=raise_keyerror)


def match(data, query):
    """Checks if `data` object satisfies `query`"""
    ast = parser.parse(query)
    # validation
    KeyExistenceValidatorVisitor(ast).evaluate()

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
