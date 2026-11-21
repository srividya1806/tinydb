"""Hidden Acceptance Tests for Issue 5: Numeric Operations / Math helpers"""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from tinydb.operations import multiply


def test_hidden_math_scaling():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'balance': 100})

    # Scale by 1.15 (15% interest)
    db.update(multiply('balance', 1.15))
    assert db.all()[0]['balance'] == pytest.approx(115.0)


def test_hidden_math_zero():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'balance': 100})

    db.update(multiply('balance', 0))
    assert db.all()[0]['balance'] == 0
