"""Manage a Shortcut Workspace's API Tokens using the v4 Admin endpoints.

This recipe demonstrates the two Admin token-management routes:

  - List Admin Tokens   GET    /{workspace-slug}/admin/tokens
  - Delete Admin Token  DELETE /{workspace-slug}/admin/tokens/{token-public-id}

Both routes require a token with the "admin" scope. Tokens without the admin
scope receive an HTTP 403 response.

See https://developer.shortcut.com/api/rest/v4#Admin
"""

import argparse
import logging
import sys

from lib import (
    print_rate_limiting_explanation,
    printerr,
    sc_delete,
    sc_get,
    sc_get_url,
    validate_environment,
)


def fetch_tokens(limit=None, filter_=None, order_by=None, order_dir=None):
    """
    Fetch Admin Tokens from the Workspace.

    The List Admin Tokens endpoint is cursor-paginated: each response includes
    an `entities` array and, when more results exist, a `next_page_url`. This
    function follows `next_page_url` until all tokens have been collected, or
    until `limit` tokens have been gathered.

    Note that when a `cursor` is present in the request (i.e. on every page
    after the first), the API requires it to be the only query parameter, so
    filter/order options are sent only on the initial request and are then
    carried forward by the server through the cursor in `next_page_url`.
    """
    params = {}
    # The API page size caps at 100; request the largest sensible page.
    params["limit"] = 100 if limit is None else min(limit, 100)
    if filter_:
        params["filter"] = filter_
    if order_by:
        params["order_by"] = order_by
    if order_dir:
        params["order_dir"] = order_dir

    data = sc_get("/admin/tokens", params)
    tokens = list(data.get("entities", []))
    total = data.get("total_items")
    logging.info(f"Workspace has {total} token(s) matching the requested filter.")

    while data.get("next_page_url") and (limit is None or len(tokens) < limit):
        data = sc_get_url(data["next_page_url"])
        tokens.extend(data.get("entities", []))

    if limit is not None:
        tokens = tokens[:limit]
    return tokens


def print_tokens(tokens):
    if not tokens:
        print("No tokens found.")
        return

    header = f"{'TOKEN ID':36}  {'DISABLED':8}  {'SCOPES':28}  {'LAST USED':20}  MEMBER"
    print(header)
    print("-" * len(header))
    for t in tokens:
        token_id = t.get("id", "")
        disabled = "yes" if t.get("disabled") else "no"
        scopes = ",".join(t.get("scopes") or []) or "(legacy)"
        last_used = (t.get("last_used_at") or "never")[:19]
        member = t.get("member") or {}
        member_name = member.get("name") or t.get("email_address") or "unknown"
        description = t.get("description") or ""
        line = f"{token_id:36}  {disabled:8}  {scopes:28}  {last_used:20}  {member_name}"
        if description:
            line += f"  — {description}"
        print(line)
    print(f"\n{len(tokens)} token(s) shown.")


def delete_token(token_id, assume_yes=False):
    """
    Delete (disable) a single Admin Token by its public UUID.

    The Delete Admin Token endpoint disables the token and responds with
    HTTP 204 No Content on success.
    """
    if not assume_yes:
        printerr(
            f"About to disable token {token_id}. This cannot be undone.\n"
            "Re-run with --yes to confirm, or type 'yes' to continue."
        )
        answer = input("Disable this token? [yes/N] ").strip().lower()
        if answer != "yes":
            print("Aborted; no token was disabled.")
            return False

    resp = sc_delete(f"/admin/tokens/{token_id}")
    # A successful delete returns 204 No Content.
    print(f"Token {token_id} disabled (HTTP {resp.status_code}).")
    return True


def build_parser():
    parser = argparse.ArgumentParser(
        description="List and delete a Shortcut Workspace's API tokens (Admin endpoints).",
    )
    parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", help="List the Workspace's API tokens."
    )
    list_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        help="Maximum number of tokens to display (default: all).",
    )
    list_parser.add_argument(
        "--filter",
        dest="filter_",
        choices=["exclude_disabled", "include_disabled"],
        default=None,
        help="Whether to include disabled tokens (default: exclude_disabled).",
    )
    list_parser.add_argument(
        "--order-by",
        dest="order_by",
        choices=["created_at"],
        default=None,
        help="Property to order results by.",
    )
    list_parser.add_argument(
        "--order-dir",
        dest="order_dir",
        choices=["asc", "desc"],
        default=None,
        help="Direction to order results.",
    )

    delete_parser = subparsers.add_parser(
        "delete", help="Disable a single API token by its public ID."
    )
    delete_parser.add_argument(
        "-t",
        "--token-id",
        dest="token_id",
        required=True,
        help="The public UUID of the token to disable.",
    )
    delete_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )

    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    if args.command == "list":
        tokens = fetch_tokens(
            limit=args.limit,
            filter_=args.filter_,
            order_by=args.order_by,
            order_dir=args.order_dir,
        )
        print_tokens(tokens)
        return 0

    if args.command == "delete":
        ok = delete_token(args.token_id, assume_yes=args.yes)
        return 0 if ok else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
