# Epic Comments as CSV

The [Shortcut exporter](https://github.com/useshortcut/exporter) includes Epics, but not their comments.
Epic comments support nesting, and their representation in the Shortcut REST API is also nested.

This recipe leverages the Shortcut REST API to generate a CSV of Epic comments for a given Shortcut Epic.
A `parent_id` column, when filled in, will contain the id of the comment that is the parent of the given comment.

## Usage

To download this script's dependencies, run:

``` shell
make setup
```

After that, you can run the script to pull down either one epic's comments:

``` shell
pipenv run python epic_comments.py --epic-id <epic-id>
```

Or epic comments for all epics in your Shortcut Workspace:

``` shell
pipenv run python epic_comments.py --all-epics
```

Each epic's comments will be written to a file with the epic ID and a current timestamp.
