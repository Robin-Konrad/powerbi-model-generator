import generator.core as core
import pytest
from pathlib import Path

from generator.measures_columns import find_numeric_fields, rename_to_no_agg

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_table.tmdl"

def _use_fixture_copy(tmp_path, monkeypatch):
    """
        Copies the sample fixture file into a pytest tmp_path
        directory, then sets core.TABLE_FILE to reference this tmp_path for this test.

        :param tmp_path:      pathlib.Path, required    temporary pytest directory used to create the copied test file
        :param monkeypatch:   str, required             pytest fixture used to temporarily modify core.TABLE_FILE
        :return:              str                       path to the temporary copied fixture file
    """
    test_file = tmp_path / "sample_table.tmdl"
    with open(FIXTURE_PATH) as source, open(test_file, "w") as dest:
        dest.write(source.read())

    monkeypatch.setattr(core, "TABLE_FILE", test_file)

    return test_file

def test_quote():
    # names with spaces or special characters get single quotes
    assert core.quote("Sales Amount") == "'Sales Amount'"
    assert core.quote("Sales-Amount") == "'Sales-Amount'"
    # plain names also get single quotes for consistency
    assert core.quote("SalesAmount") == "'SalesAmount'"


def test_append_writes_text_with_trailing_newline(tmp_path):
    test_file = f"{tmp_path}/output.tmdl"
    open(test_file, "w").close()

    core.append(test_file, "hello world")

    with open(test_file) as f:
        assert f.read() == "hello world\n"


def test_append_adds_to_existing_content(tmp_path):
    test_file = f"{tmp_path}/output.tmdl"
    with open(test_file, "w") as f:
        f.write("line one\n")

    core.append(test_file, "line two")

    with open(test_file) as f:
        assert f.read() == "line one\nline two\n"


def test_find_numeric_fields_returns_numeric_columns(tmp_path, monkeypatch):
    _use_fixture_copy(tmp_path, monkeypatch)

    fields = find_numeric_fields()

    assert "ID" in fields  # int64
    assert "Items Ordered" in fields  # int64, quoted name
    assert "Order Total" in fields  # double
    assert "Discount Deduction" in fields  # decimal


def test_find_numeric_fields_excludes_non_numeric_columns(tmp_path, monkeypatch):
    _use_fixture_copy(tmp_path, monkeypatch)

    fields = find_numeric_fields()

    assert "OrderDate" not in fields  # dateTime
    assert "Customer Name" not in fields  # string


def test_find_numeric_fields_returns_bare_names_not_quoted(tmp_path, monkeypatch):
    _use_fixture_copy(tmp_path, monkeypatch)

    fields = find_numeric_fields()

    assert "'Items Ordered'" not in fields
    assert "Items Ordered" in fields


def test_rename_to_no_agg_renames_quoted_field(tmp_path, monkeypatch):
    test_file = _use_fixture_copy(tmp_path, monkeypatch)

    rename_to_no_agg("Items Ordered")

    with open(test_file) as f:
        text = f.read()
    assert "column 'Items Ordered (No Agg)'" in text
    assert "column 'Items Ordered'\n" not in text


def test_rename_to_no_agg_renames_unquoted_field(tmp_path, monkeypatch):
    test_file = _use_fixture_copy(tmp_path, monkeypatch)

    rename_to_no_agg("ID")

    with open(test_file) as f:
        text = f.read()
    assert "column 'ID (No Agg)'" in text
    assert "column ID\n" not in text


def test_rename_to_no_agg_raises_if_field_missing(tmp_path, monkeypatch):
    _use_fixture_copy(tmp_path, monkeypatch)

    with pytest.raises(ValueError):
        rename_to_no_agg("Field That Does Not Exist")



