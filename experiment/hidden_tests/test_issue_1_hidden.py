"""Hidden Acceptance Tests for Issue 1: Generator handling in Table.update_multiple()"""

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_hidden_generator_multiple_matching_documents():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('items')
    table.insert_multiple([
        {'val': 10, 'cat': 'alpha'},
        {'val': 10, 'cat': 'alpha'},
        {'val': 10, 'cat': 'beta'}
    ])

    gen = ((lambda doc: doc.update({'val': 20}), Query().val == 10) for _ in range(1))
    updated_ids = table.update_multiple(gen)

    assert set(updated_ids) == {1, 2, 3}
    assert all(doc['val'] == 20 for doc in table.all())


def test_hidden_empty_generator():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('items')
    table.insert({'val': 10})

    empty_gen = (x for x in [])
    updated_ids = table.update_multiple(empty_gen)

    assert updated_ids == []
    assert table.all()[0]['val'] == 10


def test_hidden_multiple_different_generator_rules():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('items')
    table.insert_multiple([
        {'score': 5, 'badge': 'bronze'},
        {'score': 15, 'badge': 'silver'},
        {'score': 25, 'badge': 'gold'}
    ])

    def rule_generator():
        yield (lambda doc: doc.update({'badge': 'verified_bronze'}), Query().score == 5)
        yield (lambda doc: doc.update({'badge': 'verified_silver'}), Query().score == 15)

    updated_ids = table.update_multiple(rule_generator())
    assert set(updated_ids) == {1, 2}
    assert table.get(doc_id=1)['badge'] == 'verified_bronze'
    assert table.get(doc_id=2)['badge'] == 'verified_silver'
    assert table.get(doc_id=3)['badge'] == 'gold'
