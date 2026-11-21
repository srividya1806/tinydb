import pytest
from tinydb import TinyDB, Query, where
from tinydb.operations import multiply
import tinydb.operations

def test_acceptance_criterion_3():
    """AC-3: Given the tinydb.operations module, When it is imported, Then multiply is successfully imported from tinydb.operations.__all__."""
    assert hasattr(tinydb.operations, 'multiply')
    assert 'multiply' in tinydb.operations.__all__
    assert callable(multiply)


@pytest.mark.parametrize(
    "initial_val, multiplier, expected_val",
    [
        (10, 5, 50),                 # Positive integer
        (10, -3, -30),               # Negative number
        (10, 1.5, 15.0),             # Float multiplier
        (10, 0, 0),                  # Zero multiplier
        (5.5, 2, 11.0),              # Float initial value
        (-4, 2.5, -10.0),            # Negative initial value and float multiplier
    ]
)
def test_acceptance_criterion_1_numeric_values(tmp_path, initial_val, multiplier, expected_val):
    """AC-1: Given a document where the target field contains a numeric value (integer or float),
    When the multiply(field, n) operation is executed via table.update(),
    Then the field's value is multiplied by n (supporting positive integers, negative numbers, floats, and zero).
    """
    db_file = tmp_path / "db.json"
    db = TinyDB(db_file)
    db.insert({'id': 1, 'score': initial_val})

    db.update(multiply('score', multiplier), where('id') == 1)
    
    doc = db.get(where('id') == 1)
    assert doc['score'] == expected_val
    db.close()


def test_acceptance_criterion_2_missing_field(tmp_path):
    """AC-2: Given a document where the target field does not exist,
    When the multiply(field, n) operation is executed via table.update(),
    Then the missing field is handled consistently with existing operations
    (raising a KeyError, matching add/subtract/etc. behavior on missing dict keys).
    """
    db_file = tmp_path / "db.json"
    db = TinyDB(db_file)
    db.insert({'id': 1, 'other_field': 100})

    # Operations like add, subtract, and multiply attempt in-place modification (doc[field] *= n)
    # which raises a KeyError when the field is absent, matching existing conventions.
    with pytest.raises(KeyError):
        db.update(multiply('non_existent', 2), where('id') == 1)

    db.close()