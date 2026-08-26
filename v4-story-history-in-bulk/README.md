# Story History in Bulk (API v4)

This recipe reports every story that entered a team during a date range —
whether it was created in that team or moved into it later — and prints the
results as text, JSON, or CSV.

It demonstrates the v4 bulk history endpoint,
`GET /api/v4/{workspace-slug}/stories/history`, which accepts up to 100 story
IDs per request. Asking for one story's history at a time turns a report like
this into hundreds of API calls; asking in bulk turns it into a handful.

How the report is assembled:

1. **One search for the window.** `GET /stories/search` with
   `query=updated:START..END` returns every story touched in the range. A story
   created in the range was also updated in the range, so this single search
   covers both the "created in team" and "moved to team" cases.
2. **Created in the team.** Any story whose `created_at` falls inside the window
   and whose current team is the target team is reported as `created` — no
   history lookup needed.
3. **Moved to the team.** Everything else goes to the bulk history endpoint, 100
   IDs at a time, with `fields=team` to limit the response to changes of the
   `team` attribute. A change whose `adds` include the target team, timestamped
   inside the window, means the story was moved in.

Dates are interpreted in UTC, and both `--start` and `--end` are inclusive.

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

Report on yesterday and today (the default window):

```shell
python story_history_in_bulk.py --team "Engineering"
```

Teams in v4 are identified by UUID, but this script also accepts a
case-insensitive team name. If the name isn't found, it prints the names of all
teams in your workspace. To list teams yourself, call
`GET /api/v4/{workspace-slug}/teams`.

Report on an explicit date range:

```shell
python story_history_in_bulk.py --team "Engineering" --start 2026-08-01 --end 2026-08-25
```

Emit JSON or CSV instead of text:

```shell
python story_history_in_bulk.py --team "Engineering" --format csv > team-intake.csv
```

Each row includes the story's `id`, `name`, `how` it entered the team (`created`
or `moved`), `created_at`, `current_team`, and `app_url`.
