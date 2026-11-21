# Issue 3 (Feature): Add `multiply(field, n)` document operation to tinydb.operations

**Issue Type**: Small Feature Request  
**Component**: `tinydb/operations.py`

## Description
TinyDB currently provides `add(field, n)` and `subtract(field, n)` operations in `tinydb.operations`. However, calculating scaled quantities, percentage adjustments, and price factors requires a multiplication operation.

Please add a `multiply(field, n)` operation that returns a transformation callable following the exact conventions of `add` and `subtract`.

## Requirements
- Support positive integers, floats, negative multipliers, and zero.
- Raise an appropriate `KeyError` or leave missing fields unchanged consistent with existing operations.
- Export `multiply` in `tinydb.operations.__all__` and test integration with `table.update()`.
