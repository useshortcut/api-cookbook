from pivotal_import import *


def create_test_ctx():
    return {
        "priority_config": {"p2 - medium": "priority_medium_123"},
        "priority_custom_field_id": "priority_123",
        "user_config": {
            "Amy Williams": "amy_member_id",
            "Daniel McFadden": "daniel_member_id",
            "Emmanuelle Charpentier": "emmanuelle_member_id",
            "Giorgio Parisi": "giorgio_member_id",
            "Piper | Barnes": "piper_member_id",
        },
        "workflow_config": {"unstarted": 400001, "started": 400002, "done": 400003},
    }


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


def test_parse_labels():
    assert {
        "labels": [
            {"name": "a label"},
            {"name": "oneword"},
            {"name": "two words"},
            {"name": "three word salad"},
        ]
    } == parse_row(
        # purposefully using different variations of comma separated
        # labels
        ["a label , oneword, two words,three word salad"],
        ["labels"],
    )


def test_parse_owners():
    assert {
        "owners": [
            "Amy Williams",
            "Daniel McFadden",
        ]
    } == parse_row(
        ["Amy Williams", "Daniel McFadden"],
        ["owned by", "owned by"],
    )


def test_parse_reviewers():
    assert {
        "reviewers": [
            "Amy Williams",
            "Giorgio Parisi",
            "Emmanuelle Charpentier",
            "Piper | Barnes",
        ]
    } == parse_row(
        [
            "Amy Williams",
            "Giorgio Parisi",
            "Emmanuelle Charpentier",
            "Piper | Barnes",
        ],
        ["reviewer", "reviewer", "reviewer", "reviewer"],
    )


def test_parse_priority():
    assert "p3 - low" == parse_priority("p3 - Low")
    assert parse_priority("none") is None


def test_build_story_with_comments():
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
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
            ],
        },
        "parsed_row": d,
    } == build_entity(ctx, d)


def test_build_story_with_reviews():
    ctx = create_test_ctx()
    rows = [
        # just reviews, no Pivotal comments
        {
            "story_type": "feature",
            "reviewers": ["Emmanuelle Charpentier", "Giorgio Parisi"],
            "review_types": ["code", "security"],
            "review_states": ["unstarted", "in_review"],
        },
        # both Pivotal comments and reviews, which we add as Shortcut comments
        {
            "story_type": "bug",
            "requester": "Daniel McFadden",
            "reviewers": ["Emmanuelle Charpentier", "Giorgio Parisi", "Piper | Barnes"],
            "review_types": ["code", "security", "custom qa"],
            "review_states": ["unstarted", "in_review", "passed"],
            "comments": [
                {"text": "Comment 1"},
                {"text": "Comment 2"},
                {"text": "Comment 3"},
            ],
        },
    ]

    assert (
        [
            {
                "type": "story",
                "entity": {
                    "story_type": "feature",
                    "comments": [
                        {
                            "author_id": None,
                            "text": review_as_comment_text_prefix
                            + """
|Emmanuelle Charpentier|code|unstarted|
|Giorgio Parisi|security|in_review|""",
                        },
                    ],
                    "follower_ids": [
                        "emmanuelle_member_id",
                        "giorgio_member_id",
                    ],
                    "labels": [
                        {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                        {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                        {"name": PIVOTAL_HAD_REVIEW_LABEL},
                    ],
                },
                "parsed_row": rows[0],
            },
            {
                "type": "story",
                "entity": {
                    "story_type": "bug",
                    "requested_by_id": "daniel_member_id",
                    "comments": [
                        {"text": "Comment 1"},
                        {"text": "Comment 2"},
                        {"text": "Comment 3"},
                        {
                            "author_id": "daniel_member_id",
                            "text": review_as_comment_text_prefix
                            + """
|Emmanuelle Charpentier|code|unstarted|
|Giorgio Parisi|security|in_review|
|Piper \\| Barnes|custom qa|passed|""",
                        },
                    ],
                    "follower_ids": [
                        "emmanuelle_member_id",
                        "giorgio_member_id",
                        "piper_member_id",
                    ],
                    "labels": [
                        {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                        {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                        {"name": PIVOTAL_HAD_REVIEW_LABEL},
                    ],
                },
                "parsed_row": rows[1],
            },
        ]
        == [build_entity(ctx, d) for d in rows]
    )


def test_build_story_priority_mapping():
    ctx = create_test_ctx()
    rows = [
        {
            "story_type": "feature",
            "priority": "p2 - medium",
        },
        {
            "story_type": "bug",
            "priority": None,
        },
    ]

    assert [
        {
            "type": "story",
            "entity": {
                "story_type": "feature",
                "custom_fields": [
                    {
                        "field_id": "priority_123",
                        "value_id": "priority_medium_123",
                    }
                ],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[1],
        },
    ] == [build_entity(ctx, d) for d in rows]


def test_build_story_workflow_mapping():
    ctx = create_test_ctx()
    rows = [
        {
            "story_type": "feature",
            "pt_state": "unstarted",
        },
        {
            "story_type": "bug",
            "pt_state": "started",
        },
    ]

    assert [
        {
            "type": "story",
            "entity": {
                "story_type": "feature",
                "workflow_state_id": ctx["workflow_config"]["unstarted"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "workflow_state_id": ctx["workflow_config"]["started"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[1],
        },
    ] == [build_entity(ctx, d) for d in rows]


def test_build_story_user_mapping():
    ctx = create_test_ctx()
    rows = [
        {
            "story_type": "feature",
            "requester": "Daniel McFadden",
        },
        {
            "story_type": "bug",
            "owners": ["Amy Williams", "Daniel McFadden"],
        },
    ]

    assert [
        {
            "type": "story",
            "entity": {
                "story_type": "feature",
                "requested_by_id": ctx["user_config"]["Daniel McFadden"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "owner_ids": [
                    ctx["user_config"]["Amy Williams"],
                    ctx["user_config"]["Daniel McFadden"],
                ],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "parsed_row": rows[1],
        },
    ] == [build_entity(ctx, d) for d in rows]


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
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
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
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
            ],
        },
        "parsed_row": d,
    } == build_entity(ctx, d)


def test_entity_collector():
    entity_collector = EntityCollector()

    entity_collector.collect({"type": "story", "entity": {"name": "A Story 1"}})
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 2"}})
    entity_collector.collect({"type": "story", "entity": {"name": "A Story 3"}})

    created = entity_collector.commit()

    assert [
        {
            "name": "A Story 1",
            "id": 0,
            "app_url": "https://example.com/entity/0",
            "entity_type": "story",
        },
        {
            "name": "A Story 2",
            "id": 1,
            "app_url": "https://example.com/entity/1",
            "entity_type": "story",
        },
        {
            "name": "A Story 3",
            "id": 2,
            "app_url": "https://example.com/entity/2",
            "entity_type": "story",
        },
    ] == created


def test_entity_collector_with_epics():
    entity_collector = EntityCollector()

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
    created = entity_collector.commit()

    # Then: All epics are created before the stories
    #     and the story with the same label as the epic is created with the appropriate epic id
    assert [
        # epic id =  0
        {
            "name": "An Epic",
            "labels": [{"name": "my-epic-label"}],
            "id": 0,
            "app_url": "https://example.com/entity/0",
            "entity_type": "epic",
        },
        # epic id = 1
        {
            "name": "Another Epic",
            "labels": [{"name": "my-epic-label-2"}],
            "id": 1,
            "app_url": "https://example.com/entity/1",
            "entity_type": "epic",
        },
        {
            "name": "A Story 1",
            "id": 2,
            "app_url": "https://example.com/entity/2",
            "entity_type": "story",
        },
        {
            "name": "A Story 2",
            "epic_id": 1,
            "labels": [{"name": "my-epic-label-2"}],
            "id": 3,
            "app_url": "https://example.com/entity/3",
            "entity_type": "story",
        },
        {
            "name": "A Story 3",
            "id": 4,
            "app_url": "https://example.com/entity/4",
            "entity_type": "story",
        },
    ] == created
