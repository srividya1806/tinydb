"""Hidden Acceptance Tests for Issue 3: multiply() operation in tinydb.operations"""

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.operations import multiply


def test_hidden_multiply_integer_and_float():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'count': 5, 'rate': 2.5})

    db.update(multiply('count', 3))
    db.update(multiply('rate', 2))

    doc = db.all()[0]
    assert doc['count'] == 15
    assert doc['rate'] == pytest.approx(5.0)


def test_hidden_multiply_negative_and_zero():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'qty': 10})

    db.update(multiply('qty', -2))
    assert db.all()[0]['qty'] == -20

    db.update(multiply('qty', 0))
    assert db.all()[0]['qty'] == 0


def test_hidden_multiply_missing_key():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'other': 10})

    # Missing field should raise KeyError or leave unchanged
    try:
        db.update(multiply('missing_field', 2))
        assert 'missing_field' not in db.all()[0]
    except KeyError:
        pass
