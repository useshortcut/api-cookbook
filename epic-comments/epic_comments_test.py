import re
import tempfile
from epic_comments import csv_file_name, write_epic_comments


def test_write_epic_comments():
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        print(f"fp {fp.name}")
        write_epic_comments(
            fp,
            [
                {
                    "id": 1234,
                    "text": "Test comment one",
                    "author_id": "test-author-id-1",
                    "comments": [],
                },
                {
                    "id": 2345,
                    "text": "Test comment two",
                    "author_id": "test-author-id-2",
                    "comments": [
                        {
                            "id": 3456,
                            "text": "Test comment nested one",
                            "author_id": "test-author-id-1",
                            "comments": [
                                {
                                    "id": 4567,
                                    "text": "Test comment nested one one",
                                    "author_id": "test-author-id-2",
                                    "comments": [],
                                }
                            ],
                        },
                        {
                            "id": 5678,
                            "text": "Test comment nested two",
                            "author_id": "test-author-id-3",
                            "comments": [],
                        },
                    ],
                },
            ],
        )
        fp.flush()
        with open(fp.name, "r") as f:
            lines = f.readlines()
            assert len(lines) == 6
            assert lines[0] == "id,author_id,text,parent_id\n"
            assert lines[1] == "1234,test-author-id-1,Test comment one,\n"
            assert lines[2] == "2345,test-author-id-2,Test comment two,\n"
            assert lines[3] == "3456,test-author-id-1,Test comment nested one,2345\n"
            assert (
                lines[4] == "4567,test-author-id-2,Test comment nested one one,3456\n"
            )
            assert lines[5] == "5678,test-author-id-3,Test comment nested two,2345\n"
        fp.close()


def test_csv_file_name():
    assert re.match(
        r"epic-1234-comments_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.csv",
        csv_file_name(1234),
    )
