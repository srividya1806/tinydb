import pytest
from tinydb import TinyDB, Query, where
from tinydb.operations import multiply
import tinydb.operations


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'db.json'
    database = TinyDB(path)
    database.insert({'char': 'a', 'int': 10, 'float': 2.5})
    database.insert({'char': 'b', 'int': -4, 'float': -1.5})
    database.insert({'char': 'c', 'int': 0, 'float': 0.0})
    yield database
    database.close()


def test_acceptance_criterion_1(db):
    """
    AC-1: Given a document where the target field contains a numeric value (integer or float),
    When the multiply(field, n) operation is executed via table.update(),
    Then the field's value is multiplied by n (supporting positive integers, negative numbers, floats, and zero).
    """
    # Multiply integer by positive integer
    db.update(multiply('int', 3), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == 30

    # Multiply float by float
    db.update(multiply('float', 1.5), where('char') == 'a')
    assert db.get(where('char') == 'a')['float'] == pytest.approx(3.75)

    # Multiply negative number by positive number
    db.update(multiply('int', 2), where('char') == 'b')
    assert db.get(where('char') == 'b')['int'] == -8

    # Multiply by negative number
    db.update(multiply('float', -2.0), where('char') == 'b')
    assert db.get(where('char') == 'b')['float'] == 3.0

    # Multiply by zero
    db.update(multiply('int', 0), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == 0


def test_acceptance_criterion_2(db):
    """
    AC-2: Given a document where the target field does not exist,
    When the multiply(field, n) operation is executed via table.update(),
    Then the missing field is handled consistently with existing operations
    (either left unchanged or raising a KeyError as per standard TinyDB operation conventions).
    """
    # Ensure missing field is left unchanged (not added or erroring)
    db.update(multiply('non_existent_field', 5), where('char') == 'a')
    assert 'non_existent_field' not in db.get(where('char') == 'a')


def test_acceptance_criterion_3():
    """
    AC-3: Given the tinydb.operations module,
    When it is imported,
    Then multiply is successfully imported from tinydb.operations.__all__.
    """
    assert hasattr(tinydb.operations, 'multiply')
    assert 'multiply' in tinydb.operations.__all__
    
    # Verify that multiply can be imported directly from tinydb.operations
    from tinydb.operations import multiply as imported_multiply
    assert callable(imported_multiply('field', 2))