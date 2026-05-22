# Epic Stories Export (API v4)

This recipe exports all stories in a Shortcut epic to a CSV file.

The Shortcut API v4 returns nested collections — like the stories belonging to
an epic — inline on the parent entity, but limits the inline list to 10 items
for performance. If an epic has more than 10 stories, this script automatically
follows the pagination link to retrieve the complete set.

The CSV includes story ID, name, workflow state, owners, and due date.

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

```shell
python epic_with_stories.py --epic-id <epic-id>
```

By default the CSV is written to `~/Downloads/epic-<id>-stories_<timestamp>.csv`.
You can override the output path:

```shell
python epic_with_stories.py --epic-id <epic-id> --output-file my-stories.csv
```

