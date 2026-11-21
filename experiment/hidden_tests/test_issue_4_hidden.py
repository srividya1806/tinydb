"""Hidden Acceptance Tests for Issue 4: Table.upsert_multiple()"""

import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def test_hidden_upsert_multiple_all_insert():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('items')

    docs = [{'name': 'item1', 'v': 1}, {'name': 'item2', 'v': 2}]
    # Upsert with conditions that don't match -> all inserted
    conds = [(docs[0], Query().name == 'item1'), (docs[1], Query().name == 'item2')]
    ids = table.upsert_multiple(conds)

    assert len(ids) == 2
    assert len(table) == 2


def test_hidden_upsert_multiple_update_existing():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('items')
    table.insert({'name': 'item1', 'v': 1})

    docs = [{'name': 'item1', 'v': 100}, {'name': 'item2', 'v': 200}]
    conds = [(docs[0], Query().name == 'item1'), (docs[1], Query().name == 'item2')]
    ids = table.upsert_multiple(conds)

    assert table.get(Query().name == 'item1')['v'] == 100
    assert table.get(Query().name == 'item2')['v'] == 200
    assert len(table) == 2
