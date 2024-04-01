from lib import *


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


def test_parse_date():
    assert parse_date("Oct 15, 2014") == "2014-10-15T00:00:00"
