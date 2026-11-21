"""Hidden Acceptance Tests for Issue 2: Nested path query handling."""

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_hidden_nested_none_handling():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'user': {'profile': {'age': 25}}})
    db.insert({'user': {'profile': None}})
    db.insert({'user': None})
    db.insert({'unrelated': 100})

    Q = Query()
    res = db.search(Q.user.profile.age == 25)
    assert len(res) == 1
    assert res[0]['user']['profile']['age'] == 25


def test_hidden_nested_test_predicate():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'meta': {'tag': 'alpha_1'}})
    db.insert({'meta': {'tag': 999}})
    db.insert({'meta': None})

    Q = Query()
    res = db.search(Q.meta.tag.test(lambda v: isinstance(v, str) and v.startswith('alpha')))
    assert len(res) == 1
    assert res[0]['meta']['tag'] == 'alpha_1'


def test_hidden_deeply_missing_keys():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'a': {'b': {'c': 42}}})
    db.insert({'a': {}})
    db.insert({})

    Q = Query()
    assert len(db.search(Q.a.b.c == 42)) == 1
    assert len(db.search(Q.a.b.c == 99)) == 0
