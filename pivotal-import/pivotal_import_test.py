from pivotal_import import *


def create_test_ctx():
    return {
        "group_id": "group_123",
        "priority_config": {"p2 - medium": "priority_medium_123"},
        "priority_custom_field_id": "priority_123",
        "user_config": {
            "Amy Williams": "amy_member_id",
            "Daniel McFadden": "daniel_member_id",
            "Emmanuelle Charpentier": "emmanuelle_member_id",
            "Giorgio Parisi": "giorgio_member_id",
            "Piper | Barnes": "piper_member_id",
        },
        "workflow_config": {"unstarted": 500000, "started": 500001, "done": 500002},
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
            "group_id": "group_123",
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
        "iteration": None,
        "pt_iteration_id": None,
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
                    "group_id": "group_123",
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
                "iteration": None,
                "pt_iteration_id": None,
                "parsed_row": rows[0],
            },
            {
                "type": "story",
                "entity": {
                    "story_type": "bug",
                    "requested_by_id": "daniel_member_id",
                    "group_id": "group_123",
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
                "iteration": None,
                "pt_iteration_id": None,
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
                "group_id": "group_123",
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
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "group_id": "group_123",
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
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
                "group_id": "group_123",
                "workflow_state_id": ctx["workflow_config"]["unstarted"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "group_id": "group_123",
                "workflow_state_id": ctx["workflow_config"]["started"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
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
                "group_id": "group_123",
                "requested_by_id": ctx["user_config"]["Daniel McFadden"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[0],
        },
        {
            "type": "story",
            "entity": {
                "story_type": "bug",
                "group_id": "group_123",
                "owner_ids": [
                    ctx["user_config"]["Amy Williams"],
                    ctx["user_config"]["Daniel McFadden"],
                ],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[1],
        },
    ] == [build_entity(ctx, d) for d in rows]


def test_build_no_group():
    ctx = create_test_ctx()
    ctx["group_id"] = None  # field is allowed to be null/None
    rows = [
        {
            "story_type": "feature",
            "requester": "Daniel McFadden",
        },
        {
            "story_type": "epic",
            "name": "An Epic Name",
        },
    ]

    assert [
        {
            "type": "story",
            "entity": {
                "story_type": "feature",
                "group_id": None,
                "requested_by_id": ctx["user_config"]["Daniel McFadden"],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[0],
        },
        {
            "type": "epic",
            "entity": {
                "name": "An Epic Name",
                "group_ids": [],
                "labels": [
                    {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                    {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                ],
            },
            "iteration": None,
            "pt_iteration_id": None,
            "parsed_row": rows[1],
        },
    ] == [build_entity(ctx, d) for d in rows]


def test_build_release():
    ctx = create_test_ctx()
    d = {
        "story_type": "release",
        "name": "A Release",
        "deadline": "2014-10-15T00:00:00",
    }

    assert {
        "type": "story",
        "entity": {
            "name": "A Release",
            "story_type": "chore",
            "group_id": "group_123",
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
                {"name": PIVOTAL_RELEASE_TYPE_LABEL},
            ],
            "deadline": "2014-10-15T00:00:00",
        },
        "iteration": None,
        "pt_iteration_id": None,
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
            "group_ids": ["group_123"],
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL},
            ],
        },
        "iteration": None,
        "pt_iteration_id": None,
        "parsed_row": d,
    } == build_entity(ctx, d)


def test_assign_stories_to_epics():
    assert assign_stories_to_epics(
        [
            {
                "type": "story",
                "entity": {
                    "name": "A Story 1",
                    # This label is used to determine epic membership of the story; see the epic's labels
                    "labels": [{"name": "an epic name"}],
                },
            },
            # This story is not assigned to an epic, and so should not have an epic_id
            {"type": "story", "entity": {"name": "A Story 2"}},
        ],
        [
            {
                "type": "epic",
                # This label is used to determine epic membership of the story; see the story's labels
                "entity": {"id": 1234, "labels": [{"name": "an epic name"}]},
                "imported_entity": {"id": 1234},
            }
        ],
    ) == [
        {
            "type": "story",
            "entity": {
                "name": "A Story 1",
                "epic_id": 1234,
                "labels": [{"name": "an epic name"}],
            },
        },
        # Note the absence of the epic_id, fixing a bug where we unintentionally assigned
        # an epic to every story; bug introduced in commit
        # efbb2ddb691c7c91b0f2e3c817cfead663adc5db on 2024-04-08
        {"type": "story", "entity": {"name": "A Story 2"}},
    ]


def test_assign_stories_to_iterations():
    assert assign_stories_to_iterations(
        [
            {
                "type": "story",
                "entity": {
                    "name": "A Story 1",
                },
                "iteration": "123|2024-01-01|2025-01-01",
                "pt_iteration_id": "123",
            },
            # This story is not assigned to an iteration, and so should not have an iteration_id
            {
                "type": "story",
                "entity": {"name": "A Story 2"},
                "iteration": None,
                "pt_iteration_id": None,
            },
        ],
        [
            {
                "type": "iteration",
                "pt_iteration_id": "123",
                "entity": {
                    "name": "PT 123",
                    "start_date": "2024-01-01",
                    "end_date": "2025-01-01",
                },
                "imported_entity": {"id": 1234},
            }
        ],
    ) == [
        {
            "type": "story",
            "entity": {
                "name": "A Story 1",
                "iteration_id": 1234,
            },
            "iteration": "123|2024-01-01|2025-01-01",
            "pt_iteration_id": "123",
        },
        {
            "type": "story",
            "entity": {"name": "A Story 2"},
            "iteration": None,
            "pt_iteration_id": None,
        },
    ]


def test_entity_collector():
    entity_collector = EntityCollector()

    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 1", "external_id": "1234"},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 2", "external_id": "4567"},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 3", "external_id": "6789"},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )

    created = entity_collector.commit()

    assert [
        {
            "name": "A Story 1",
            "id": 0,
            "app_url": "https://example.com/entity/0",
            "entity_type": "story",
            "external_id": "1234",
        },
        {
            "name": "A Story 2",
            "id": 1,
            "app_url": "https://example.com/entity/1",
            "entity_type": "story",
            "external_id": "4567",
        },
        {
            "name": "A Story 3",
            "id": 2,
            "app_url": "https://example.com/entity/2",
            "entity_type": "story",
            "external_id": "6789",
        },
    ] == created


def test_entity_collector_with_epics():
    ctx = create_test_ctx()
    entity_collector = EntityCollector(emitter=None, ctx=ctx)

    # Given: a sequence of stories and epics
    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 1", "external_id": "1234"},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "story",
            "entity": {
                "name": "A Story 2",
                "labels": [{"name": "my-epic-label-2"}],
                "external_id": "2345",
            },
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "epic",
            "entity": {"name": "An Epic", "labels": [{"name": "my-epic-label"}]},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "epic",
            "entity": {"name": "Another Epic", "labels": [{"name": "my-epic-label-2"}]},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )
    entity_collector.collect(
        {
            "type": "story",
            "entity": {"name": "A Story 3", "external_id": "3456"},
            "iteration": None,
            "pt_iteration_id": None,
        }
    )

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
            "external_id": "1234",
        },
        {
            "name": "A Story 2",
            "epic_id": 1,
            "labels": [{"name": "my-epic-label-2"}],
            "id": 3,
            "app_url": "https://example.com/entity/3",
            "entity_type": "story",
            "external_id": "2345",
        },
        {
            "name": "A Story 3",
            "id": 4,
            "app_url": "https://example.com/entity/4",
            "entity_type": "story",
            "external_id": "3456",
        },
    ] == created


def test_calculate_epic_state():
    ctx = create_test_ctx()

    # Test empty stories list
    assert calculate_epic_state(ctx, []) == epic_states["todo"]

    # Test all stories done
    stories_done = [{
        "entity": {"workflow_state_id": ctx["workflow_config"]["done"]}
    }]
    assert calculate_epic_state(ctx, stories_done) == epic_states["done"]

    # Test mixed states
    stories_mixed = [
        {"entity": {"workflow_state_id": ctx["workflow_config"]["done"]}},
        {"entity": {"workflow_state_id": ctx["workflow_config"]["started"]}},
        {"entity": {"workflow_state_id": ctx["workflow_config"]["unstarted"]}}
    ]
    assert calculate_epic_state(ctx, stories_mixed) == epic_states["in_progress"]

    # Test all stories todo
    stories_todo = [{
        "entity": {"workflow_state_id": ctx["workflow_config"]["unstarted"]}
    }]
    assert calculate_epic_state(ctx, stories_todo) == epic_states["todo"]

    # Test all stories in progress
    stories_progress = [{
        "entity": {"workflow_state_id": ctx["workflow_config"]["started"]}
    }]
    assert calculate_epic_state(ctx, stories_progress) == epic_states["in_progress"]


def test_entity_collector_epic_state_updates():
    ctx = create_test_ctx()
    entity_collector = EntityCollector(emitter=get_mock_emitter(), ctx=ctx)

    # Create an epic with initial state
    epic = {
        "type": "epic",
        "entity": {
            "name": "Test Epic",
            "workflow_state_id": epic_states["todo"],  # Set initial state
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}
            ]
        }
    }
    entity_collector.collect(epic)

    # Create stories in different states
    story1 = {
        "type": "story",
        "entity": {
            "name": "Story 1",
            "workflow_state_id": ctx["workflow_config"]["done"],
            "epic_id": 0,  # Will be assigned by mock emitter
            "external_id": "PT1",  # Add external_id for Pivotal tracking
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}
            ],
            "story_type": "feature"  # Add story_type as required by build_entity
        },
        "iteration": None,
        "pt_iteration_id": None
    }
    story2 = {
        "type": "story",
        "entity": {
            "name": "Story 2",
            "workflow_state_id": ctx["workflow_config"]["started"],
            "epic_id": 0,
            "external_id": "PT2",  # Add external_id for Pivotal tracking
            "labels": [
                {"name": PIVOTAL_TO_SHORTCUT_LABEL},
                {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}
            ],
            "story_type": "feature"  # Add story_type as required by build_entity
        },
        "iteration": None,
        "pt_iteration_id": None
    }

    entity_collector.collect(story1)
    entity_collector.collect(story2)

    # Commit and verify epic state updates
    created_entities = entity_collector.commit()

    # Find the epic in created entities
    epic_updates = [e for e in created_entities if e["entity_type"] == "epic"]
    assert len(epic_updates) > 0
    assert epic_updates[0]["workflow_state_id"] == epic_states["in_progress"]
