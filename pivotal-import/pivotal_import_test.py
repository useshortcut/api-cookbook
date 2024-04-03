from pivotal_import import *


def create_test_ctx():
    return {"workflow_config": {"unstarted": 400001, "started": 400002, "done": 400003}}


def test_parse_row_basic():
    assert {
        "name": "My Story Name",
        "description": "My Story Description",
    } == parse_row(["My Story Name", "My Story Description"], ["title", "description"])


def test_parse_comments():
    assert {
        "comments": [
            {"text": "Comment 1"},
            {"text": "Comment 2"},
            {"text": "Comment 3"},
        ]
    } == parse_row(
        ["Comment 1", "Comment 2", "Comment 3"], ["comment", "comment", "comment"]
    )


def test_build_story():
    ctx = create_test_ctx()
    d = {
        "story_type": "feature",
        "comments": [
            {"text": "Comment 1"},
            {"text": "Comment 2"},
            {"text": "Comment 3"},
        ],
    }

    assert {
        "type": "story",
        "entity": {
            "story_type": "feature",
            "comments": [
                {"text": "Comment 1"},
                {"text": "Comment 2"},
                {"text": "Comment 3"},
            ],
            "labels": [{"name": PIVOTAL_TO_SHORTCUT_LABEL}],
        },
        "parsed_row": d,
    } == build_entity(ctx, d)


def test_build_release():
    ctx = create_test_ctx()
    d = {
        "story_type": "release",
        "name": "A Release",
    }

    assert {
        "type": "story",
        "entity": {
            "name": "A Release",
            "story_type": "chore",
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_RELEASE_TYPE_LABEL},
            ],
        },
        "parsed_row": d,
    } == build_entity(ctx, d)


def test_build_epic():
    ctx = create_test_ctx()
    d = {
        "story_type": "epic",
        "name": "An Epic Name",
        "comments": [
            {"text": "Comment 1"},
            {"text": "Comment 2"},
            {"text": "Comment 3"},
        ],
    }

    assert {
        "type": "epic",
        "entity": {
            "name": "An Epic Name",
            "labels": [{"name": PIVOTAL_TO_SHORTCUT_LABEL}],
        },
        "parsed_row": d,
    } == build_entity(ctx, d)
