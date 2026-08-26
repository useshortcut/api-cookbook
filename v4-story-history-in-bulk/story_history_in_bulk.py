import argparse
import csv
import io
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone

from lib import print_rate_limiting_explanation, sc_get, sc_get_url, validate_environment

parser = argparse.ArgumentParser(
    description="Report stories created in or moved to a team during a date range",
)
parser.add_argument(
    "-t",
    "--team",
    dest="team",
    required=True,
    help="The name (case-insensitive) or UUID of the team to report on",
)
parser.add_argument(
    "--start",
    dest="start",
    help="Start date as YYYY-MM-DD, inclusive (default: yesterday, UTC)",
)
parser.add_argument(
    "--end",
    dest="end",
    help="End date as YYYY-MM-DD, inclusive (default: today, UTC)",
)
parser.add_argument(
    "--format",
    dest="format",
    choices=["text", "json", "csv"],
    default="text",
    help="Output format (default: text)",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")

# The bulk history endpoint accepts up to 100 story IDs per request, and v4 list
# endpoints return at most 100 entities per page.
batch_size = 100
page_limit = 100

story_fields = "id,name,created_at,updated_at,team,app_url"
csv_keys = ["id", "name", "how", "created_at", "current_team", "app_url"]


def fetch_all(path, params, item_key):
    """Return all items from a paginated v4 list endpoint."""
    all_items = []
    data = sc_get(path, params)
    all_items.extend(data.get(item_key) or [])
    while data.get("next_page_url"):
        data = sc_get_url(data["next_page_url"])
        all_items.extend(data.get(item_key) or [])
    return all_items


def resolve_team(team_arg):
    """
    Return the (id, name) of the team matching a UUID or name.

    Team IDs in v4 are UUIDs, so this recipe also accepts a team name to keep
    the command line friendly.
    """
    teams = fetch_all("/teams", {"limit": page_limit}, "entities")
    for team in teams:
        if team_arg.lower() in (
            str(team.get("id", "")).lower(),
            str(team.get("name", "")).lower(),
        ):
            return str(team["id"]), team.get("name", team_arg)
    names = ", ".join(sorted(t.get("name", "?") for t in teams))
    sys.exit(f"Team {team_arg!r} not found. Teams in this workspace: {names}")


def parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def story_team_id(story):
    team = story.get("team")
    return str(team["id"]) if team else None


def fetch_updated_stories(start_date, end_date):
    """
    Return every story updated within the date range.

    A story created in the range is also updated in the range, so this single
    search covers both stories created in the team and stories moved into it.
    """
    query = f"updated:{start_date.isoformat()}..{end_date.isoformat()}"
    stories = fetch_all(
        "/stories/search",
        {"query": query, "limit": page_limit, "fields": story_fields},
        "entities",
    )
    logging.info(f"Found {len(stories)} stories updated between {start_date} and {end_date}")
    return stories


def created_in_team(stories, team_id, window_start, window_end):
    """Return IDs of stories created inside the window that are already on the team."""
    return {
        s["id"]
        for s in stories
        if window_start <= parse_ts(s["created_at"]) < window_end
        and story_team_id(s) == team_id
    }


def moved_to_team(story_ids, team_id, window_start, window_end):
    """
    Return IDs of stories whose history shows a move to the team in the window.

    Rather than requesting history one story at a time, this uses the bulk
    history endpoint, which accepts up to 100 story IDs per request. The
    `fields` parameter narrows the response to changes of the `team` attribute,
    so a story that was only re-estimated or re-pointed costs nothing to skip.
    """
    moved = set()
    batches = [
        story_ids[i : i + batch_size] for i in range(0, len(story_ids), batch_size)
    ]
    for i, batch in enumerate(batches, start=1):
        logging.info(f"Fetching history batch {i}/{len(batches)} ({len(batch)} stories)")
        changes = fetch_all(
            "/stories/history",
            {
                "ids": ",".join(str(sid) for sid in batch),
                "fields": "team",
                "limit": page_limit,
            },
            "changes",
        )
        for change in changes:
            if change.get("attribute") != "team":
                continue
            if not window_start <= parse_ts(change["timestamp"]) < window_end:
                continue
            if any(str(a.get("id")) == team_id for a in change.get("adds") or []):
                moved.add(change["entity"]["id"])
    return moved


def story_to_row(story, how):
    return {
        "id": story["id"],
        "name": story.get("name", ""),
        "how": how,
        "created_at": story.get("created_at", ""),
        "current_team": (story.get("team") or {}).get("name", ""),
        "app_url": story.get("app_url", ""),
    }


def print_rows(rows, team_name, start_date, end_date, output_format):
    if output_format == "json":
        print(json.dumps(rows, indent=2))
    elif output_format == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=csv_keys)
        writer.writeheader()
        writer.writerows(rows)
        print(out.getvalue(), end="")
    else:
        print(
            f"\n{len(rows)} stories entered team {team_name!r} "
            f"between {start_date} and {end_date}:"
        )
        for row in rows:
            print(f"  [{row['how']:7}] sc-{row['id']}: {row['name']}  {row['app_url']}")


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    today = datetime.now(timezone.utc).date()
    start_date = date.fromisoformat(args.start) if args.start else today - timedelta(days=1)
    end_date = date.fromisoformat(args.end) if args.end else today
    if end_date < start_date:
        sys.exit(f"--end {end_date} is before --start {start_date}")
    window_start = datetime.combine(start_date, datetime.min.time(), timezone.utc)
    window_end = datetime.combine(
        end_date + timedelta(days=1), datetime.min.time(), timezone.utc
    )

    team_id, team_name = resolve_team(args.team)
    logging.info(f"Team: {team_name} ({team_id})")
    logging.info(f"Window: {start_date} .. {end_date} (UTC)")

    stories = fetch_updated_stories(start_date, end_date)
    stories_by_id = {s["id"]: s for s in stories}

    created_ids = created_in_team(stories, team_id, window_start, window_end)
    candidate_ids = [sid for sid in stories_by_id if sid not in created_ids]
    moved_ids = moved_to_team(candidate_ids, team_id, window_start, window_end)

    rows = [
        story_to_row(stories_by_id[sid], "created" if sid in created_ids else "moved")
        for sid in sorted(created_ids | moved_ids)
    ]
    print_rows(rows, team_name, start_date, end_date, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
