from copy import deepcopy
import tempfile

import pytest
from lib import *


def test_read_config_from_disk_ok():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b'{ "workflow_id": 1234 }')
        fp.seek(0)
        assert read_config_from_disk(fp.name) == {"workflow_id": 1234}
        fp.close()


def test_read_config_from_disk_empty():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b"")
        fp.seek(0)
        assert read_config_from_disk(fp.name) == None
        fp.close()


def test_read_config_from_disk_malformed():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b"{ abc }")
        fp.seek(0)
        assert read_config_from_disk(fp.name) == None
        fp.close()


cfg_ok = {
    "group_id": None,
    "pt_csv_file": data_pivotal_export_csv,
    "priorities_csv_file": data_priorities_csv,
    "priority_custom_field_id": "123",
    "states_csv_file": data_states_csv,
    "users_csv_file": data_users_csv,
    "workflow_id": "456",
}


def assoc(dict, key, value):
    """Return a copy of `dict` with `key` assigned to `value`"""
    d = deepcopy(dict)
    d[key] = value


def dissoc(dict, key_to_remove):
    """Return a copy of `dict` with `key_to_remove` absent."""
    d = deepcopy(dict)
    del d[key_to_remove]
    return d


def test_validate_config_ok():
    assert cfg_ok == validate_config(cfg_ok)


def test_validate_config_missing_fields():
    with pytest.raises(SystemExit):
        validate_config({})
    for k in cfg_ok.keys():
        with pytest.raises(SystemExit):
            validate_config(dissoc(cfg_ok, k))
    for k in [key for key in cfg_ok.keys() if k != "group_id"]:  # group_id may be null
        with pytest.raises(SystemExit):
            validate_config(assoc(cfg_ok, k, ""))


def test_parse_comment_good():
    comment = """Testing comments (Daniel Gregoire - Mar 25, 2024)"""
    assert parse_comment(comment) == {
        "text": "Testing comments",
        "author": "Daniel Gregoire",
        "created_at": "2024-03-25T00:00:00",
    }


def test_parse_comment_authorship_in_text():
    comment = """Testing comments (Daniel Gregoire - Mar 25, 2024) (Osei Poku - Jan 01, 2004)"""
    assert parse_comment(comment) == {
        "text": "Testing comments (Daniel Gregoire - Mar 25, 2024)",
        "author": "Osei Poku",
        "created_at": "2004-01-01T00:00:00",
    }


def test_parse_comment_multiline():
    s = """Here's
a
multiline
comment
no
extra
newlines."""
    comment = f"{s} (Daniel Gregoire - Apr 1, 2024)"
    assert parse_comment(comment) == {
        "text": s,
        "author": "Daniel Gregoire",
        "created_at": "2024-04-01T00:00:00",
    }


def test_parse_comment_without_suffix():
    s = "A comment without a suffix"
    assert parse_comment(s) == {"text": s}


def test_parse_date():
    assert parse_date("Oct 15, 2024") == "2024-10-15"


def test_parse_date_time():
    assert parse_date_time("Oct 15, 2014") == "2014-10-15T00:00:00"
