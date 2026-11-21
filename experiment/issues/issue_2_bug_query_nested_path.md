# Issue 2 (Bug): Query().test() raises AttributeError/KeyError on documents with missing or non-dict nested paths

**Issue Type**: Bug Report  
**Component**: `tinydb/queries.py` (`Query`)

## Description
When performing a query with `Query().field.test(predicate)` across documents where some documents do not contain `field`, or where the field path traverses a non-dict scalar value, an unhandled exception (`AttributeError` or `KeyError`) is raised instead of treating the document as non-matching (returning `False`).

## Steps to Reproduce
```python
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

db = TinyDB(storage=MemoryStorage)
db.insert({'profile': {'name': 'Alice'}})
db.insert({'profile': None}) # Non-dict nested value
db.insert({'other': 123})    # Missing 'profile' entirely

User = Query()
# Should return only Alice, but crashes with AttributeError: 'NoneType' object has no attribute 'get'
results = db.search(User.profile.name.test(lambda v: v.startswith('A')))
```

## Expected Behavior
Queries traversing paths on documents with missing keys or invalid nested structures should gracefully evaluate to `False` without crashing.
