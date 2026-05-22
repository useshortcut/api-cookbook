# Field-Filtered Story Export (API v4)

This recipe exports all stories in a given workflow state to a CSV file.

It demonstrates two v4 features:

- **Field filtering** — the `fields` query parameter limits the response to
  only the fields you need, reducing payload size and improving performance.
- **Pagination** — v4 list endpoints are always paginated. This script
  automatically follows `next_page_url` to retrieve all results regardless of
  how many stories are in the workflow state.

To find your workflow state IDs, check **Settings → Workflow** in Shortcut, or
call `GET /api/v4/{workspace-slug}/workflows`.

## Requirements

- Python 3
- `requests` library
- `pyrate_limiter` library

The top-level Pipfile can be used to install these dependencies:

```shell
pipenv install
```

## Setup

Set your environment variables:

```shell
export SHORTCUT_API_TOKEN="your-api-token-here"
export SHORTCUT_WORKSPACE_SLUG="your-workspace-slug"
```

## Usage

By default the CSV includes `id`, `name`, `workflow_state`, and `owners`.

```shell
python field_filtered_search.py --workflow-state-id <state-id>
```

Request a custom set of fields:

```shell
python field_filtered_search.py --workflow-state-id <state-id> --fields id,name,workflow_state,owners,deadline
```

Available fields (see [Story documentation](https://developer.shortcut.com/api/rest/v4#Story)): `app_url`, `archived`, `blocked`, `blocker`, `branches`,
`checklist_items`, `comments`, `commits`, `completed`, `completed_at`,
`completed_at_override`, `created_at`, `custom_field_values`, `deadline`,
`description`, `entity_type`, `epic`, `estimate`, `external_id`,
`external_links`, `files`, `followers`, `id`, `iterations`, `labels`,
`linked_files`, `mentioned_members`, `mentioned_teams`, `moved_at`, `name`,
`owners`, `parent_story`, `position`, `project`, `pull_requests`, `requester`,
`started`, `started_at`, `started_at_override`, `story_links`, `story_template`,
`story_type`, `sub_task_stories`, `team`, `updated_at`, `uri`, `workflow`,
`workflow_state`

By default the CSV is written to `~/Downloads/workflow-state-<id>-stories_<timestamp>.csv`.
You can override the output path:

```shell
python field_filtered_search.py --workflow-state-id <state-id> --output-file my-stories.csv
```

