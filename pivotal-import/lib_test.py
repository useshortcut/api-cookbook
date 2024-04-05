import tempfile
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
    assert parse_date("Oct 15, 2014") == "2014-10-15T00:00:00"
