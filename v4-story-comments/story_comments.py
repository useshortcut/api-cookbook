import argparse
import logging
import sys

from lib import print_rate_limiting_explanation, sc_get, sc_get_url, validate_environment

parser = argparse.ArgumentParser(
    description="Print all comments on a Shortcut story",
)
parser.add_argument(
    "-s",
    "--story-id",
    dest="story_id",
    required=True,
    help="The ID of the story to fetch comments for",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


def fetch_all_comments(story):
    """
    Return all comments on a story.

    The story response includes inline comment summaries and a list_url pointing
    to the full paginated comments list. We always follow list_url to get full
    comment objects (including author name and timestamps).
    """
    comments_collection = story["entity"]["comments"]
    total = comments_collection["total_items"]

    if total == 0:
        return []

    logging.info(
        f"Story has {total} comment(s); fetching from {comments_collection['list_url']}"
    )
    all_comments = []
    data = sc_get_url(comments_collection["list_url"])
    all_comments.extend(data.get("entities", []))
    while data.get("next_page_url"):
        data = sc_get_url(data["next_page_url"])
        all_comments.extend(data.get("entities", []))
    return all_comments


def print_comments(story, comments):
    entity = story["entity"]
    print(f"Story {entity['id']}: {entity['name']}")
    print(f"{len(comments)} comment(s)\n")
    for comment in comments:
        author = comment.get("author", {}).get("name", "unknown")
        created = comment.get("created_at", "")[:10]
        text = comment.get("text", "")
        print(f"[{created}] {author}: {text}")


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    story = sc_get(f"/stories/{args.story_id}")
    comments = fetch_all_comments(story)
    print_comments(story, comments)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
