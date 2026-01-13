#!/usr/bin/env python3
"""Generate a report of story rollover from iteration to iteration.

This script analyzes stories in an iteration and reports how many previous
iterations each story has been in, grouped by team (group_id).

Usage:
    # Analyze the latest started iteration
    python iteration_rollover.py

    # Analyze a specific iteration by ID
    python iteration_rollover.py --iteration-id 12345

    # Output to CSV
    python iteration_rollover.py --output-file rollover-report.csv
"""

import argparse
import csv
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone

from lib import print_rate_limiting_explanation, sc_get, validate_environment

parser = argparse.ArgumentParser(
    description="Generate a report of story rollover from iteration to iteration",
)
parser.add_argument(
    "--iteration-id",
    dest="iteration_id",
    type=int,
    help="Specific iteration ID to analyze. If not provided, uses the latest started iteration.",
)
parser.add_argument(
    "--output-file",
    dest="output_file",
    help="Name of file to write CSV results to. If not provided, outputs to stdout.",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


def parse_date(date_str):
    """Parse an ISO date string, handling various formats."""
    # Handle Z suffix
    date_str = date_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        # Fallback: parse just the date portion
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    # Make timezone-aware if naive
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def get_latest_started_iteration():
    """Find the most recently started iteration that is currently in progress."""
    logging.info("Fetching all iterations...")
    iterations = sc_get("/iterations")

    now = datetime.now(timezone.utc)

    # Filter to iterations that have started (start_date <= now)
    started_iterations = []
    for it in iterations:
        start_date = parse_date(it["start_date"])
        if start_date <= now:
            started_iterations.append(it)

    if not started_iterations:
        logging.error("No started iterations found in your workspace.")
        sys.exit(1)

    # Sort by start_date descending to get the most recently started
    started_iterations.sort(
        key=lambda x: parse_date(x["start_date"]),
        reverse=True,
    )

    return started_iterations[0]


def get_iteration_by_id(iteration_id):
    """Fetch a specific iteration by ID."""
    logging.info(f"Fetching iteration {iteration_id}...")
    return sc_get(f"/iterations/{iteration_id}")


def get_iteration_stories(iteration_id):
    """Fetch all stories in an iteration."""
    logging.info(f"Fetching stories for iteration {iteration_id}...")
    return sc_get(f"/iterations/{iteration_id}/stories")


def get_groups():
    """Fetch all groups (teams) in the workspace and return as a dict keyed by ID."""
    logging.info("Fetching groups (teams)...")
    groups = sc_get("/groups")
    return {g["id"]: g for g in groups}


def analyze_rollover(stories, groups):
    """
    Analyze stories for rollover information.

    Returns a dict keyed by group_id containing:
    - group_name: Name of the team
    - stories: List of story info dicts with rollover counts
    - total_stories: Count of stories in this group
    - rollover_stories: Count of stories that rolled over from previous iterations
    - total_previous_iterations: Sum of all previous iterations across stories
    """
    results = defaultdict(
        lambda: {
            "group_name": None,
            "stories": [],
            "total_stories": 0,
            "rollover_stories": 0,
            "total_previous_iterations": 0,
        }
    )

    for story in stories:
        group_id = story.get("group_id")
        previous_iteration_ids = story.get("previous_iteration_ids", [])
        rollover_count = len(previous_iteration_ids)

        # Handle stories without a team assignment
        if group_id is None:
            group_key = "unassigned"
            group_name = "(No Team Assigned)"
        else:
            group_key = group_id
            group_name = groups.get(group_id, {}).get(
                "name", f"Unknown Team ({group_id})"
            )

        results[group_key]["group_name"] = group_name
        results[group_key]["total_stories"] += 1
        results[group_key]["total_previous_iterations"] += rollover_count

        if rollover_count > 0:
            results[group_key]["rollover_stories"] += 1

        results[group_key]["stories"].append(
            {
                "story_id": story["id"],
                "story_name": story["name"],
                "story_type": story.get("story_type", "unknown"),
                "previous_iteration_count": rollover_count,
                "previous_iteration_ids": previous_iteration_ids,
                "app_url": story.get("app_url", ""),
            }
        )

    return dict(results)


def print_report(iteration, results):
    """Print the rollover report to stdout."""
    print(f"\n{'=' * 60}")
    print("Iteration Rollover Report")
    print(f"{'=' * 60}")
    print(f"Iteration: {iteration['name']}")
    print(f"ID: {iteration['id']}")
    print(f"Start Date: {iteration['start_date'][:10]}")
    print(f"End Date: {iteration['end_date'][:10]}")
    print(f"{'=' * 60}\n")

    if not results:
        print("No stories found in this iteration.")
        return

    # Summary by team
    print("SUMMARY BY TEAM")
    print("-" * 60)
    print(f"{'Team':<30} {'Total':<8} {'Rolled':<8} {'% Rolled':<10} {'Avg Prev':<10}")
    print("-" * 60)

    total_all = 0
    rollover_all = 0

    for group_key in sorted(results.keys(), key=lambda k: results[k]["group_name"]):
        data = results[group_key]
        total = data["total_stories"]
        rolled = data["rollover_stories"]
        pct = (rolled / total * 100) if total > 0 else 0
        avg_prev = (data["total_previous_iterations"] / total) if total > 0 else 0

        total_all += total
        rollover_all += rolled

        name = data["group_name"][:28]
        print(f"{name:<30} {total:<8} {rolled:<8} {pct:<10.1f} {avg_prev:<10.2f}")

    print("-" * 60)
    pct_all = (rollover_all / total_all * 100) if total_all > 0 else 0
    print(f"{'TOTAL':<30} {total_all:<8} {rollover_all:<8} {pct_all:<10.1f}")
    print()

    # Detailed breakdown by team
    print("\nDETAILED BREAKDOWN BY TEAM")
    print("=" * 60)

    for group_key in sorted(results.keys(), key=lambda k: results[k]["group_name"]):
        data = results[group_key]
        print(f"\n{data['group_name']}")
        print("-" * 40)

        # Sort stories by rollover count descending
        sorted_stories = sorted(
            data["stories"], key=lambda s: s["previous_iteration_count"], reverse=True
        )

        for story in sorted_stories:
            prev_count = story["previous_iteration_count"]
            indicator = f"[{prev_count} prev]" if prev_count > 0 else "[new]"
            print(f"  {indicator:<10} {story['story_name'][:45]}")


def write_csv_report(output_file, iteration, results):
    """Write the rollover report to a CSV file."""
    logging.info(f"Writing report to {output_file}...")

    fieldnames = [
        "iteration_id",
        "iteration_name",
        "group_id",
        "group_name",
        "story_id",
        "story_name",
        "story_type",
        "previous_iteration_count",
        "previous_iteration_ids",
        "app_url",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for group_key, data in results.items():
            for story in data["stories"]:
                writer.writerow(
                    {
                        "iteration_id": iteration["id"],
                        "iteration_name": iteration["name"],
                        "group_id": group_key if group_key != "unassigned" else "",
                        "group_name": data["group_name"],
                        "story_id": story["story_id"],
                        "story_name": story["story_name"],
                        "story_type": story["story_type"],
                        "previous_iteration_count": story["previous_iteration_count"],
                        "previous_iteration_ids": ",".join(
                            str(i) for i in story["previous_iteration_ids"]
                        ),
                        "app_url": story["app_url"],
                    }
                )

    print(f"Report written to {output_file}")


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    # Get the iteration to analyze
    if args.iteration_id:
        iteration = get_iteration_by_id(args.iteration_id)
    else:
        iteration = get_latest_started_iteration()
        logging.info(
            f"Using latest started iteration: {iteration['name']} (ID: {iteration['id']})"
        )

    # Fetch stories and groups
    stories = get_iteration_stories(iteration["id"])
    groups = get_groups()

    if not stories:
        print(f"No stories found in iteration '{iteration['name']}'")
        return 0

    # Analyze rollover
    results = analyze_rollover(stories, groups)

    # Output results
    if args.output_file:
        write_csv_report(args.output_file, iteration, results)
    else:
        print_report(iteration, results)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
