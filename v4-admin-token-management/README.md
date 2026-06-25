# Admin Token Management (API v4)

This recipe demonstrates the two Shortcut API v4 **Admin** routes for managing a
Workspace's API tokens:

- **List Admin Tokens** — `GET /{workspace-slug}/admin/tokens`
- **Delete Admin Token** — `DELETE /{workspace-slug}/admin/tokens/{token-public-id}`

See the [Admin section of the API reference](https://developer.shortcut.com/api/rest/v4#Admin).

A Workspace admin can use these endpoints to audit every API token in the
Workspace (who owns it, what scopes it has, when it was last used) and to disable
tokens that should no longer be active.

## The `admin` scope is required

These endpoints require a token that has the **`admin`** scope. Older "legacy"
tokens and tokens created without the `admin` scope will receive an HTTP `403`
response. Only users with Admin privileges in a workspace can create tokens
with the **`admin`** scope.

When you create a new API token at
https://app.shortcut.com/settings/account/api-tokens, be sure to add the
**Admin** scope to it. You can confirm your token's scopes with the `whoami`
endpoint:

```shell
curl -s -H "Authorization: Bearer $SHORTCUT_API_TOKEN" \
  https://api.app.shortcut.com/api/v4/whoami | python -m json.tool
```

The `authorization.scopes` array should include `"admin"`.

## How pagination works

The List Admin Tokens endpoint is **cursor-paginated**. Each response includes:

- `entities` — the tokens on the current page,
- `total_items` / `total_pages` — totals across all pages,
- `next_page_url` — a fully-formed URL for the next page (absent on the last page).

When a `cursor` is present in a request (i.e. on every page after the first), the
API requires it to be the only query parameter, so filter and ordering options are
sent only on the initial request and then carried forward by the server through the
cursor embedded in `next_page_url`. This script follows `next_page_url` until all
matching tokens (or your requested `--limit`) have been retrieved.

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
export SHORTCUT_API_TOKEN="your-admin-scoped-api-token"
export SHORTCUT_WORKSPACE_SLUG="your-workspace-slug"
```

## Usage

### List tokens

List all tokens in the Workspace:

```shell
python admin_token_management.py list
```

Show only the first 25 tokens, including disabled ones, newest first:

```shell
python admin_token_management.py list --limit 25 \
  --filter include_disabled --order-by created_at --order-dir desc
```

Options:

| Option | Description |
| --- | --- |
| `-n`, `--limit` | Maximum number of tokens to display (default: all). |
| `--filter` | `exclude_disabled` (default) or `include_disabled`. |
| `--order-by` | `created_at`. |
| `--order-dir` | `asc` or `desc`. |

Example output:

```
TOKEN ID           DISABLED  SCOPES                        LAST USED             MEMBER
---------------------------------------------------------------------------------------
<token-id-1>       no        read,admin                    2026-06-25T00:00:00   Daniel Gregoire  — Admin Test
<token-id-2>       no        read,write,admin              never                 Lauren Arnett  — rwa token
```

### Delete (disable) a token

Use the token's public ID (the `TOKEN ID` / `id` UUID from the list output):

```shell
python admin_token_management.py delete --token-id 6a3d965f-0650-4fe6-89b5-c7ae788dd496
```

You'll be prompted to confirm before the token is disabled. To skip the prompt
(for example, when scripting), pass `--yes`:

```shell
python admin_token_management.py delete --token-id <token-public-id> --yes
```

A successful delete disables the token and the API responds with `204 No Content`.
