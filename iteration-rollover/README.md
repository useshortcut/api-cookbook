# Iteration Rollover Report

This script generates a report showing how many times stories in an iteration have "rolled over" from previous iterations. This is useful for identifying work that has been carried over multiple sprints and may need attention.

## What it does

1. Fetches all stories in an iteration
2. Analyzes the `previous_iteration_ids` field on each story to determine how many times it has rolled over
3. Groups the results by team (group_id)
4. Outputs a summary showing:
   - Total stories per team
   - Number of stories that rolled over
   - Percentage of rollover stories
   - Average number of previous iterations per story

## Requirements

- Python 3
- `requests` library
- `pyrate_limiter` library

The top-level Pipfile can be used to install these dependencies.

## Setup

Set your Shortcut API token as an environment variable:

```bash
export SHORTCUT_API_TOKEN="your-api-token-here"
```

## Usage

### Analyze the latest started iteration

```bash
python iteration_rollover.py
```

This will find the most recently started iteration in your workspace and generate a rollover report.

### Analyze a specific iteration

```bash
python iteration_rollover.py --iteration-id 12345
```

### Output to CSV

```bash
python iteration_rollover.py --output-file rollover-report.csv
```

### Enable debug logging

```bash
python iteration_rollover.py --debug
```

## Example Output

```
============================================================
Iteration Rollover Report
============================================================
Iteration: Sprint 42
ID: 12345
Start Date: 2024-01-15
End Date: 2024-01-29
============================================================

SUMMARY BY TEAM
------------------------------------------------------------
Team                           Total    Rolled   % Rolled   Avg Prev
------------------------------------------------------------
Backend Team                   15       5        33.3       0.67
Frontend Team                  12       3        25.0       0.42
Platform Team                  8        2        25.0       0.38
(No Team Assigned)             3        1        33.3       0.33
------------------------------------------------------------
TOTAL                          38       11       28.9

DETAILED BREAKDOWN BY TEAM
============================================================

Backend Team
----------------------------------------
  [3 prev]   Implement user authentication refactor
  [2 prev]   Fix database connection pooling
  [new]      Add API rate limiting
  [new]      Update logging format
  ...
```

## CSV Output Format

When using `--output-file`, the CSV contains the following columns:

| Column                   | Description                                     |
| ------------------------ | ----------------------------------------------- |
| iteration_id             | ID of the analyzed iteration                    |
| iteration_name           | Name of the analyzed iteration                  |
| group_id                 | Team ID (empty for unassigned stories)          |
| group_name               | Team name                                       |
| story_id                 | Story ID                                        |
| story_name               | Story name                                      |
| story_type               | Type of story (feature, bug, chore)             |
| previous_iteration_count | Number of previous iterations this story was in |
| previous_iteration_ids   | Comma-separated list of previous iteration IDs  |
| app_url                  | Link to the story in Shortcut                   |

## Notes

- Stories without a team assignment are grouped under "(No Team Assigned)"
- The script adheres to Shortcut's API rate limiting (200 requests/minute)
- If an iteration has no stories, the script will indicate this and exit cleanly
