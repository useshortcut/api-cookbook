# Story Comments (API v4)

This recipe fetches all comments on a Shortcut story and prints them to stdout.

The Shortcut API v4 returns nested collections — like comments — inline on the
parent entity, but limits the inline list to 10 items for performance. If a
story has more than 10 comments, this script automatically follows the
pagination link to retrieve the complete set.

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
python story_comments.py --story-id <story-id>
```

