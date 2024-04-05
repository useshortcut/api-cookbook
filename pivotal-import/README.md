This script imports a Pivotal Tracker CSV export file into a Shortcut workspace.

[Walk-through Video](https://us06web.zoom.us/clips/share/b-GrMOkI75f5MPehYt_uK1RS7SdNy-ADfJqsew5gCQ5w05sNfAFhS56SgE4xIq2RIM-K68_9QNyJNVIwBb2sDkl3.ouSPQZoDx0WOD8ic) _(recorded 2024-04-05 using api-cookbook commit [1c12c1cc03](https://github.com/useshortcut/api-cookbook/tree/1c12c1cc035f4321f6b09a0e264eec740ddf2e88))_

# Prerequisites and Setup

In order to run this, you will require a Pivotal account and the ability to sign up for a Shortcut account, as well as a working internet connection.

1. Sign up for a Shortcut account at [https://www.shortcut.com/signup](https://www.shortcut.com/signup).
   - **NOTE:** Do not run this importer against an existing Shortcut workspace that already has data you wish to keep.
1. [Create an API token](https://app.shortcut.com/settings/account/api-tokens) and [export it into your environment](../Authentication.md).
1. Export your Pivotal project to CSV and save the file to `data/pivotal_export.csv`.
1. Create/Invite all users you want to reference into your Shortcut workspace.
   - **NOTE:** If you're not on a Shortcut trial, please [reach out to our support team](https://help.shortcut.com/hc/en-us/requests/new) before running this import to make sure you're not billed for users that you want to be disabled after import.
1. Run `make import` to perform a dry-run of the import.
   - Follow instructions printed to the console to ensure the mapping of Pivotal and Shortcut data is complete and correct.
   - Refer to `data/states.csv` and `data/users.csv` to review these mappings.
1. If the dry-run output looks correct, you can apply the import to your Shortcut workspace by running `make import-apply`
1. Refer to `data/shortcut_imported_entities.csv` to review all epics, stories, etc. imported successfully into Shortcut.
   1. If you find that you need to adjust your configuration or your Pivotal data and try again, you can run `make delete` to review a dry-run and `make delete-apply` to actually delete the imported Shortcut epics and stories listed in that CSV file.

# Operation

Before you run the import, you should go through the steps in **Prerequisites and Setup**. You can check that the prerequisites are superficially met by running [`pivotal_import.py`](pivotal_import.py) which by default will not write any changes to your Shortcut workspace. You can use this mode to validate that you've configured the import correctly.

If `pivotal_import.py` completes without errors, you can run the script with the `--apply` flag, which will enable writing to the Shortcut API.

# Known Limitations

**This is alpha software.** Not only is not guaranteed to be without bugs, but it is under active development and has several known feature gaps to be filled before we consider it complete.

The following are known limitations:

- **No story reviewers:** Pivotal story reviewers are not imported.
- **No story priority:** Pivotal story priorities are not imported.
- **No story blockers:** Pivotal story blockers (the relationships between stories) are not imported.
- **No iterations:** Pivotal iterations are not imported.
- **Epics are imported as unstarted:** Imported epics are set to an unstarted "Todo" state.
- **No redirects:** The URLs in the descriptions and comments of your Pivotal stories/epics are not rewritten to point to imported Shortcut stories/epics; they remain unchanged.
- **No attachments:** The attachments (including Google Drive attachments) are not imported into Shortcut.
- **No history:** Project history is not imported into Shortcut.

Our intention is to attend to items higher on the list sooner than those lower.

Please check [currently open issues](https://github.com/useshortcut/api-cookbook/issues) for further reported limitations.

# Customization

It's possible that this tool does not do exactly what you'd like it to - if that's the case, we have tried to make it straightforward to modify. Make reference to the [Shortcut API](https://developer.shortcut.com/api/rest/v3) and the other examples in this cookbook, and please let us know in [our Discord](https://discord.gg/shortcut-community-887801174496006216) what you're doing with it!

# Contributing

Any contributions you make are greatly appreciated!

If you have a bug report or feature request, please [create a GitHub Issue](https://github.com/useshortcut/api-cookbook/issues/new).

If you need to share sensitive information or need help specific to your Shortcut workspace, please [submit a help center request](https://help.shortcut.com/hc/en-us/requests/new) instead.

You can also chat with us anytime on our [Shortcut Communuity Discord](https://discord.gg/shortcut-community-887801174496006216).

If you have code changes that would make this better, please fork this repository and create a pull request. Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
