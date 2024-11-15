# Rewrite Text

Need to rewrite text in your entity descriptions in your Shortcut workspace (like links to external systems)?
This recipe helps you accomplish that.

## Usage

You'll need two CSVs: one to specify text substitutions, and one to indicate which entities to rewrite.

### CSV 1: Text Substitutions

Put together a CSV file names `rewrites.csv` with two columns:

- `from`
- `to`

With this information, the script will comb all non-archived entities within your Shortcut Workspace and rewrite every instance of `from` with `to`.
Note that it will only match `from` surrounded by non-word characters (a la regular expression `\bexample\b`).
This is to avoid accidental matches.

### CSV 2: Entities to Rewrite

Next put together a CSV `entities.csv` with the entities you want rewritten.
This should include the following columns (which match what you get from a Shortcut Workspace CSV export), only one of which should have a value per row:

- `id` (if a story)
- `epic_id`
- `iteration_id`
- `milestone_id` or `objective_id`

If you've already labeled stories and epics that you want to rewrite, you can pass that label id to the `entities_with_labels.py` script and it will produce an output CSV `entities_with_labels.csv` that follows the above pattern:

```shell
pipenv run python entities_with_labels.py <label-id>
```

### Running the Code

To download this script's dependencies, run:

```shell
make setup
```

Then you can run the rewrite:

```shell
pipenv run python rewrite_text.py --rewrites rewrites.csv --entities entities.csv
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
