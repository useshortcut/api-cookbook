This script imports a Pivotal Tracker CSV export file into a Shortcut workspace.

[Walk-through Video](https://vimeo.com/931197039?share=copy) _(recorded 2024-04-05 using api-cookbook commit [1c12c1cc03](https://github.com/useshortcut/api-cookbook/tree/1c12c1cc035f4321f6b09a0e264eec740ddf2e88))_

This README contains detailed usage instructions, but if you just want to jump in, clone this repository and at its root run:

```
# Dry run:
make import

# Real run:
make import-apply
```

Follow the instructions printed to the console to configure and complete your import.

# Prerequisites and Setup

In order to run this, you will require a Pivotal account and the ability to sign up for a Shortcut account, as well as a working internet connection.

1. Sign up for a Shortcut account at [https://www.shortcut.com/signup](https://www.shortcut.com/signup).
   - **NOTE:** Do not run this importer against an existing Shortcut workspace that already has data you wish to keep.
1. [Create a new Shortcut API token](https://app.shortcut.com/settings/account/api-tokens) and [export it into your environment](../Authentication.md).
1. Export your Pivotal project to CSV.
   - Unarchive the ZIP file provided by Pivotal.
   - Copy the primary CSV file to `data/pivotal_export.csv`
   - (Optional) To import your Pivotal story file attachments, ensure you included them when requesting your Pivotal export, and then copy the directories in your Pivotal export that are named after your Pivotal story IDs (which contain their file attachments) into the `data/` folder of this project. This will result in a directory structure like `data/10000/*`, `data/10001/*`, etc.
1. Create/Invite all users you want to reference into your Shortcut workspace.
   - **NOTE:** If you're not on a Shortcut trial, please [reach out to our support team](https://help.shortcut.com/hc/en-us/requests/new) before running this import to make sure you're not billed for users that you want to be disabled after import.
   - **Also Note:** When you commit your import, there's the potential for many notification emails to be sent to the users in your workspace. [**Contact our support team**](https://help.shortcut.com/hc/en-us/requests/new) to temporarily disable email notifications if you would prefer to keep your inbox clear.
1. Run `make import` to perform a dry-run of the import.
   - Follow instructions printed to the console to ensure the mapping of Pivotal and Shortcut data is complete and correct.
   - You may edit the following files generated during initialization, to change how story priorities, story workflow states, and users are mapped between your Pivotal export and Shortcut workspace:
     - `data/priorities.csv`
     - `data/states.csv`
     - `data/users.csv`
   - This script will also write the following files during initialization to help you fill out the mapping files above:
     - `data/shortcut_groups.csv` is a listing of all your Shortcut Teams/Groups
     - `data/shortcut_users.csv` is a listing of all users in your Shortcut workspace
     - `data/shortcut_imported_entities.csv` contains a listing of all entities created during import
   - Ensure a `group_id` is set in your `config.json` file if you want to assign the epics and stories you import to a Shortcut Team/Group.
1. 🚀 Run `make import-apply` to actually import your data into Shortcut, if the dry run looked correct.
   - The console should print a link to an import-specific Shortcut label page that you can review to find all imported Stories and Epics.
   - If you run the importer multiple times, you can review all imported Stories and Epics by visiting Settings > Labels and then searching for the `pivotal->shortcut` label and clicking on it.
1. If you find that you need to adjust your configuration or your Pivotal data and try again, you can run `make delete` to review a dry-run and `make delete-apply` to actually delete the imported Shortcut epics and stories listed in `data/shortcut_imported_entities.csv`. You can also archive or delete content in the Shortcut application if needed.

You can run `make clean` if you want to start over, but be aware this will delete all but your `data/pivotal_export.csv` file.

# Known Limitations

**This is alpha software.** Not only is not guaranteed to be without bugs, but it is under active development and has several known feature gaps to be filled before we consider it complete.

The following are known limitations:

- **Story reviews:** Shortcut does not have a feature equivalent to Pivotal story reviews, so they are imported as follows:
  - Pivotal story reviewers are imported as Shortcut story followers on the stories they were assigned for review. Shortcut story followers receive updates in their Shortcut Activity Feed for all story updates.
  - Imported stories that had Pivotal reviews have an additional comment with a table that lists all of the story reviews from Pivotal (reviewer, review type, and review status).
  - Imported stories that had Pivotal reviews have a label in Shortcut of `pivotal-had-review`.
- **File attachments:** Files included in the Pivotal export (and correctly placed in the `data/` folder prior to import) are uploaded and associated with respective imported Shortcut stories. Other kinds of attachments (e.g., Google Drive) are not supported.
- **No story blockers:** Pivotal story blockers (the relationships between stories) are not imported.
- **Epics are imported as unstarted:** Imported epics are set to an unstarted "Todo" state.
- **No redirects:** The URLs in the descriptions and comments of your Pivotal stories/epics are not rewritten to point to imported Shortcut stories/epics; they remain unchanged.
- **No history:** Project history is not imported into Shortcut.

Our intention is to attend to items higher on the list sooner than those lower.

Please check [currently open issues](https://github.com/useshortcut/api-cookbook/issues) for further reported limitations.

# Customization

It's possible that this tool does not do exactly what you'd like it to - if that's the case, we have tried to make it straightforward to modify. Make reference to the [Shortcut API](https://developer.shortcut.com/api/rest/v3) and the other examples in this cookbook, and please let us know in [our Slack](https://shortcut.com/join-slack) what you're doing with it! We have a specific channel there, [#pivotal-migration](https://shortcutcommunity.slack.com/archives/C07QAKTQX43).

# Implementation

This project is written in Python (3.10) using `pipenv` for version and dependency management and `make` as the intended CLI for normal operation.

This project is not structured as a Python module, but instead as independent Python scripts.

First we'll cover the `make` targets, and then provide a deeper look at the Python scripts.

## make targets

The following `make` targets are supported (alphabetic order):

- `clean`
  - Deletes `config.json` and all files in the `data/` folder, except the user's Pivotal export at `data/pivotal_export.csv`
- `delete`
  - This is a dry-run version of the `delete-apply` target.
  - This target runs `pipenv run python delete_imported_entities.py`
- `delete-apply`
  - This target runs `pipenv run python delete_imported_entities.py --apply`
  - After an import completes, a `data/shortcut_imported_entities.csv` file is written.
  - This target uses that CSV to make `DELETE` calls to the Shortcut API, deleting all entities imported during that last run.
  - If you've done multiple imports and need to delete all entities, visit the Settings > Labels > `pivotal->shortcut` label page to see all epics and stories imported by this tool.
- `import`
  - This is a dry-run version of the `import-apply` target.
- `import-apply`
  - This target depends on the `initialize` target.
  - This target runs `pipenv run python pivotal_import.py --apply` to execute an import of the stories, epics, and iterations found in the user's Pivotal export `data/pivotal_export.csv` into the Shortcut workspace associated with the user's `SHORTCUT_API_TOKEN` environment variable.
  - See the section below on `pivotal_import.py` for more details.
- `initialize`
  - This target depends on the `setup` target.
  - This target runs `pipenv run python initialize.py` to initialize the user's import.
  - Initialization includes populating and verifying the `config.json` file for single config values, as well as the `data/priorities`, `data/states.csv`, and `data/users.csv` files that represent mappings from Pivotal to Shortcut.
  - See the section below on `initialize.py` for more details.
- `lint` (development)
  - This target runs linting/formatting using the Black formatter.
- `setup`
  - This target checks for the presence of the `pipenv` command on the user's `PATH`, and having found it runs `pipenv install` to download all primary Python dependencies.
- `setup-dev`
  - This target does what `setup` does, but also installs development-only Python dependencies.
- `test`
  - This target runs this project's Python tests using `pytest`

The `clean`, `lint`, `setup`, and `test` scripts are the backing for the `make` targets of the same name.

## Python: `initialize.py`

For `initialize.py` to complete successfully, the following must be true:

- A `config.json` file at the root of this repo—populated by `initialize.py` if not present—must encode a single JSON object with the following fields (note that in practice, users will only need to edit `workflow_id` and/or `priority_custom_field_id`):
  - `group_id` is a Shortcut ID representing the Team/Group the user wants all epics and stories to be assigned to during import.
    - Value may be `null`, but the field itself is required.
    - See `data/groups.csv` (populated by `initialize.py`) for Teams/Groups in your Shortcut workspace.
  - `priorities_csv_file` is the location of a file containing all the Priority custom field values from your Shortcut workspace.
    - Warning: Don't change this configuration value unless you're hacking on the project.
  - `priority_custom_field_id` is the Shortcut ID of the built-in Custom Field titled "Priority" in your Shortcut workspace.
    - To customize this value,
  - `priorities_csv_file` is the location of a file containing the user's desired mapping between PT priorities and Shortcut Priority custom field values. See `data/shortcut_custom_fields.csv` (populated by `initialize.py`) for a full listing of custom fields in the Shortcut workspace.
  - `pt_csv_file` is the location of your Pivotal CSV export.
    - By default, this value is `data/pivotal_export.csv`.
    - Warning: Don't change this configuration value unless you're hacking on the project.
  - `states_csv_file` is the location of a file containing the user's desired mapping between PT story state and Shortcut story workflow state. See `data/shortcut_workflows.csv` for a complete listing of all workflows and their constituent workflow states found in the Shortcut workspace.
    - Warning: Don't change this configuration value unless you're hacking on the project.
  - `users_csv_file` is the location of a file containing the user's desired mapping between PT users and Shortcut users. This is populated from the users found in the PT export. The user needs to invite missing users to Shortcut (or use a blanket user if they don't care about preserving that information) and fill in all blank email fields in this CSV for the importer to run successfully.
    - If the user fills out the `users_csv_file` before inviting people to their Shortcut workspace, the importer will print a listing of all emails found in that CSV file but not in the Shortcut workspace, at which point it is trivial to copy and paste that list of emails into Shortcut's UI for inviting users in bulk.
    - Warning: Don't change this configuration value unless you're hacking on the project.
  - `workflow_id` is the Shortcut ID of the story workflow that should be used to configure mappings between PT story states and Shortcut workflow states. The Shortcut _workflow_ contains many _workflow states_. The `states_csv_file` is that mapping between the actual states; this `workflow_id` is used to fetch candidate workflow states and automatically map workflow states where possible.

NOTE: In practice, you will only need to edit the `config.json` file if you need to edit the `workflow_id` or `priority_custom_field_id`.

The `config.json` file is loaded into memory when the `pivotal_import.py` is run, to ascertain the values and file locations specified above. If the `config.json` file is not valid, the `initialize.py` script will print the reasons why and provide instructions for correcting what is wrong.

With a valid `config.json` file, the importer will attempt to populate the `data/priorities.csv`, `data/states.csv`, and `data/users.csv` files automatically, printing to the console any issues it has with automatically identifying these mappings.

### Priority mapping in `data/priorities.csv`

At this time, the importer assumes you have Pivotal priorities enabled and requires that you map them to Shortcut Priority custom field values. You can straightforwardly comment all mentions of priority from the Python implementation of this importer to have it skip considering Priority mapping.

If your Shortcut workspace has the default Priority custom field enabled, `initialize.py` will identify its Shortcut ID, will populate the `priority_custom_field_id` value in your `config.json` with that ID, and will then populate `data/priorities.csv` with the IDs of the top 4 custom field values (which are "Highest", "High", "Medium", and "Low" by default). If this is satisfactory, no further customization is required on your part.

If you wish to use a different custom field for mapping your Pivotal priority values, you can populate the `priority_custom_field_id` value with that Custom Field ID and then run `make initialize` again to have it populate the default custom field values. If you want further control over how each Pivotal priority is mapped to each custom field value, you can replace the custom field value IDs in the `data/priorities.csv` file to your liking.

Once all Pivotal priorities have a Shortcut priority mapping, initialization can continue successfully.

### Story State mapping in `data/states.csv`

Pivotal has a fixed set of possible story state, but Shortcut supports multiple workflows, each of which has consituent story states.

The `workflow_id` in your `config.json` is the Shortcut ID for the workflow (the container of states).

The `data/states.csv` file maps the individual Pivotal story states to Shortcut story workflow states within the workflow specified by `workflow_id`.

If your Shortcut workspace has the default workflow and its default workflow states, `initialize.py` will identify those and create the `data/states.csv` file with a full mapping from your Pivotal states to Shortcut workflow states.

If your Shortcut workspace does not have the default workflow, or if that workflow has non-standard states (since both of these things are user-editable), then you will need to complete the mapping in `data/states.csv` by reviewing the workflows and workflow states written to `data/shortcut_workflows.csv`, so that every Pivotal story state has a corresponding Shortcut story workflow state.

Once all Pivotal story states have a Shortcut story workflow state mapping, initialization can continue successfully.

### User mapping in `data/users.csv`

Your Pivotal projects contain story requesters, story owners, story reviewers, and commenters, all of which require an identity in Shortcut for a successful import.

The `data/users.csv` file is populated by `initialize.py` with every unique user identified in your Pivotal export. The Pivotal export does not provide email addresses; it provides full names for the users in question.

The `initialize.py` script then checks whether there are users in your Shortcut workspace with full names that match the full names found in the Pivotal export. It automatically maps ones it can find, but leaves blank `shortcut_user_email` entries for any user that doesn't have an exact match.

You must provide an email address for every row in your `data/users.csv` file for initialization to proceed successfully.

If you're still on a Shortcut trial (or if you contact support), you can add users whom you intend to immediately disable, so that you can have a one-to-one mapping from your Pivotal users to your Shortcut users. If you don't care about preserving user history for people who won't be a part of your Shortcut workspace, you can also optionally map all of those users to a single email address for a blanket user that you add to your Shortcut workspace.

Note: The `shortcut_user_mention_name` column is there for your convenience, but is not required for initialization or import. You can leave that column empty for rows that you fill in manually.

## Python: `pivotal_import.py`

Once your `config.json` is in order and all of the rows in `data/priorities.csv`, `data/states.csv`, and `data/users.csv` are filled in, you can proceed with importing your Pivotal export into Shortcut.

The `pivotal_import.py` script defaults to doing a dry run of the import, wherein it: identifies the number of epics, iterations, and stories that would be imported; prints that information to the screen; and populates `data/shortcut_imported_entities.csv` with that mocked data.

Once you have reviewed what the importer has identified, you can run a real import by invoking the `make import-apply` make target. This will print less information to the screen, but it will provide a link to a Shortcut Label page that will automatically update with all of the epics and stories being imported. When complete, the importer will write `data/shortcut_imported_entities.csv` which provides a summary of all the Shortcut epics, iterations, and stories created during the import.

NOTE: Don't delete the `data/shortcut_imported_entities.csv` file; if you need to delete the import and try again, the `make delete` and `make delete-apply` targets depend on it.

## Python: `delete_imported_entities.py`

After performing an import, you may see something that you want to adjust in your configuration, mappings, or in the Python code of this importer itself.

To delete all of the epics, iterations, and stories you just imported, invoke `make delete` to see a dry run of what would be deleted, and then `make delete-apply` to actually delete the Shortcut entities. The underlying `delete_imported_entities.py` script relies on the `data/shortcut_imported_entities.csv` file to determine what to delete, so it shouldn't delete epics, iterations, and stories not found in that CSV file.

When you run `make import-apply` again, a new `data/shortcut_imported_entities.csv` file will be written, so you can cycle through imports and deletions until you're satisfied with the import.

# Contributing

Any contributions you make are greatly appreciated!

If you have a bug report or feature request, please [create a GitHub Issue](https://github.com/useshortcut/api-cookbook/issues/new).

If you need to share sensitive information or need help specific to your Shortcut workspace, please [submit a help center request](https://help.shortcut.com/hc/en-us/requests/new) instead.

You can also chat with us anytime on our [Shortcut Communuity Slack](https://shortcut.com/join-slack). We have a channel there specifically for you, [#pivotal-migration](https://shortcutcommunity.slack.com/archives/C07QAKTQX43). Please note that this is a community Slack and channel, so we urge you not to post information confidential to your company, including the CSV files you may be working with.

If you have code changes that would make this better, please fork this repository and create a pull request. Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
