# Unused Labels to CSV

Run this script to produce a CSV of labels that aren't currently being used in your Shortcut workspace.

By default, a label is considered unused if it has neither stories nor epics associated with it.

If you add the `--include-completed` flag, this script will include all labels that have only stories and/or epics that are completed (in a "Done" workflow state).

## Usage

To download this script's dependencies, run:

```shell
make setup
```

After that, you can run the script to produce a CSV of labels that have neither stories nor epics associated with them:

```shell
pipenv run python unused_labels.py
```

Optionally include labels that have associated stories and/or epics, all of which are in a Done workflow state:

```shell
pipenv run python unused_labels.py --include-completed
```

Once you're satisfied that the CSV contains labels you want to archive, pass the `--archive` argument with the name of the CSV:

```shell
pipenv run python unused_labels.py --archive-labels labels-to-archive.csv
```

The CSV must have a header with at least an `id` column which is treated as the ID of labels to archive.

Pass `--help` for full usage information.

## Development

Set up your development environment:

```shell
make setup-dev
```

Run `pipenv shell` to enter a shell with all Python dependencies loaded.

Run the linter:

```shell
make lint
```
