# Issue 1 (Bug): Table.update_multiple() fails to update subsequent documents when passed a generator

**Issue Type**: Bug Report  
**Component**: `tinydb/table.py` (`Table.update_multiple`)

## Description
When calling `table.update_multiple()` with an iterable of `(operation, condition)` tuples where the iterable is a one-shot generator (e.g. from a generator expression or `yield`), only the first matching document gets updated. Any subsequent matching documents are skipped because the generator is exhausted after the first match.

## Steps to Reproduce
```python
from tinydb import TinyDB, Query

db = TinyDB(storage=MemoryStorage)
table = db.table('items')
table.insert_multiple([{'val': 1, 'tag': 'a'}, {'val': 1, 'tag': 'a'}])

# Generator of updates:
updates = ((lambda doc: doc.update({'val': 2}), Query().val == 1) for _ in range(1))
updated_ids = table.update_multiple(updates)

print(updated_ids) # Expected [1, 2], but got [1]
```

## Expected Behavior
All matching documents should receive the applicable update operations even if the passed iterable is a single-use generator. The method should return the document IDs of all updated documents, preserving existing list behavior.
