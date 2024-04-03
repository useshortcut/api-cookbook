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


def test_entity_collector():
    created = []

    def mock_emitter(items):
        created.extend([i["entity"] for i in items])
        return range(len(items))

    entity_collector = EntityCollector(mock_emitter)

    entity_collector.collect({"type": "story", "entity": {"name": "A Story 1"}})
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 2"}})
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 3"}})

    entity_collector.commit()

    assert [
        {"name": "A Story 1"},
        {"name": "A Story 2"},
        {"name": "A Story 3"},
    ] == created


def test_entity_collector_with_epics():
    created = []

    def mock_emitter(items):
        created.extend([i["entity"] for i in items])
        return range(len(items))

    entity_collector = EntityCollector(mock_emitter)

    # Given: a sequence of stories and epics
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 1"}})
    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 2", "labels": [{"name": "my-epic-label-2"}]},
        }
    )
    entity_collector.collect(
        {
            "type": "epic",
            "entity": {"name": "An Epic", "labels": [{"name": "my-epic-label"}]},
        }
    )
    entity_collector.collect(
        {
            "type": "epic",
            "entity": {"name": "Another Epic", "labels": [{"name": "my-epic-label-2"}]},
        }
    )
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 3"}})

    # When: the entities are commited/crread
    entity_collector.commit()

    # Then: All epics are created before the stories
    #     and the story with the same label as the epic is created with the appropriate epic id
    assert [
        # epic id =  0
        {"name": "An Epic", "labels": [{"name": "my-epic-label"}]},
        # epic id = 1
        {"name": "Another Epic", "labels": [{"name": "my-epic-label-2"}]},
        {"name": "A Story 1"},
        {"name": "A Story 2", "epic_id": 1, "labels": [{"name": "my-epic-label-2"}]},
        {"name": "A Story 3"},
    ] == created
