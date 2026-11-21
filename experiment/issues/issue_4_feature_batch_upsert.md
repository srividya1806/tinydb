# Issue 4 (Feature): Add `Table.upsert_multiple()` for bulk upsert operations

**Issue Type**: Small Feature Request  
**Component**: `tinydb/table.py`

## Description
Currently, `Table.upsert()` only supports updating or inserting a single document at a time. When ingesting feeds or synchronizing remote collections, callers must loop over `upsert()` individually, causing repetitive storage read/write operations and cache invalidations.

Please implement `Table.upsert_multiple(documents, cond)` to perform batch upsert operations efficiently.

## Requirements
- Accepts an iterable of documents or `(document, condition)` pairs.
- If a condition matches existing documents, updates them; otherwise inserts a new document.
- Returns list of document IDs created or updated.
- Ensures consistency with table query caching.
